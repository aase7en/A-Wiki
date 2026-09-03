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
import os
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


def _validate_target_repo(target_repo_root) -> Path:
    """Trusted external-target seam: validate the target supplies ONLY git
    truth (HEAD/clean/worktree identity). Absolute existing Git checkout or
    linked worktree (gitfile) only; anything else fails closed bounded."""
    if not isinstance(target_repo_root, (str, Path)):
        raise ReviewBridgeError("target repo root must be an absolute path")
    raw = Path(target_repo_root)
    if not raw.is_absolute():
        raise ReviewBridgeError(
            "target repo root must be an absolute path (relative paths rejected)")
    resolved = raw.resolve(strict=False)
    if not resolved.is_dir():
        raise ReviewBridgeError("target repo does not exist or is not a directory")
    if not (resolved / ".git").exists():
        raise ReviewBridgeError("target repo is not a Git checkout (.git missing)")
    try:
        out = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--git-dir"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReviewBridgeError(f"target repo git check failed: {e!r}") from e
    if out.returncode != 0:
        raise ReviewBridgeError("target repo is not a usable Git worktree")
    return resolved


def _target_state_namespace(authority_root: Path, target_root: Path) -> Path:
    """Fail-closed namespace for one resolved target path spelling.

    OS family is not filesystem case semantics: Windows supports per-directory
    case sensitivity. Hash the resolved spelling exactly. False separation of
    aliases is acceptable; merging distinct targets into one state namespace is not.
    """
    canonical = str(target_root).replace("\\", "/")
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return authority_root / ".tmp" / "review-bridge-targets" / digest


