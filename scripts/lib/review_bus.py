"""review_bus.py — Agent Review Bus state engine (Phase 8).

Implements the operational half of schemas/awiki-review/v1: publish →
findings → fixes → retest → CI → READY, with SHA-attributable cycles
(new head invalidates approval) and disk-durable state that survives
process/session restarts.

Scope discipline (§16-10 + repo rules):
  - STATE ONLY. This engine never merges, pushes, rebases or spawns
    external processes. Merging stays a human/CI decision.
  - The reviewer is DATA (name + transport), so any reviewer
    implementation can be swapped without touching this protocol.

Storage: one JSON doc per cycle at <dir>/<phase>-c<cycle>.json, written
atomically (atomic_json) and validated against the awiki-review/v1
schema on every transition — a state that cannot be expressed by the
contract is refused, not silently coerced.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from atomic_json import atomic_write

_SCHEMA_CONST = "awiki-review/v1"
_OPEN_BLOCKERS = ("open",)  # states that still block READY
_PASSING_VERDICTS = ("PASS", "PASS_WITH_NOTES")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class ReviewBusError(RuntimeError):
    """Invalid transition or contract violation — state is left untouched."""


def _now() -> float:
    return round(time.time(), 3)


class ReviewBus:
    def __init__(self, dir_: Path | str, phase: str = "P8"):
        self.dir = Path(dir_)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.phase = phase

    # ── persistence ───────────────────────────────────────────────────
    def _path(self, cycle: int) -> Path:
        return self.dir / f"{self.phase}-c{cycle}.json"

    def load(self, cid: str) -> dict:
        doc = json.loads((self.dir / f"{cid}.json").read_text(encoding="utf-8"))
        return doc

    def _save(self, doc: dict) -> None:
        atomic_write(self._path(doc["cycle"]), doc, indent=2)

    def _next_cycle(self) -> int:
        existing = [p.stem.split("-c")[-1] for p in self.dir.glob(f"{self.phase}-c*.json")]
        return max((int(c) for c in existing if c.isdigit()), default=0) + 1

    def _next_finding_no(self, doc: dict) -> int:
        nums = []
        for f in doc.get("findings", []):
            m = re.fullmatch(r"R-[A-Za-z0-9-]+-(\d{3})", f["id"])
            if m:
                nums.append(int(m.group(1)))
        return max(nums, default=0) + 1

    @staticmethod
    def _validate(doc: dict) -> None:
        import jsonschema  # CI authority (requirements.txt)
        schema_path = (Path(__file__).resolve().parents[2]
                       / "schemas" / "awiki-review" / "v1.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(doc, schema)
        except jsonschema.ValidationError as e:
            raise ReviewBusError(f"state violates awiki-review/v1: {e.message}") from e

    # ── lifecycle ─────────────────────────────────────────────────────
    def publish(self, *, head_sha: str, executor: str,
                required_tests: list[str],
                reviewer: Optional[str] = None,
                transport: str = "local-mcp") -> dict:
        if not _SHA_RE.fullmatch(head_sha):
            raise ReviewBusError(f"head_sha must be a sha: {head_sha!r}")
        doc: dict[str, Any] = {
            "schema": _SCHEMA_CONST,
            "phase": self.phase,
            "cycle": self._next_cycle(),
            "executor": executor,
            "status": "REVIEW_REQUESTED",
            "head_sha": head_sha,
            "findings": [],
            "required_tests": required_tests,
            "transport": transport,
            "retest": None,
            "ci": None,
            "retries": 0,
            "max_retries": 3,
            "halt_reason": None,
        }
        if reviewer:
            doc["reviewer"] = reviewer
        self._validate(doc)
        self._save(doc)
        return doc

    def add_finding(self, *, severity: str, area: str, summary: str,
                    required_action: Optional[str] = None,
                    file: Optional[str] = None,
                    cid=None) -> dict:
        doc = self._load_latest(cid)
        finding = {
            "id": f"R-{self.phase}-{self._next_finding_no(doc):03d}",
            "severity": severity,
            "area": area,
            "summary": summary,
            "required_action": required_action,
            "file": file,
            "state": "open",
            "fix_sha": None,
        }
        doc["findings"].append(finding)
        self._validate(doc)
        self._save(doc)
        return finding

    def resolve_finding(self, finding_id: str, *, fix_sha: str,
                        cid: Optional[int] = None) -> dict:
        if not _SHA_RE.fullmatch(fix_sha):
            raise ReviewBusError(f"fix_sha must be a sha: {fix_sha!r}")
        doc, finding = self._finding(doc_of=None, finding_id=finding_id, cid=cid)
        if finding["state"] not in ("open", "addressed"):
            raise ReviewBusError(
                f"{finding_id} is {finding['state']} — only open findings resolve")
        finding["state"] = "addressed"
        finding["fix_sha"] = fix_sha
        self._validate(doc)
        self._save(doc)
        return finding

    def verify_finding(self, finding_id: str, *, cid: Optional[int] = None) -> dict:
        doc, finding = self._finding(doc_of=None, finding_id=finding_id, cid=cid)
        if finding["state"] not in ("open", "addressed"):
            raise ReviewBusError(
                f"{finding_id} is {finding['state']} — cannot be verified")
        finding["state"] = "verified"
        self._validate(doc)
        self._save(doc)
        return finding

    def set_verdict(self, *, reviewer: str, verdict: str,
                    cid: Optional[int] = None) -> dict:
        doc = self._load_latest(cid)
        doc["reviewer"] = reviewer
        doc["verdict"] = verdict
        if verdict in _PASSING_VERDICTS:
            blockers = [f["id"] for f in doc["findings"]
                        if f["state"] == "open" and f["severity"] == "blocker"]
            if blockers:
                raise ReviewBusError(
                    f"cannot pass with open blockers: {blockers}")
            doc["status"] = "APPROVED"
            doc["next_action"] = "RUN_CI_GATE"
        else:
            doc["status"] = "CHANGES_REQUIRED"
            doc["next_action"] = "FIX_AND_REREVIEW"
        self._validate(doc)
        self._save(doc)
        return doc

    def record_retest(self, *, sha: str, ok: bool,
                      cid: Optional[int] = None) -> dict:
        if not _SHA_RE.fullmatch(sha):
            raise ReviewBusError(f"sha must be a sha: {sha!r}")
        doc = self._load_latest(cid)
        if sha != doc["head_sha"] and doc["status"] in ("APPROVED", "READY"):
            # §16-7: a new SHA invalidates approval earned at the old head —
            # the cycle re-enters review at the new SHA (verdict dropped).
            doc["status"] = "REVIEW_REQUESTED"
            doc.pop("verdict", None)
            doc["next_action"] = "FIX_AND_REREVIEW"
        doc["head_sha"] = sha
        doc["retest"] = {"sha": sha, "ok": bool(ok), "ts": _now()}
        if not ok:
            doc["retries"] = int(doc.get("retries", 0)) + 1
            if doc["retries"] >= int(doc.get("max_retries", 3)):
                doc["halt_reason"] = "retries-exceeded"
        self._validate(doc)
        self._save(doc)
        return doc

    def record_ci(self, *, ok: bool, cid: Optional[int] = None) -> dict:
        doc = self._load_latest(cid)
        doc["ci"] = {"ok": bool(ok), "ts": _now()}
        self._validate(doc)
        self._save(doc)
        return doc

    def readiness(self, cid=None) -> dict:
        """READY iff: passing verdict at the CURRENT sha, no open blockers,
        retest passed at this sha, CI green. Reports every gap otherwise."""
        doc = self._load_latest(cid)
        reasons: list[str] = []
        if doc.get("halt_reason"):
            reasons.append(f"halted: {doc['halt_reason']}")
        if doc.get("verdict") not in _PASSING_VERDICTS:
            reasons.append("no passing verdict")
        blockers = [f["id"] for f in doc["findings"]
                    if f["state"] == "open" and f["severity"] == "blocker"]
        if blockers:
            reasons.append(f"open blockers: {blockers}")
        retest = doc.get("retest") or {}
        if not retest.get("ok") or retest.get("sha") != doc["head_sha"]:
            reasons.append("retest not passed at current head")
        ci = doc.get("ci") or {}
        if not ci.get("ok"):
            reasons.append("ci not green")
        if not reasons:
            doc["status"] = "READY"
            doc["next_action"] = "MARK_READY"
            self._validate(doc)
            self._save(doc)
            return {"ready": True, "reasons": [], "cycle": doc["cycle"]}
        return {"ready": False, "reasons": reasons, "cycle": doc["cycle"]}

    def clear_halt(self, cid=None) -> dict:
        """Human reset of a halted cycle (retries counter back to 0)."""
        doc = self._load_latest(cid)
        doc["halt_reason"] = None
        doc["retries"] = 0
        self._validate(doc)
        self._save(doc)
        return doc

    # ── helpers ───────────────────────────────────────────────────────
    def _load_latest(self, cid) -> dict:
        if cid is None:
            cycle: Optional[int] = self._next_cycle() - 1
        elif isinstance(cid, int):
            cycle = cid
        else:
            m = re.fullmatch(r"[A-Za-z0-9-]+-c(\d+)", str(cid))
            if not m:
                raise ReviewBusError(f"bad cycle id: {cid!r}")
            cycle = int(m.group(1))
        if cycle is None or cycle < 1:
            raise ReviewBusError("no review cycle published yet")
        path = self._path(cycle)
        if not path.is_file():
            raise ReviewBusError(f"cycle {cycle} not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def _finding(self, *, doc_of, finding_id: str, cid: Optional[int]):
        doc = self._load_latest(cid)
        for f in doc["findings"]:
            if f["id"] == finding_id:
                return doc, f
        raise ReviewBusError(f"finding {finding_id} not found")
