"""world-intel lazy MCP bridge — Phase 10 (optional external modules).

Contract from config/integrations.yaml: lazy, default-off, no vendoring,
domain-triggered, local regenerable cache (never committed). The bridge
degrades gracefully when no external server is bound; when one IS bound
(via env WORLD_INTEL_MCP_CMD), it speaks stdio JSON-RPC to it and
normalizes responses. No vendor names or hardcoded endpoints in the lib.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from world_intel import WorldIntel  # noqa: E402

FAKE_SERVER = textwrap.dedent("""
    import json, sys

    def send(obj):
        print(json.dumps(obj), flush=True)

    for line in sys.stdin:
        req = json.loads(line)
        rid = req.get("id")
        if req.get("method") == "initialize":
            send({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "serverInfo": {"name": "fake-world", "version": "0"}}})
        elif req.get("method") == "tools/call":
            payload = {"events": [{"title": "flood alert",
                                   "domain": "disaster"}]}
            send({"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": json.dumps(payload)}],
                "isError": False}})
""")


def test_not_enabled_degrades_gracefully(tmp_path, monkeypatch):
    monkeypatch.delenv("WORLD_INTEL_MCP_CMD", raising=False)
    wi = WorldIntel(cache_dir=tmp_path / "cache")
    out = wi.query("flood risk bangkok")
    assert out.get("enabled") is False
    assert "reason" in out and "WORLD_INTEL_MCP_CMD" in out["reason"]
    assert out.get("events") in (None, [])


def test_bound_server_answers_via_stdio_jsonrpc(tmp_path, monkeypatch):
    server = tmp_path / "fake_mcp.py"
    server.write_text(FAKE_SERVER, encoding="utf-8")
    monkeypatch.setenv("WORLD_INTEL_MCP_CMD", f"{sys.executable} {server}")
    wi = WorldIntel(cache_dir=tmp_path / "cache")
    out = wi.query("flood risk bangkok")
    assert out.get("enabled") is True
    assert out["events"][0]["title"] == "flood alert"


def test_cache_is_local_and_regenerable(tmp_path, monkeypatch):
    """integration contract: cache lands under the cache dir, never repo."""
    server = tmp_path / "fake_mcp.py"
    server.write_text(FAKE_SERVER, encoding="utf-8")
    monkeypatch.setenv("WORLD_INTEL_MCP_CMD", f"{sys.executable} {server}")
    cache = tmp_path / "cache"
    wi = WorldIntel(cache_dir=cache)
    wi.query("flood risk")
    cached = list(cache.glob("*.json"))
    assert cached, "second query should be servable from the local cache"
    # cached payload equals a fresh call
    again = wi.query("flood risk")
    assert again["events"][0]["title"] == "flood alert"


def test_broken_server_degrades_not_crash(tmp_path, monkeypatch):
    monkeypatch.setenv("WORLD_INTEL_MCP_CMD",
                       f"{sys.executable} -c import\\ sys;sys.exit(3)")
    wi = WorldIntel(cache_dir=tmp_path / "cache")
    out = wi.query("anything")
    assert out.get("enabled") is False or out.get("error"), out


def test_lib_has_no_vendor_names():
    src = (REPO_ROOT / "scripts" / "lib" / "world_intel.py").read_text(
        encoding="utf-8").lower()
    for vendor in ("openai", "anthropic", "perplexity", "newsapi", "openrouter"):
        assert vendor not in src, f"vendor leak: {vendor}"
