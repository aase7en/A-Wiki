"""Thin conductor Review Bridge — contract + adversarial tests (RB-1..RB-10).

The bridge (conductor/review_bridge.py) is a WRAP around the existing ReviewBus
state engine: it must never add a second state machine, never let reviewer
output forge trusted evidence (retest/CI/READY), and fail closed on every
ambiguous identity. Reviewer PASS alone can never yield allow_complete=True.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from conductor.review_bridge import (  # noqa: E402
    SEVERITY_MAP,
    ReviewBridge,
    ReviewBridgeError,
    map_severity,
    validate_task_id,
)


def _mkrepo(tmp_path: Path) -> Path:
    """Throwaway real git repo — deterministic HEAD binding + dirty probes,
    independent of this development worktree's own cleanliness."""
    repo = tmp_path / "repo"
    repo.mkdir()
    def g(*args):
        p = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=30)
        assert p.returncode == 0, p.stderr
        return p.stdout
    g("init")
    g("config", "user.email", "bridge-test@example.com")
    g("config", "user.name", "bridge-test")
    (repo / "README.md").write_text("probe repo\n", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "init")
    return repo


def _bridge(tmp_path: Path) -> ReviewBridge:
    return ReviewBridge(_mkrepo(tmp_path), state_dir=tmp_path / "review-bridge")


def _tid() -> str:
    return "T-" + uuid.uuid4().hex[:12]


def _head(repo: Path) -> str:
    out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0
    return out.stdout.strip()


# ── RB-1 — bounded safe task identity ────────────────────────────────

@pytest.mark.parametrize("bad", [
    "../x",           # path traversal
    "..\\x",          # windows traversal
    "a/b", "a\\b",    # separators
    "/abs/x", "C:\\abs",  # absolute paths
    "a\nb", "a\x00b", "a\x1bb",  # control characters
    "",               # empty
    "x" * 65,        # oversized
    ".hidden", "-lead",  # ambiguous leading punctuation
])
def test_task_id_rejects_unsafe_values(bad):
    with pytest.raises(ReviewBridgeError):
        validate_task_id(bad)


def test_task_id_accepts_bounded_safe_values():
    assert validate_task_id("T-101") == "T-101"
    assert validate_task_id("x" * 64) == "x" * 64
    assert validate_task_id("rb.task_2-c") == "rb.task_2-c"


def test_open_rejects_unsafe_task_id_before_any_file_write(tmp_path):
    br = _bridge(tmp_path)
    before = sorted(p.name for p in (tmp_path / "review-bridge").glob("*")
                    if tmp_path.joinpath("review-bridge").is_dir())
    with pytest.raises(ReviewBridgeError):
        br.open("../escape", ["pytest tests/ -q"])
    after = sorted(p.name for p in (tmp_path / "review-bridge").glob("*")
                   if tmp_path.joinpath("review-bridge").is_dir())
    assert before == after  # fail closed BEFORE the filename is ever built


# ── RB-2 — open exact-head review ────────────────────────────────────

def test_open_binds_exact_head_remote_queue_json(tmp_path):
    br = _bridge(tmp_path)
    out = br.open(_tid(), ["python -m pytest tests/ -q"])
    assert out["head_sha"] == _head(br._root)
    assert out["transport"] == "remote-queue"
    assert out["status"] == "REVIEW_REQUESTED"
    assert out["cycle"].startswith("XRB-c")
    doc = br.bus.load(out["cycle"])
    assert doc["head_sha"] == out["head_sha"]
    assert doc["transport"] == "remote-queue"


