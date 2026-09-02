"""review_bridge.py — thin brain-side Review Bridge (WRAP, not new).

Exposes the existing ReviewBus state engine (scripts/lib/review_bus.py — the
ONLY review-state authority) and the A-Conductor stable external-agent mailbox
seam (transport = remote-queue, already in schemas/awiki-review/v1) through a
bounded machine-readable adapter so A-Conductor / external reviewers can drive
review cycles without human result copy/paste.

Zero duplicate orchestration: no scheduler, no mailbox, no provider registry,
no second state machine, no reviewer/provider/mailbox process is ever spawned
from here. Every state transition delegates to ReviewBus; the task<->cycle map
reuses ALoopReview. A reviewer PASS alone NEVER yields READY — retest/CI
evidence only enters through the explicit trusted operations (record-retest /
record-ci), never through ingested reviewer payloads.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "awiki-review-bridge/v1"
TRANSPORT = "remote-queue"

VERDICTS = ("PASS", "PASS_WITH_NOTES", "CHANGES_REQUIRED", "BLOCK")

# RB-4 — the ONE explicit external→ReviewBus severity map (P0/P1/P2 block,
# P3 is a non-blocking note). ReviewBus's richer major/minor vocabulary stays
# available to internal callers; this bridge never invents mappings per field.
SEVERITY_MAP = {"P0": "blocker", "P1": "blocker", "P2": "blocker", "P3": "note"}

_TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")

MAX_RESULT_BYTES = 64_000
MAX_FINDINGS = 50
MAX_TESTS = 20


class ReviewBridgeError(ValueError):
    """Bounded validation/contract failure — safe to print, never a traceback."""


def validate_task_id(task_id: str) -> str:
    """RB-1 — task ids reach a filename (`task-<id>.json`), so only strictly
    bounded safe identifiers pass. Ambiguous ids are REJECTED, never sanitized."""
    if not isinstance(task_id, str) or not task_id:
        raise ReviewBridgeError("task id must be a non-empty string")
    if len(task_id) > 64:
        raise ReviewBridgeError("task id too long (max 64 chars)")
    if "/" in task_id or "\\" in task_id:
        raise ReviewBridgeError("task id must not contain path separators")
    if _CTRL_RE.search(task_id):
        raise ReviewBridgeError("task id must not contain control characters")
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ReviewBridgeError(
            "task id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ "
            "(no leading punctuation, no traversal, no absolute paths)")
    return task_id


def map_severity(external: str) -> str:
    """RB-4 — the single documented external→engine severity mapping."""
    try:
        return SEVERITY_MAP[external]
    except (KeyError, TypeError):
        raise ReviewBridgeError(
            f"unknown external severity {external!r} — expected one of "
            f"{sorted(SEVERITY_MAP)}") from None


def _bounded_str(value, what: str, limit: int) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewBridgeError(f"{what} must be a non-empty string")
    if len(value) > limit:
        raise ReviewBridgeError(f"{what} too long (max {limit} chars)")
    if _CTRL_RE.search(value):
        raise ReviewBridgeError(f"{what} must not contain control characters")
    return value


class ReviewBridge:
    """Thin adapter over ReviewBus + ALoopReview for the external mailbox seam."""

    def __init__(self, repo_root: Path | str, state_dir: Path | str | None = None,
                 phase: str = "XRB"):
        self._root = Path(repo_root)
        lib = str(self._root / "scripts" / "lib")
        if lib not in sys.path:
            sys.path.insert(0, lib)
        import review_bus as rb
        import a_loop_review as alr
        self._rb = rb
        self._alr = alr
        self.bus = rb.ReviewBus(
            Path(state_dir) if state_dir else self._root / ".tmp" / "review-bridge",
            phase=phase)
        self.gate = alr.ALoopReview(self.bus, git_dir=self._root / ".git")

    # ── git helpers (bounded plumbing; worktree-safe like ALoopReview) ──
    def _git(self, *args: str) -> str:
        try:
            out = subprocess.run(["git", "-C", str(self._root), *args],
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ReviewBridgeError(f"git {args[0]} failed: {e!r}") from e
        if out.returncode != 0:
            raise ReviewBridgeError(
                f"git {args[0]} failed: {out.stderr.strip()[:200]}")
        return out.stdout

    def _require_clean_worktree(self) -> None:
        if self._git("status", "--porcelain").strip():
            raise ReviewBridgeError(
                "worktree is dirty — exact-head review requires a clean tree "
                "(commit or stash first)")

    # ── task map (durable, beside the cycles it points at) ────────────
    def _map_path(self, task_id: str) -> Path:
        return self.gate._map_path(validate_task_id(task_id))

    def _load_map(self, task_id: str) -> dict:
        path = self._map_path(task_id)
        if not path.is_file():
            raise ReviewBridgeError(
                f"no review opened for task {task_id!r} — run review open first")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_map(self, task_id: str, m: dict) -> None:
        self._map_path(task_id).write_text(
            json.dumps(m, indent=2), encoding="utf-8")

    # ── RB-2 — open exact-head review ─────────────────────────────────
    def open(self, task_id: str, required_tests: list[str],
             reviewer: str | None = None) -> dict:
        validate_task_id(task_id)
        if (not isinstance(required_tests, list) or not required_tests
                or len(required_tests) > MAX_TESTS):
            raise ReviewBridgeError(
                f"required_tests must be a non-empty list (max {MAX_TESTS})")
        tests = [_bounded_str(t, "required_tests entry", 200)
                 for t in required_tests]
        rev = None
        if reviewer is not None:
            rev = _bounded_str(reviewer, "reviewer", 100)

        self._require_clean_worktree()
        head = self.gate.head_sha()
        doc = self.bus.publish(head_sha=head, executor=f"bridge:{task_id}",
                               required_tests=tests, reviewer=rev,
                               transport=TRANSPORT)
        cid = f"{doc['phase']}-c{doc['cycle']}"
        self._save_map(task_id, {"task_id": task_id, "cycle": cid,
                                 "head_sha": head, "ingest": None})
        return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                "head_sha": head, "transport": TRANSPORT,
                "status": doc["status"]}

    # ── RB-3/4/5 — ingest one durable external result ─────────────────
    def ingest(self, task_id: str, result: dict) -> dict:
        validate_task_id(task_id)
        m = self._load_map(task_id)
        cid = m["cycle"]
        if not isinstance(result, dict):
            raise ReviewBridgeError("result must be a JSON object")
        if len(json.dumps(result, default=str)) > MAX_RESULT_BYTES:
            raise ReviewBridgeError(
                f"result exceeds size bound ({MAX_RESULT_BYTES} bytes)")

        # bounded validated fields only — extra fields are IGNORED, never trusted
        rid = result.get("task_id")
        if rid != task_id:
            raise ReviewBridgeError(
                f"task mismatch: result is for {rid!r}, bridge task is {task_id!r}")
        head = result.get("reviewed_head")
        if not isinstance(head, str) or not _SHA_RE.fullmatch(head):
            raise ReviewBridgeError("reviewed_head must be a git sha")
        doc = self.bus.load(cid)
        if head != doc["head_sha"]:
            raise ReviewBridgeError(
                f"head mismatch: result reviewed {head[:12]}, cycle is at "
                f"{doc['head_sha'][:12]} — stale result fails closed")
        verdict = result.get("verdict")
        if verdict not in VERDICTS:
            raise ReviewBridgeError(
                f"unknown verdict {verdict!r} — expected one of {VERDICTS}")
        reviewer = result.get("model") or result.get("reviewer") or "external-reviewer"
        reviewer = _bounded_str(reviewer, "model/reviewer", 100)
        task_sha256 = result.get("task_sha256")
        if task_sha256 is not None and (
                not isinstance(task_sha256, str)
                or not _SHA256_RE.fullmatch(task_sha256)):
            raise ReviewBridgeError("task_sha256 must be a 64-hex sha256")

        findings_in = result.get("findings", [])
        if not isinstance(findings_in, list) or len(findings_in) > MAX_FINDINGS:
            raise ReviewBridgeError(
                f"findings must be a list (max {MAX_FINDINGS})")
        mapped: list[dict] = []
        for f in findings_in:
            if not isinstance(f, dict):
                raise ReviewBridgeError("each finding must be an object")
            sev = map_severity(f.get("severity"))
            mapped.append({
                "severity": sev,
                "area": _bounded_str(f.get("area"), "finding area", 64),
                "summary": _bounded_str(f.get("summary"), "finding summary", 500),
                "required_action": (
                    _bounded_str(f["required_action"],
                                 "finding required_action", 500)
                    if f.get("required_action") else None),
                "file": (_bounded_str(f["file"], "finding file", 200)
                         if f.get("file") else None),
            })

        if verdict in ("PASS", "PASS_WITH_NOTES") and any(
                f["severity"] == "blocker" for f in mapped):
            raise ReviewBridgeError(
                "passing verdict with a blocking P0/P1/P2 finding is rejected — "
                "fail closed")

        digest = hashlib.sha256(json.dumps(
            {"task_id": rid, "reviewed_head": head, "verdict": verdict,
             "model": reviewer, "task_sha256": task_sha256,
             "findings": mapped}, sort_keys=True).encode("utf-8")).hexdigest()

        prev = m.get("ingest")
        if prev:
            if prev.get("digest") == digest:
                return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                        "ingested": True, "duplicate": True,
                        "verdict": prev.get("verdict"),
                        "findings": prev.get("finding_ids", []),
                        "status": self.bus.load(cid).get("status")}
            raise ReviewBridgeError(
                "a different result was already ingested for this cycle — "
                "resolve findings and re-review at a new head")

        finding_ids = []
        for f in mapped:
            finding = self.bus.add_finding(cid=cid, **f)
            finding_ids.append(finding["id"])
        self.bus.set_verdict(reviewer=reviewer, verdict=verdict, cid=cid)
        self._save_map(task_id, {**m, "ingest": {
            "digest": digest, "ts": round(time.time(), 3),
            "verdict": verdict, "reviewer": reviewer,
            "task_sha256": task_sha256, "finding_ids": finding_ids}})
        return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                "ingested": True, "duplicate": False, "verdict": verdict,
                "reviewer": reviewer, "findings": finding_ids,
                "status": self.bus.load(cid).get("status")}

    # ── RB-6 — status / resolve / verify (thin delegation) ────────────
    def status(self, task_id: str) -> dict:
        validate_task_id(task_id)
        if not self._map_path(task_id).is_file():
            return {"schema": SCHEMA, "task_id": task_id, "cycle": None,
                    "transport": TRANSPORT, "allow_complete": False,
                    "status": "NO_REVIEW", "blockers": [],
                    "reasons": ["no review opened for this task"]}
        g = self.gate.task_gate(task_id)
        m = self._load_map(task_id)
        return {"schema": SCHEMA, "task_id": task_id,
                "cycle": g.get("cycle"), "transport": TRANSPORT,
                "allow_complete": g.get("allow_complete"),
                "status": g.get("status"), "blockers": g.get("blockers", []),
                "reasons": g.get("reasons", []),
                "head_sha": m.get("head_sha")}

    def resolve(self, task_id: str, finding_id: str, fix_sha: str) -> dict:
        validate_task_id(task_id)
        m = self._load_map(task_id)
        if not isinstance(fix_sha, str) or not _SHA_RE.fullmatch(fix_sha):
            raise ReviewBridgeError("fix_sha must be a git sha")
        finding = self.bus.resolve_finding(finding_id, fix_sha=fix_sha,
                                           cid=m["cycle"])
        return {"schema": SCHEMA, "task_id": task_id, **finding}

    def verify_finding(self, task_id: str, finding_id: str) -> dict:
        validate_task_id(task_id)
        m = self._load_map(task_id)
        finding = self.bus.verify_finding(finding_id, cid=m["cycle"])
        return {"schema": SCHEMA, "task_id": task_id, **finding}

    # ── RB-7 — trusted evidence (never reachable from reviewer payloads) ──
    def record_retest(self, task_id: str, ok: bool,
                      sha: str | None = None) -> dict:
        validate_task_id(task_id)
        m = self._load_map(task_id)
        head = sha if sha is not None else self.gate.head_sha()
        if not isinstance(head, str) or not _SHA_RE.fullmatch(head):
            raise ReviewBridgeError("retest sha must be a git sha")
        doc = self.bus.record_retest(sha=head, ok=bool(ok), cid=m["cycle"])
        return {"schema": SCHEMA, "task_id": task_id, "cycle": m["cycle"],
                "retest": doc["retest"], "status": doc["status"]}

    def record_ci(self, task_id: str, ok: bool) -> dict:
        validate_task_id(task_id)
        m = self._load_map(task_id)
        doc = self.bus.record_ci(ok=bool(ok), cid=m["cycle"])
        return {"schema": SCHEMA, "task_id": task_id, "cycle": m["cycle"],
                "ci": doc["ci"], "status": doc["status"]}