class ReviewBridge:
    """Thin adapter over ReviewBus + ALoopReview for the external mailbox seam."""

    def __init__(self, repo_root: Path | str, state_dir: Path | str | None = None,
                 phase: str = "XRB",
                 target_repo_root: Path | str | None = None):
        authority = Path(repo_root)
        self._authority_root = authority
        if target_repo_root is None:
            # Backward compatibility: the authority repo is also the review
            # target — HEAD/dirty/state behavior is exactly as before.
            self._root = authority
            default_state = authority / ".tmp" / "review-bridge"
        else:
            # External target seam: the target supplies ONLY git truth; the
            # authority keeps scripts/lib, ReviewBus/ALoopReview, and the
            # durable namespaced review state. An explicit state_dir would let
            # a caller redirect authority bookkeeping into the target itself,
            # so it is not a supported override in external-target mode.
            if state_dir is not None:
                raise ReviewBridgeError(
                    "external target state is authority-owned; state_dir override is not allowed"
                )
            self._root = _validate_target_repo(target_repo_root)
            default_state = _target_state_namespace(authority, self._root)
        lib = str(authority / "scripts" / "lib")
        if lib not in sys.path:
            sys.path.insert(0, lib)
        import review_bus as rb
        import a_loop_review as alr
        self._rb = rb
        self._alr = alr
        self.bus = rb.ReviewBus(
            Path(state_dir) if state_dir else default_state,
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
        try:
            m = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ReviewBridgeError(
                f"task map unreadable/invalid JSON for {task_id!r}: {exc}") from None
        if not isinstance(m, dict):
            raise ReviewBridgeError(f"task map must be an object for {task_id!r}")
        if m.get("task_id") != task_id:
            raise ReviewBridgeError(f"task map identity mismatch for {task_id!r}")
        cycle = m.get("cycle")
        if not isinstance(cycle, str) or not cycle or len(cycle) > 100 or _CTRL_RE.search(cycle):
            raise ReviewBridgeError(f"task map cycle invalid for {task_id!r}")
        head = m.get("head_sha")
        if not isinstance(head, str) or not _SHA_RE.fullmatch(head):
            raise ReviewBridgeError(f"task map head_sha invalid for {task_id!r}")
        if m.get("ingest") is not None and not isinstance(m.get("ingest"), dict):
            raise ReviewBridgeError(f"task map ingest record invalid for {task_id!r}")
        return m

    def _save_map(self, task_id: str, m: dict) -> None:
        path = self._map_path(task_id)
        temporary = path.with_name(
            f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}"
        )
        try:
            temporary.write_text(json.dumps(m, indent=2), encoding="utf-8")
            os.replace(temporary, path)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _load_bound_map(self, task_id: str) -> tuple[dict, dict]:
        m = self._load_map(task_id)
        try:
            doc = self.bus.load(m["cycle"])
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(f"task review state invalid: {exc}") from None
        if doc.get("executor") != f"bridge:{task_id}":
            raise ReviewBridgeError(
                f"task map cycle identity mismatch for {task_id!r}"
            )
        if doc.get("head_sha") != m.get("head_sha"):
            raise ReviewBridgeError(
                f"task map head mismatch for {task_id!r}"
            )
        return m, doc

    def _actual_head(self) -> str:
        try:
            return self.gate.head_sha()
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(f"git head unavailable: {exc}") from None

    def _require_current_clean_head(self, expected_head: str) -> str:
        self._require_clean_worktree()
        actual = self._actual_head()
        if actual != expected_head:
            raise ReviewBridgeError(
                f"current git head {actual[:12]} does not match review head "
                f"{expected_head[:12]} — stale evidence fails closed"
            )
        return actual

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
        if self._map_path(task_id).is_file():
            m, doc = self._load_bound_map(task_id)
            blockers = [
                f["id"] for f in doc.get("findings", [])
                if f.get("severity") == "blocker" and f.get("state") != "verified"
            ]
            if blockers:
                raise ReviewBridgeError(
                    f"existing review has unresolved blockers: {blockers}"
                )
            raise ReviewBridgeError(
                f"review already open for task {task_id!r}; use record-retest "
                "on a new clean HEAD instead of replacing task→cycle authority"
            )

        head = self._actual_head()
        doc = self.bus.publish(head_sha=head, executor=f"bridge:{task_id}",
                               required_tests=tests, reviewer=rev,
                               transport=TRANSPORT)
        cid = f"{doc['phase']}-c{doc['cycle']}"
        self._save_map(task_id, {"task_id": task_id, "cycle": cid,
                                 "head_sha": head, "reviewer": rev,
                                 "ingest": None})
        return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                "head_sha": head, "transport": TRANSPORT,
                "status": doc["status"]}

    # ── RB-3/4/5 — ingest one durable external result ─────────────────
    def ingest(self, task_id: str, result: dict) -> dict:
        validate_task_id(task_id)
        m, doc = self._load_bound_map(task_id)
        cid = m["cycle"]
        self._require_current_clean_head(doc["head_sha"])
        if not isinstance(result, dict):
            raise ReviewBridgeError("result must be a JSON object")
        encoded = json.dumps(
            result, default=str, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        if len(encoded) > MAX_RESULT_BYTES:
            raise ReviewBridgeError(
                f"result exceeds size bound ({MAX_RESULT_BYTES} bytes)")

        rid = result.get("task_id")
        if rid != task_id:
            raise ReviewBridgeError(
                f"task mismatch: result is for {rid!r}, bridge task is {task_id!r}")
        head = result.get("reviewed_head")
        if not isinstance(head, str) or not _SHA_RE.fullmatch(head):
            raise ReviewBridgeError("reviewed_head must be a git sha")
        if head != doc["head_sha"]:
            raise ReviewBridgeError(
                f"head mismatch: result reviewed {head[:12]}, cycle is at "
                f"{doc['head_sha'][:12]} — stale result fails closed")
        verdict = result.get("verdict")
        if verdict not in VERDICTS:
            raise ReviewBridgeError(
                f"unknown verdict {verdict!r} — expected one of {VERDICTS}")

        model_raw = result.get("model")
        reviewer_raw = result.get("reviewer")
        model = (_bounded_str(model_raw, "model", 100)
                 if model_raw is not None else None)
        result_reviewer = (_bounded_str(reviewer_raw, "reviewer", 100)
                           if reviewer_raw is not None else None)
        if model is not None and result_reviewer is not None and model != result_reviewer:
            raise ReviewBridgeError("conflicting model/reviewer identity")
        supplied_identity = model or result_reviewer
        pinned = m.get("reviewer")
        if pinned is not None and supplied_identity != pinned:
            raise ReviewBridgeError(
                f"reviewer identity mismatch: cycle is pinned to {pinned!r}"
            )
        reviewer = supplied_identity or pinned or "external-reviewer"

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
        replay = prev is not None
        if prev:
            if prev.get("digest") != digest:
                raise ReviewBridgeError(
                    "a different result was already ingested for this cycle — "
                    "record-retest at the new clean HEAD before re-review")
            state = prev.get("state", "complete")
            if state == "complete":
                return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                        "ingested": True, "duplicate": True,
                        "verdict": prev.get("verdict"),
                        "findings": prev.get("finding_ids", []),
                        "status": self.bus.load(cid).get("status")}
            if state != "applying":
                raise ReviewBridgeError("task map ingest state invalid")
            baseline_ids = prev.get("baseline_finding_ids")
            if not isinstance(baseline_ids, list):
                raise ReviewBridgeError("task map ingest baseline invalid")
        else:
            baseline_ids = [f["id"] for f in doc.get("findings", [])]
            applying = {
                "digest": digest, "state": "applying",
                "ts": round(time.time(), 3), "verdict": verdict,
                "reviewer": reviewer, "task_sha256": task_sha256,
                "baseline_finding_ids": baseline_ids,
            }
            m = {**m, "ingest": applying}
            self._save_map(task_id, m)

        current_doc = self.bus.load(cid)
        current_findings = current_doc.get("findings", [])
        current_ids = [f.get("id") for f in current_findings]
        if current_ids[:len(baseline_ids)] != baseline_ids:
            raise ReviewBridgeError(
                "review findings changed outside staged ingest — fail closed"
            )
        added = current_findings[len(baseline_ids):]
        if len(added) > len(mapped):
            raise ReviewBridgeError("review ingest progress exceeds staged result")

        fields = ("severity", "area", "summary", "required_action", "file")
        for index, existing in enumerate(added):
            desired = mapped[index]
            if any(existing.get(key) != desired.get(key) for key in fields):
                raise ReviewBridgeError(
                    "review ingest progress does not match staged result"
                )

        for desired in mapped[len(added):]:
            self.bus.add_finding(cid=cid, **desired)

        current_doc = self.bus.load(cid)
        current_findings = current_doc.get("findings", [])
        added = current_findings[len(baseline_ids):len(baseline_ids) + len(mapped)]
        existing_verdict = current_doc.get("verdict")
        if existing_verdict is None:
            self.bus.set_verdict(reviewer=reviewer, verdict=verdict, cid=cid)
        elif (existing_verdict != verdict
              or current_doc.get("reviewer") != reviewer):
            raise ReviewBridgeError(
                "review verdict changed outside staged ingest — fail closed"
            )

        finding_ids = [f["id"] for f in added]
        complete = {
            "digest": digest, "state": "complete",
            "ts": round(time.time(), 3), "verdict": verdict,
            "reviewer": reviewer, "task_sha256": task_sha256,
            "baseline_finding_ids": baseline_ids,
            "finding_ids": finding_ids,
        }
        self._save_map(task_id, {**m, "ingest": complete})
        return {"schema": SCHEMA, "task_id": task_id, "cycle": cid,
                "ingested": True, "duplicate": replay, "verdict": verdict,
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
        m, doc = self._load_bound_map(task_id)
        try:
            g = self.gate.task_gate(task_id)
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(f"task review state invalid: {exc}") from None
        if g.get("cycle") != m["cycle"]:
            raise ReviewBridgeError(f"task map cycle mismatch for {task_id!r}")

        reasons = list(g.get("reasons", []))
        allow_complete = bool(g.get("allow_complete"))
        if self._git("status", "--porcelain").strip():
            allow_complete = False
            reasons.append("worktree is dirty — READY is unusable")
        actual = self._actual_head()
        if actual != doc["head_sha"]:
            allow_complete = False
            reasons.append(
                f"current git head {actual[:12]} differs from reviewed head "
                f"{doc['head_sha'][:12]}"
            )
        return {"schema": SCHEMA, "task_id": task_id,
                "cycle": g.get("cycle"), "transport": TRANSPORT,
                "allow_complete": allow_complete,
                "status": g.get("status"), "blockers": g.get("blockers", []),
                "reasons": reasons, "head_sha": doc.get("head_sha")}

    def resolve(self, task_id: str, finding_id: str, fix_sha: str) -> dict:
        validate_task_id(task_id)
        m, _doc = self._load_bound_map(task_id)
        if not isinstance(fix_sha, str) or not _SHA_RE.fullmatch(fix_sha):
            raise ReviewBridgeError("fix_sha must be a git sha")
        try:
            finding = self.bus.resolve_finding(
                finding_id, fix_sha=fix_sha, cid=m["cycle"])
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(str(exc)) from None
        return {"schema": SCHEMA, "task_id": task_id, **finding}

    def verify_finding(self, task_id: str, finding_id: str) -> dict:
        validate_task_id(task_id)
        m, _doc = self._load_bound_map(task_id)
        try:
            finding = self.bus.verify_finding(finding_id, cid=m["cycle"])
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(str(exc)) from None
        return {"schema": SCHEMA, "task_id": task_id, **finding}

    # ── RB-7 — trusted evidence (never reachable from reviewer payloads) ──
    def record_retest(self, task_id: str, ok: bool,
                      sha: str | None = None) -> dict:
        validate_task_id(task_id)
        if not isinstance(ok, bool):
            raise ReviewBridgeError("retest ok must be a bool")
        self._require_clean_worktree()
        actual = self._actual_head()
        head = sha if sha is not None else actual
        if not isinstance(head, str) or not _SHA_RE.fullmatch(head):
            raise ReviewBridgeError("retest sha must be a git sha")
        if head != actual:
            raise ReviewBridgeError(
                "retest sha must equal the current clean git HEAD"
            )

        m = self._load_map(task_id)
        try:
            doc = self.bus.load(m["cycle"])
        except self._rb.ReviewBusError as exc:
            raise ReviewBridgeError(f"task review state invalid: {exc}") from None
        if doc.get("executor") != f"bridge:{task_id}":
            raise ReviewBridgeError(f"task map cycle identity mismatch for {task_id!r}")
        bus_head = doc.get("head_sha")
        map_head = m.get("head_sha")
        if bus_head != map_head and bus_head != head:
            raise ReviewBridgeError(
                f"task map head mismatch for {task_id!r}"
            )
        map_head_changed = map_head != head
        doc = self.bus.record_retest(sha=head, ok=ok, cid=m["cycle"])
        updated = {**m, "head_sha": head}
        if map_head_changed:
            updated["ingest"] = None
        self._save_map(task_id, updated)
        return {"schema": SCHEMA, "task_id": task_id, "cycle": m["cycle"],
                "retest": doc["retest"], "status": doc["status"]}

    def record_ci(self, task_id: str, ok: bool) -> dict:
        validate_task_id(task_id)
        if not isinstance(ok, bool):
            raise ReviewBridgeError("ci ok must be a bool")
        m, doc = self._load_bound_map(task_id)
        self._require_current_clean_head(doc["head_sha"])
        doc = self.bus.record_ci(ok=ok, cid=m["cycle"])
        return {"schema": SCHEMA, "task_id": task_id, "cycle": m["cycle"],
                "ci": doc["ci"], "status": doc["status"]}
