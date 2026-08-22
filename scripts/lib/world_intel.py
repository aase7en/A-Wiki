"""world_intel.py — Phase 10: lazy bridge to an EXTERNAL world-intel MCP.

Contract (config/integrations.yaml `world-intel`): default-off, lazy,
runtime external, NO vendoring, local regenerable cache (commit: false).
The bridge never names vendors or endpoints — a bound server is supplied
at runtime via WORLD_INTEL_MCP_CMD (machine-local, gitignored policy),
spoken to over stdio JSON-RPC. Unbound or broken server degrades to a
structured "not enabled"/error answer — never a crash, never blocking.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

_CMD_ENV = "WORLD_INTEL_MCP_CMD"
_TIMEOUT_S = 20
_CACHE_TTL_S = 6 * 3600  # regenerable cache; short-lived by design


class WorldIntel:
    def __init__(self, cache_dir: Path | str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── public ───────────────────────────────────────────────────────
    def query(self, text: str) -> dict:
        cached = self._cache_get(text)
        if cached is not None:
            return cached
        cmd = os.environ.get(_CMD_ENV, "").strip()
        if not cmd:
            out = {"enabled": False,
                   "reason": f"no external world-intel MCP bound — set {_CMD_ENV} "
                             "to a stdio JSON-RPC server command (lazy, default-off "
                             "per config/integrations.yaml)",
                   "events": None}
            self._cache_put(text, out)
            return out
        try:
            payload = self._call_server(cmd, text)
        except Exception as e:  # broken server must degrade, never crash
            return {"enabled": False, "error": f"world-intel MCP call failed: {e}",
                    "events": None}
        out = {"enabled": True, "events": payload.get("events", []),
               "fetched_at": round(time.time(), 3)}
        self._cache_put(text, out)
        return out

    # ── stdio JSON-RPC (fresh process per query: lazy by definition) ──
    def _call_server(self, cmd: str, text: str) -> dict:
        import shlex
        argv = shlex.split(cmd, posix=(os.name != "nt")) if os.name != "nt" \
            else cmd.split()
        proc = subprocess.run(
            argv,
            input=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {"protocolVersion": "2024-11-05",
                                         "capabilities": {},
                                         "clientInfo": {"name": "awiki-world-intel",
                                                        "version": "1"}}}) + "\n" +
                 json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                             "params": {"name": "query",
                                        "arguments": {"text": text}}}) + "\n",
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=_TIMEOUT_S,
        )
        result = None
        for line in proc.stdout.splitlines():
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == 2 and "result" in resp:
                result = resp["result"]
        if result is None:
            raise RuntimeError(
                f"no tools/call response (rc={proc.returncode}) "
                f"stderr={proc.stderr[-200:]!r}")
        content = result.get("content") or [{}]
        try:
            return json.loads(content[0].get("text", "{}"))
        except json.JSONDecodeError:
            return {}

    # ── regenerable local cache ─────────────────────────────────────
    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"world-intel-{key}.json"

    def _cache_get(self, text: str):
        p = self._cache_path(text)
        if not p.is_file():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("fetched_at", 0) > _CACHE_TTL_S:
            return None
        return data

    def _cache_put(self, text: str, out: dict) -> None:
        try:
            self._cache_path(text).write_text(
                json.dumps(out, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # cache is best-effort regenerable state