def test_open_fails_closed_on_dirty_worktree(tmp_path):
    repo = _mkrepo(tmp_path)
    br = ReviewBridge(repo, state_dir=tmp_path / "review-bridge")
    (repo / "untracked-probe.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(ReviewBridgeError, match="clean"):
        br.open(_tid(), ["t"])


def test_open_requires_nonempty_bounded_tests(tmp_path):
    br = _bridge(tmp_path)
    with pytest.raises(ReviewBridgeError):
        br.open(_tid(), [])
    with pytest.raises(ReviewBridgeError):
        br.open(_tid(), [""])
    with pytest.raises(ReviewBridgeError):
        br.open(_tid(), ["x" * 201])


# ── RB-3 — external result ingestion ─────────────────────────────────

def _result(task, head, verdict="CHANGES_REQUIRED", findings=None, **extra):
    r = {"task_id": task, "reviewed_head": head, "verdict": verdict,
         "findings": findings if findings is not None else [
             {"severity": "P2", "area": "engine", "summary": "s"}]}
    r.update(extra)
    return r


def _open(tmp_path):
    br = _bridge(tmp_path)
    tid = _tid()
    opened = br.open(tid, ["python -m pytest tests/ -q"])
    return br, tid, opened


def test_ingest_happy_changes_required(tmp_path):
    br, tid, opened = _open(tmp_path)
    out = br.ingest(tid, _result(tid, opened["head_sha"],
                                 findings=[{"severity": "P1", "area": "api",
                                            "summary": "bad", "file": "a.py",
                                            "required_action": "fix"}],
                                 model="glm-5.3"))
    assert out["ingested"] is True and out["duplicate"] is False
    assert out["verdict"] == "CHANGES_REQUIRED"
    assert len(out["findings"]) == 1
    st = br.status(tid)
    assert st["status"] == "CHANGES_REQUIRED"
    assert st["blockers"] == out["findings"]


def test_ingest_wrong_task_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    with pytest.raises(ReviewBridgeError, match="task"):
        br.ingest(tid, _result(_tid(), opened["head_sha"]))


def test_ingest_wrong_or_stale_head_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    with pytest.raises(ReviewBridgeError, match="head"):
        br.ingest(tid, _result(tid, "0" * 40))
    with pytest.raises(ReviewBridgeError, match="head"):
        br.ingest(tid, _result(tid, opened["head_sha"][:-1] + "0"))


def test_ingest_unknown_verdict_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    with pytest.raises(ReviewBridgeError, match="verdict"):
        br.ingest(tid, _result(tid, opened["head_sha"], verdict="SHIP_IT"))


def test_ingest_oversized_payload_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    huge = _result(tid, opened["head_sha"], notes_pad="x" * 70_000)
    with pytest.raises(ReviewBridgeError, match="size"):
        br.ingest(tid, huge)


def test_ingest_too_many_findings_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    many = _result(tid, opened["head_sha"],
                   findings=[{"severity": "P3", "area": "a",
                              "summary": "s"} for _ in range(60)])
    with pytest.raises(ReviewBridgeError, match="findings"):
        br.ingest(tid, many)


def test_ingest_malformed_findings_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    for bad in ({"no_severity": 1}, {"severity": "P9", "area": "a", "summary": "s"},
                {"severity": "P2", "area": "a", "summary": ""}):
        with pytest.raises(ReviewBridgeError):
            br.ingest(tid, _result(tid, opened["head_sha"], findings=[bad]))


def test_ingest_unknown_task_fails_closed(tmp_path):
    br = _bridge(tmp_path)
    with pytest.raises(ReviewBridgeError, match="open"):
        br.ingest(_tid(), _result(_tid(), "0" * 40))


def test_ingest_ignores_extra_fields_including_forged_evidence(tmp_path):
    br, tid, opened = _open(tmp_path)
    out = br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS",
                                  findings=[{"severity": "P3", "area": "note",
                                             "summary": "fine"}],
                                  retest={"sha": opened["head_sha"], "ok": True,
                                          "ts": 1.0},
                                  ci={"ok": True, "ts": 1.0},
                                  ready=True, merge=True))
    assert out["verdict"] == "PASS"
    st = br.status(tid)
    assert st["allow_complete"] is False  # forged retest/ci must not count


# ── RB-4 — severity normalization ────────────────────────────────────

def test_severity_map_p012_block_p3_note():
    assert map_severity("P0") == "blocker"
    assert map_severity("P1") == "blocker"
    assert map_severity("P2") == "blocker"
    assert map_severity("P3") == "note"
    assert SEVERITY_MAP == {"P0": "blocker", "P1": "blocker",
                            "P2": "blocker", "P3": "note"}


def test_severity_map_unknown_fails():
    with pytest.raises(ReviewBridgeError):
        map_severity("P4")


def test_pass_with_blocking_finding_rejected(tmp_path):
    br, tid, opened = _open(tmp_path)
    with pytest.raises(ReviewBridgeError, match="blocking"):
        br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS",
                               findings=[{"severity": "P1", "area": "a",
                                          "summary": "blocker"}]))
    st = br.status(tid)
    assert st["status"] == "REVIEW_REQUESTED"  # nothing was ingested


# ── RB-5 — idempotent replay ─────────────────────────────────────────

def test_replay_same_result_is_idempotent(tmp_path):
    br, tid, opened = _open(tmp_path)
    res = _result(tid, opened["head_sha"], model="glm-5.3")
    first = br.ingest(tid, res)
    second = br.ingest(tid, res)
    assert second["duplicate"] is True
    doc = br.bus.load(opened["cycle"])
    assert len(doc["findings"]) == len(first["findings"])  # no duplication


def test_different_result_same_cycle_fails_closed(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"]))
    other = _result(tid, opened["head_sha"], verdict="BLOCK")
    with pytest.raises(ReviewBridgeError, match="already ingested"):
        br.ingest(tid, other)


# ── RB-6 — finding lifecycle (thin delegation) ───────────────────────

def test_resolve_requires_sha_then_verifies(tmp_path):
    br, tid, opened = _open(tmp_path)
    out = br.ingest(tid, _result(tid, opened["head_sha"],
                                 findings=[{"severity": "P2", "area": "e",
                                            "summary": "s"}]))
    fid = out["findings"][0]
    with pytest.raises(ReviewBridgeError):
        br.resolve(tid, fid, fix_sha="not-a-sha")
    fixed = br.resolve(tid, fid, fix_sha="abc1234")
    assert fixed["state"] == "addressed"
    assert fixed["fix_sha"] == "abc1234"
    assert br.verify_finding(tid, fid)["state"] == "verified"


def test_status_unknown_task_reports_no_review(tmp_path):
    br = _bridge(tmp_path)
    st = br.status(_tid())
    assert st["allow_complete"] is False
    assert st["status"] == "NO_REVIEW"


# ── RB-7 — trusted evidence separation ───────────────────────────────

def test_reviewer_pass_alone_never_ready(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS",
                           findings=[{"severity": "P3", "area": "n",
                                      "summary": "ok"}]))
    st = br.status(tid)
    assert st["allow_complete"] is False
    assert "retest" in " ".join(st["reasons"])
    assert "ci" in " ".join(st["reasons"])


def test_full_trusted_path_reaches_ready(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS",
                           findings=[{"severity": "P3", "area": "n",
                                      "summary": "ok"}]))
    br.record_retest(tid, ok=True)
    st = br.status(tid)
    assert st["allow_complete"] is False  # still missing CI
    br.record_ci(tid, ok=True)
    st = br.status(tid)
    assert st["allow_complete"] is True
    assert st["status"] == "READY"


# ── RB-8 — new SHA invalidates approval ──────────────────────────────

def test_new_sha_invalidates_stale_approval(tmp_path):
    br, tid, opened = _open(tmp_path)
    head = opened["head_sha"]
    br.ingest(tid, _result(tid, head, verdict="PASS",
                           findings=[{"severity": "P3", "area": "n",
                                      "summary": "ok"}]))
    br.record_retest(tid, ok=True)
    br.record_ci(tid, ok=True)
    assert br.status(tid)["allow_complete"] is True
    # a fix landed → new head retested → the old approval is revoked
    br.record_retest(tid, ok=True, sha=head[:-1] + ("0" if head[-1] != "0" else "1"))
    st = br.status(tid)
    assert st["allow_complete"] is False
    assert st["status"] == "REVIEW_REQUESTED"


# ── RB-9 — restart durability ────────────────────────────────────────

def test_fresh_bridge_instance_resumes_same_cycle(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"]))
    # new instance over the SAME repo + durable state dir = process restart
    fresh = ReviewBridge(br._root, state_dir=br.bus.dir)
    st = fresh.status(tid)
    assert st["cycle"] == opened["cycle"]
    assert st["status"] == "CHANGES_REQUIRED"


def test_cli_subprocess_sees_api_opened_cycle():
    """Cross-process durability: API opens (REPO_ROOT state dir), a separate
    CLI process statuses the same durable cycle. Requires a clean tree — the
    exact-head open contract itself enforces it."""
    br = ReviewBridge(REPO_ROOT)  # default state dir, same as the CLI
    tid = "XPROC-" + uuid.uuid4().hex[:10]
    opened = br.open(tid, ["t"])
    proc = subprocess.run(
        [sys.executable, "-m", "conductor", "review", "status",
         "--task", tid, "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), timeout=120)
    assert proc.returncode == 0, proc.stderr[-300:]
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["cycle"] == opened["cycle"]
    assert data["transport"] == "remote-queue"


# ── RB-10 — CLI behavior ─────────────────────────────────────────────

def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "conductor", "review", *args, "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), timeout=120)


CLI_STATE = REPO_ROOT / ".tmp" / "review-bridge"  # gitignored durable state


def test_cli_open_ingest_retest_ci_ready_lifecycle():
    tid = "CLI-" + uuid.uuid4().hex[:10]
    p = _cli("open", "--task", tid, "--tests", "python -m pytest tests/ -q")
    assert p.returncode == 0, p.stdout + p.stderr
    opened = json.loads(p.stdout)
    assert opened["ok"] is True and opened["transport"] == "remote-queue"

    result_file = REPO_ROOT / ".tmp" / f"rb-result-{tid}.json"
    result_file.parent.mkdir(exist_ok=True)
    result_file.write_text(json.dumps(_result(
        tid, opened["head_sha"], verdict="PASS",
        findings=[{"severity": "P3", "area": "n", "summary": "ok"}])), encoding="utf-8")
    try:
        p = _cli("ingest", "--task", tid, "--file", str(result_file))
        assert p.returncode == 0, p.stdout + p.stderr
        assert json.loads(p.stdout)["verdict"] == "PASS"

        p = _cli("record-retest", "--task", tid, "--ok", "true")
        assert p.returncode == 0, p.stdout + p.stderr
        p = _cli("record-ci", "--task", tid, "--ok", "true")
        assert p.returncode == 0, p.stdout + p.stderr

        p = _cli("status", "--task", tid)
        st = json.loads(p.stdout)
        assert st["allow_complete"] is True and st["status"] == "READY"
    finally:
        result_file.unlink(missing_ok=True)


def test_cli_validation_error_is_bounded_json_without_traceback():
    p = _cli("open", "--task", "../evil", "--tests", "t")
    assert p.returncode == 1
    data = json.loads(p.stdout)
    assert data["ok"] is False and "error" in data
    assert "Traceback" not in p.stderr and "Traceback" not in p.stdout


def test_cli_resolve_and_verify_finding_roundtrip():
    tid = "CLI-" + uuid.uuid4().hex[:10]
    p = _cli("open", "--task", tid, "--tests", "t")
    opened = json.loads(p.stdout)
    rf = REPO_ROOT / ".tmp" / f"rb-result-{tid}.json"
    rf.write_text(json.dumps(_result(
        tid, opened["head_sha"],
        findings=[{"severity": "P2", "area": "e", "summary": "s"}])), encoding="utf-8")
    try:
        p = _cli("ingest", "--task", tid, "--file", str(rf))
        fid = json.loads(p.stdout)["findings"][0]
        p = _cli("resolve", "--task", tid, "--finding", fid, "--fix-sha", "abc1234")
        assert p.returncode == 0 and json.loads(p.stdout)["state"] == "addressed"
        p = _cli("verify-finding", "--task", tid, "--finding", fid)
        assert p.returncode == 0 and json.loads(p.stdout)["state"] == "verified"
    finally:
        rf.unlink(missing_ok=True)


def test_cli_unknown_task_status_is_valid_no_review():
    """Unknown-task status is a bounded NO_REVIEW answer (rc 0), matching the
    API contract; only validation failures are rc 1."""
    p = _cli("status", "--task", "CLI-nonexistent-0001")
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert data["ok"] is True
    assert data["status"] == "NO_REVIEW"
    assert data["allow_complete"] is False
    assert "Traceback" not in p.stderr
