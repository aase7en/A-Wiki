"""Thin conductor Review Bridge โ€” contract + adversarial tests (RB-1..RB-10).

The bridge (conductor/review_bridge.py) is a WRAP around the existing ReviewBus
state engine: it must never add a second state machine, never let reviewer
output forge trusted evidence (retest/CI/READY), and fail closed on every
ambiguous identity. Reviewer PASS alone can never yield allow_complete=True.
"""
from __future__ import annotations

import json
import shutil
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
    """Throwaway real git repo โ€” deterministic HEAD binding + dirty probes,
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
    (repo / ".gitignore").write_text(".tmp/\n__pycache__/\n*.pyc\n", encoding="utf-8")
    for rel in (
        "scripts/lib/review_bus.py",
        "scripts/lib/a_loop_review.py",
        "scripts/lib/atomic_json.py",
        "schemas/awiki-review/v1.schema.json",
    ):
        source = REPO_ROOT / rel
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
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


# โ”€โ”€ RB-1 โ€” bounded safe task identity โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-2 โ€” open exact-head review โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-3 โ€” external result ingestion โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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
    wrong_tail = "0" if opened["head_sha"][-1] != "0" else "1"
    with pytest.raises(ReviewBridgeError, match="head"):
        br.ingest(tid, _result(tid, opened["head_sha"][:-1] + wrong_tail))


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


# โ”€โ”€ RB-4 โ€” severity normalization โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-5 โ€” idempotent replay โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-6 โ€” finding lifecycle (thin delegation) โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-7 โ€” trusted evidence separation โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

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


# โ”€โ”€ RB-8 โ€” new SHA invalidates approval โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

def test_new_sha_invalidates_stale_approval(tmp_path):
    br, tid, opened = _open(tmp_path)
    head = opened["head_sha"]
    br.ingest(tid, _result(tid, head, verdict="PASS",
                           findings=[{"severity": "P3", "area": "n",
                                      "summary": "ok"}]))
    br.record_retest(tid, ok=True)
    br.record_ci(tid, ok=True)
    assert br.status(tid)["allow_complete"] is True
    # a fix landed โ’ new head retested โ’ the old approval is revoked
    new_head = _commit_new_head(br._root, "rb8-new-head.txt")
    br.record_retest(tid, ok=True, sha=new_head)
    st = br.status(tid)
    assert st["allow_complete"] is False
    assert st["status"] == "REVIEW_REQUESTED"


# โ”€โ”€ RB-9 โ€” restart durability โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

def test_fresh_bridge_instance_resumes_same_cycle(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"]))
    # new instance over the SAME repo + durable state dir = process restart
    fresh = ReviewBridge(br._root, state_dir=br.bus.dir)
    st = fresh.status(tid)
    assert st["cycle"] == opened["cycle"]
    assert st["status"] == "CHANGES_REQUIRED"


def test_cli_subprocess_sees_api_opened_cycle(tmp_path):
    """Cross-process durability uses a throwaway clean git repo so unrelated
    suite artifacts cannot weaken or accidentally trip the clean-HEAD gate."""
    repo = _mkrepo(tmp_path)
    br = ReviewBridge(repo)
    tid = "XPROC-" + uuid.uuid4().hex[:10]
    opened = br.open(tid, ["t"])
    proc = _cli("status", "--task", tid, repo=repo)
    assert proc.returncode == 0, proc.stderr[-300:]
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["cycle"] == opened["cycle"]
    assert data["transport"] == "remote-queue"


# โ”€โ”€ RB-10 โ€” CLI behavior โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

def _cli(*args, repo=REPO_ROOT):
    if Path(repo) == REPO_ROOT:
        command = [sys.executable, "-m", "conductor", "review", *args, "--json"]
    else:
        code = (
            "import sys; from pathlib import Path; import conductor.cli as c; "
            "c.REPO_ROOT=Path(sys.argv[1]); "
            "raise SystemExit(c.main(sys.argv[2:]))"
        )
        command = [sys.executable, "-c", code, str(repo),
                   "review", *args, "--json"]
    return subprocess.run(
        command, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), timeout=120)


CLI_STATE = REPO_ROOT / ".tmp" / "review-bridge"  # gitignored durable state


def test_cli_open_ingest_retest_ci_ready_lifecycle(tmp_path):
    repo = _mkrepo(tmp_path)
    tid = "CLI-" + uuid.uuid4().hex[:10]
    p = _cli("open", "--task", tid, "--tests", "python -m pytest tests/ -q", repo=repo)
    assert p.returncode == 0, p.stdout + p.stderr
    opened = json.loads(p.stdout)
    assert opened["ok"] is True and opened["transport"] == "remote-queue"

    result_file = repo / ".tmp" / f"rb-result-{tid}.json"
    result_file.parent.mkdir(exist_ok=True)
    result_file.write_text(json.dumps(_result(
        tid, opened["head_sha"], verdict="PASS",
        findings=[{"severity": "P3", "area": "n", "summary": "ok"}])), encoding="utf-8")
    try:
        p = _cli("ingest", "--task", tid, "--file", str(result_file), repo=repo)
        assert p.returncode == 0, p.stdout + p.stderr
        assert json.loads(p.stdout)["verdict"] == "PASS"

        p = _cli("record-retest", "--task", tid, "--ok", "true", repo=repo)
        assert p.returncode == 0, p.stdout + p.stderr
        p = _cli("record-ci", "--task", tid, "--ok", "true", repo=repo)
        assert p.returncode == 0, p.stdout + p.stderr

        p = _cli("status", "--task", tid, repo=repo)
        st = json.loads(p.stdout)
        assert st["allow_complete"] is True and st["status"] == "READY"
    finally:
        result_file.unlink(missing_ok=True)


def test_cli_validation_error_is_bounded_json_without_traceback(tmp_path):
    repo = _mkrepo(tmp_path)
    p = _cli("open", "--task", "../evil", "--tests", "t", repo=repo)
    assert p.returncode == 1
    data = json.loads(p.stdout)
    assert data["ok"] is False and "error" in data
    assert "Traceback" not in p.stderr and "Traceback" not in p.stdout


def test_cli_resolve_and_verify_finding_roundtrip(tmp_path):
    repo = _mkrepo(tmp_path)
    tid = "CLI-" + uuid.uuid4().hex[:10]
    p = _cli("open", "--task", tid, "--tests", "t", repo=repo)
    opened = json.loads(p.stdout)
    rf = repo / ".tmp" / f"rb-result-{tid}.json"
    rf.write_text(json.dumps(_result(
        tid, opened["head_sha"],
        findings=[{"severity": "P2", "area": "e", "summary": "s"}])), encoding="utf-8")
    try:
        p = _cli("ingest", "--task", tid, "--file", str(rf), repo=repo)
        fid = json.loads(p.stdout)["findings"][0]
        p = _cli("resolve", "--task", tid, "--finding", fid, "--fix-sha", "abc1234", repo=repo)
        assert p.returncode == 0 and json.loads(p.stdout)["state"] == "addressed"
        p = _cli("verify-finding", "--task", tid, "--finding", fid, repo=repo)
        assert p.returncode == 0 and json.loads(p.stdout)["state"] == "verified"
    finally:
        rf.unlink(missing_ok=True)


def test_cli_unknown_task_status_is_valid_no_review(tmp_path):
    """Unknown-task status is a bounded NO_REVIEW answer (rc 0), matching the
    API contract; only validation failures are rc 1."""
    repo = _mkrepo(tmp_path)
    p = _cli("status", "--task", "CLI-nonexistent-0001", repo=repo)
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert data["ok"] is True
    assert data["status"] == "NO_REVIEW"
    assert data["allow_complete"] is False
    assert "Traceback" not in p.stderr


# --- GPT Primary repair REDs: trusted evidence + engine error boundary ---

def test_trusted_retest_requires_actual_bool(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))
    with pytest.raises(ReviewBridgeError, match="bool"):
        br.record_retest(tid, ok="false")
    assert br.status(tid)["allow_complete"] is False


def test_trusted_ci_requires_actual_bool(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))
    br.record_retest(tid, ok=True)
    with pytest.raises(ReviewBridgeError, match="bool"):
        br.record_ci(tid, ok="false")
    assert br.status(tid)["allow_complete"] is False


def test_engine_contract_error_is_translated_to_bridge_error(tmp_path):
    br, tid, _opened = _open(tmp_path)
    with pytest.raises(ReviewBridgeError, match="finding"):
        br.resolve(tid, "R-XRB-999", fix_sha="abc1234")
    with pytest.raises(ReviewBridgeError, match="finding"):
        br.verify_finding(tid, "R-XRB-999")


def test_cli_unknown_finding_is_bounded_json_without_traceback(tmp_path):
    repo = _mkrepo(tmp_path)
    br = ReviewBridge(repo)
    tid = "CLI-ERR-" + uuid.uuid4().hex[:10]
    br.open(tid, ["t"])
    p = _cli("resolve", "--task", tid, "--finding", "R-XRB-999", "--fix-sha", "abc1234", repo=repo)
    assert p.returncode == 1
    data = json.loads(p.stdout)
    assert data["ok"] is False
    assert "finding" in data["error"]
    assert "Traceback" not in p.stdout and "Traceback" not in p.stderr


# --- GPT adversarial rereview REDs: durable task-map identity boundary ---

def test_corrupt_task_map_fails_as_bounded_bridge_error(tmp_path):
    br, tid, _opened = _open(tmp_path)
    br._map_path(tid).write_text("{broken", encoding="utf-8")
    with pytest.raises(ReviewBridgeError, match="map"):
        br.status(tid)


def test_task_map_cannot_be_substituted_across_task_ids(tmp_path):
    br = _bridge(tmp_path)
    a = _tid()
    b = _tid()
    br.open(a, ["a"])
    br.open(b, ["b"])
    br._map_path(a).write_bytes(br._map_path(b).read_bytes())
    with pytest.raises(ReviewBridgeError, match="task"):
        br.status(a)


def test_cli_corrupt_task_map_is_bounded_json_without_traceback(tmp_path):
    repo = _mkrepo(tmp_path)
    tid = "CLI-MAP-" + uuid.uuid4().hex[:10]
    path = repo / ".tmp" / "review-bridge" / f"task-{tid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")
    try:
        p = _cli("status", "--task", tid, repo=repo)
        assert p.returncode == 1
        data = json.loads(p.stdout)
        assert data["ok"] is False and "map" in data["error"]
        assert "Traceback" not in p.stdout and "Traceback" not in p.stderr
    finally:
        path.unlink(missing_ok=True)


# --- GPT adversarial rereview REDs: map โ” ReviewBus binding ---

def test_task_map_cycle_must_belong_to_same_bridge_task(tmp_path):
    br = _bridge(tmp_path)
    a = _tid()
    b = _tid()
    br.open(a, ["a"])
    br.open(b, ["b"])
    ma = json.loads(br._map_path(a).read_text(encoding="utf-8"))
    mb = json.loads(br._map_path(b).read_text(encoding="utf-8"))
    ma["cycle"] = mb["cycle"]
    ma["head_sha"] = mb["head_sha"]
    br._map_path(a).write_text(json.dumps(ma), encoding="utf-8")
    with pytest.raises(ReviewBridgeError, match="cycle|identity|task"):
        br.status(a)


def test_task_map_head_must_match_review_bus_head(tmp_path):
    br, tid, _opened = _open(tmp_path)
    m = json.loads(br._map_path(tid).read_text(encoding="utf-8"))
    m["head_sha"] = "0" * 40
    br._map_path(tid).write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ReviewBridgeError, match="head"):
        br.status(tid)


def test_record_retest_new_sha_keeps_task_map_head_in_sync(tmp_path):
    br, tid, opened = _open(tmp_path)
    new_sha = _commit_new_head(br._root, "map-sync.txt")
    br.record_retest(tid, ok=True, sha=new_sha)
    st = br.status(tid)
    persisted = json.loads(br._map_path(tid).read_text(encoding="utf-8"))
    assert st["head_sha"] == new_sha
    assert persisted["head_sha"] == new_sha


# --- GPT adversarial rereview REDs: original RB-A1..A7 blockers ---

def _commit_new_head(repo: Path, name: str = "probe.txt") -> str:
    target = repo / name
    target.write_text(uuid.uuid4().hex + "\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", name], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "probe head advance"],
        check=True, capture_output=True, text=True,
    )
    return _head(repo)


def test_stale_result_rejected_after_actual_git_head_advances(tmp_path):
    br, tid, opened = _open(tmp_path)
    _commit_new_head(br._root)
    with pytest.raises(ReviewBridgeError, match="head|stale"):
        br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))


def test_ready_not_usable_after_actual_git_head_advances(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))
    br.record_retest(tid, ok=True)
    br.record_ci(tid, ok=True)
    assert br.status(tid)["allow_complete"] is True
    _commit_new_head(br._root, "advance.txt")
    assert br.status(tid)["allow_complete"] is False


def test_dirty_worktree_cannot_reach_or_keep_ready(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))
    br.record_retest(tid, ok=True)
    (br._root / "dirty.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(ReviewBridgeError, match="dirty"):
        br.record_ci(tid, ok=True)
    assert br.status(tid)["allow_complete"] is False


def test_repeated_open_cannot_hide_existing_blocker(tmp_path):
    br, tid, opened = _open(tmp_path)
    br.ingest(tid, _result(
        tid, opened["head_sha"], verdict="CHANGES_REQUIRED",
        findings=[{"severity": "P1", "area": "trust", "summary": "block"}],
    ))
    _commit_new_head(br._root, "fix.txt")
    with pytest.raises(ReviewBridgeError, match="block|review|cycle"):
        br.open(tid, ["retest"])


def test_pinned_reviewer_identity_is_enforced(tmp_path):
    br = _bridge(tmp_path)
    tid = _tid()
    opened = br.open(tid, ["t"], reviewer="glm-5.3")
    with pytest.raises(ReviewBridgeError, match="reviewer|model|identity"):
        br.ingest(tid, _result(
            tid, opened["head_sha"], verdict="PASS", findings=[], model="other-model",
        ))
    with pytest.raises(ReviewBridgeError, match="reviewer|model|identity"):
        br.ingest(tid, _result(
            tid, opened["head_sha"], verdict="PASS", findings=[],
            model="glm-5.3", reviewer="other-model",
        ))


def test_ingest_replay_after_partial_bus_mutation_does_not_duplicate(tmp_path, monkeypatch):
    br, tid, opened = _open(tmp_path)
    result = _result(
        tid, opened["head_sha"], verdict="CHANGES_REQUIRED",
        findings=[
            {"severity": "P2", "area": "a", "summary": "one"},
            {"severity": "P2", "area": "b", "summary": "two"},
        ],
    )
    original = br.bus.add_finding
    calls = {"n": 0}

    def crash_after_first_add(**kwargs):
        finding = original(**kwargs)
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated crash after ReviewBus mutation")
        return finding
    monkeypatch.setattr(br.bus, "add_finding", crash_after_first_add)
    with pytest.raises(RuntimeError, match="simulated crash"):
        br.ingest(tid, result)
    monkeypatch.setattr(br.bus, "add_finding", original)

    replay = br.ingest(tid, result)
    doc = br.bus.load(opened["cycle"])
    assert len(doc["findings"]) == 2
    assert [f["summary"] for f in doc["findings"]] == ["one", "two"]
    assert replay["duplicate"] is True


def test_atomic_map_save_preserves_previous_bytes_on_write_failure(tmp_path, monkeypatch):
    br, tid, _opened = _open(tmp_path)
    path = br._map_path(tid)
    before = path.read_bytes()
    original_write_text = Path.write_text

    def fail_after_partial_write(self, data, *args, **kwargs):
        self.write_bytes(b"{broken")
        raise OSError("simulated partial write")

    monkeypatch.setattr(Path, "write_text", fail_after_partial_write)
    with pytest.raises(OSError, match="partial write"):
        br._save_map(tid, {"task_id": tid, "cycle": "XRB-c999", "head_sha": "0" * 40, "ingest": None})
    monkeypatch.setattr(Path, "write_text", original_write_text)
    assert path.read_bytes() == before


def test_pinned_reviewer_rejects_missing_identity(tmp_path):
    br = _bridge(tmp_path)
    tid = _tid()
    opened = br.open(tid, ["t"], reviewer="glm-5.3")
    with pytest.raises(ReviewBridgeError, match="reviewer|model|identity"):
        br.ingest(tid, _result(tid, opened["head_sha"], verdict="PASS", findings=[]))


def test_cli_oversized_result_rejected_before_whole_file_read(tmp_path, monkeypatch, capsys):
    from conductor import cli as conductor_cli

    result_file = tmp_path / "oversized-result.json"
    result_file.write_bytes(b"x" * (64_000 + 1))
    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if self == result_file:
            raise AssertionError("whole-file-read")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    rc = conductor_cli.main([
        "review", "ingest", "--task", "oversized-probe",
        "--file", str(result_file), "--json",
    ])
    captured = capsys.readouterr()
    assert rc == 1
    assert "size" in captured.out.lower() or "large" in captured.out.lower()
    assert "whole-file-read" not in captured.out + captured.err


# --- Cross-repo target worktree seam (post-main follow-up) ---

def _mk_target_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()

    def g(*args: str) -> str:
        p = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30,
        )
        assert p.returncode == 0, p.stderr
        return p.stdout

    g("init")
    g("config", "user.email", "target-test@example.com")
    g("config", "user.name", "target-test")
    (repo / "README.md").write_text(f"{name}\n", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "init")
    return repo

def test_external_target_open_binds_target_head_and_keeps_state_outside_target(tmp_path):
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-a")
    before = _git_status(target)

    br = ReviewBridge(authority, target_repo_root=target)
    out = br.open(_tid(), ["python -m pytest -q"])

    assert out["head_sha"] == _head(target)
    assert br._root == target.resolve()
    assert _is_within(br.bus.dir, authority.resolve())
    assert not _is_within(br.bus.dir, target.resolve())
    assert _git_status(target) == before == ""


def test_external_target_dirty_state_fails_closed_even_when_authority_clean(tmp_path):
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-dirty")
    (target / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    br = ReviewBridge(authority, target_repo_root=target)

    with pytest.raises(ReviewBridgeError, match="clean|dirty"):
        br.open(_tid(), ["t"])

def _git_status(repo: Path) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def test_external_target_state_is_namespaced_and_cannot_cross_task_repo(tmp_path):
    authority = _mkrepo(tmp_path)
    target_a = _mk_target_repo(tmp_path, "target-one")
    target_b = _mk_target_repo(tmp_path, "target-two")
    task = "XREPO-SAME-TASK"

    a = ReviewBridge(authority, target_repo_root=target_a)
    b = ReviewBridge(authority, target_repo_root=target_b)
    opened = a.open(task, ["a"])

    assert a.bus.dir != b.bus.dir
    assert a.status(task)["cycle"] == opened["cycle"]
    assert b.status(task)["status"] == "NO_REVIEW"

def test_external_target_head_advance_revokes_ready(tmp_path):
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-head")
    br = ReviewBridge(authority, target_repo_root=target)
    task = _tid()
    opened = br.open(task, ["t"])
    br.ingest(task, _result(task, opened["head_sha"], verdict="PASS", findings=[]))
    br.record_retest(task, ok=True)
    br.record_ci(task, ok=True)
    assert br.status(task)["allow_complete"] is True

    _commit_new_head(target, "advance-target.txt")
    assert br.status(task)["allow_complete"] is False


@pytest.mark.parametrize("bad_kind", ["relative", "missing", "not-git"])
def test_external_target_invalid_root_fails_closed(tmp_path, bad_kind):
    authority = _mkrepo(tmp_path)
    if bad_kind == "relative":
        target = Path("relative-target")
    elif bad_kind == "missing":
        target = (tmp_path / "missing-target").resolve()
    else:
        target = (tmp_path / "plain-dir").resolve()
        target.mkdir()

    with pytest.raises(ReviewBridgeError, match="target|repo|absolute|git"):
        br = ReviewBridge(authority, target_repo_root=target)
        br.status(_tid())

def _cli_authority_target(authority: Path, target: Path, *args: str):
    code = (
        "import sys; from pathlib import Path; import conductor.cli as c; "
        "c.REPO_ROOT=Path(sys.argv[1]); "
        "raise SystemExit(c.main(sys.argv[2:]))"
    )
    command = [
        sys.executable, "-c", code, str(authority),
        "review", *args, "--target-repo", str(target), "--json",
    ]
    return subprocess.run(
        command, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), timeout=120,
    )


def test_cli_external_target_full_lifecycle_uses_target_head(tmp_path):
    parent = tmp_path / "authority-parent"
    parent.mkdir()
    authority = _mkrepo(parent)
    target = _mk_target_repo(tmp_path, "cli-target")
    task = "CLI-XREPO-" + uuid.uuid4().hex[:8]

    opened_p = _cli_authority_target(
        authority, target, "open", "--task", task, "--tests", "t")
    assert opened_p.returncode == 0, opened_p.stdout + opened_p.stderr
    opened = json.loads(opened_p.stdout)
    assert opened["head_sha"] == _head(target)

    result_file = tmp_path / "external-review-result.json"
    result_file.write_text(json.dumps(_result(
        task, opened["head_sha"], verdict="PASS", findings=[])), encoding="utf-8")
    ingest = _cli_authority_target(
        authority, target, "ingest", "--task", task, "--file", str(result_file))
    assert ingest.returncode == 0, ingest.stdout + ingest.stderr
    assert json.loads(ingest.stdout)["verdict"] == "PASS"

    retest = _cli_authority_target(
        authority, target, "record-retest", "--task", task, "--ok", "true")
    assert retest.returncode == 0, retest.stdout + retest.stderr
    ci = _cli_authority_target(
        authority, target, "record-ci", "--task", task, "--ok", "true")
    assert ci.returncode == 0, ci.stdout + ci.stderr
    status = _cli_authority_target(authority, target, "status", "--task", task)
    data = json.loads(status.stdout)
    assert status.returncode == 0
    assert data["allow_complete"] is True and data["status"] == "READY"
    assert _git_status(target) == ""


def test_cli_external_target_invalid_path_is_bounded_json(tmp_path):
    parent = tmp_path / "authority-parent"
    parent.mkdir()
    authority = _mkrepo(parent)
    missing = (tmp_path / "missing-target").resolve()
    p = _cli_authority_target(authority, missing, "status", "--task", "CLI-XREPO-MISSING")
    assert p.returncode == 1
    data = json.loads(p.stdout)
    assert data["ok"] is False
    assert "Traceback" not in p.stdout + p.stderr


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


# --- TR-R1 / TR-R2 repairs (GPT primary review CHANGES_REQUIRED) ---

def test_external_target_rejects_state_dir_override_before_any_creation(tmp_path):
    """TR-R1: external-target mode + custom state_dir is a trust-boundary
    escape (state could be steered into the target or outside the
    authority). It must fail closed BEFORE creating anything."""
    import os as _os
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-r1")
    rogue = target / ".review-state"
    before = _git_status(target)
    assert before == ""

    with pytest.raises(ReviewBridgeError, match="state"):
        ReviewBridge(authority, state_dir=rogue, target_repo_root=target)

    assert not rogue.exists(), "state directory was created inside target"
    assert _git_status(target) == ""
    # nothing else appeared in the target either
    assert not (target / ".tmp").exists()
    # default external-target state still lives under the authority
    br = ReviewBridge(authority, target_repo_root=target)
    assert _is_within(br.bus.dir, authority.resolve())
    assert not _is_within(br.bus.dir, target.resolve())
    assert _os.name == _os.name  # keep import used on all platforms


def test_external_target_state_dir_outside_authority_also_rejected(tmp_path):
    """TR-R1 (breadth): ANY state_dir override in external-target mode is
    rejected — including paths outside both repos."""
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-r1b")
    elsewhere = tmp_path / "elsewhere-state"
    with pytest.raises(ReviewBridgeError, match="state"):
        ReviewBridge(authority, state_dir=elsewhere, target_repo_root=target)
    assert not elsewhere.exists()


def test_omitted_target_state_dir_override_still_supported(tmp_path):
    """TR-R1 guard must NOT weaken historical behavior: with the target
    omitted, explicit state_dir keeps working exactly as before."""
    authority = _mkrepo(tmp_path)
    custom = tmp_path / "custom-state"
    br = ReviewBridge(authority, state_dir=custom)
    out = br.open(_tid(), ["t"])
    assert br.bus.dir == custom
    assert br.status(out["task_id"])["cycle"] == out["cycle"]


def test_target_namespace_is_full_hash_without_raw_path(tmp_path):
    """TR-R2: the namespace segment is the full sha256 fingerprint — never
    a raw machine path, never a lossy truncation."""
    import re as _re
    from conductor.review_bridge import _target_state_namespace
    authority = _mkrepo(tmp_path)
    target = _mk_target_repo(tmp_path, "target-ns")
    ns = _target_state_namespace(authority, target)
    assert _is_within(ns, authority.resolve())
    segment = ns.name
    assert _re.fullmatch(r"[0-9a-f]{64}", segment), segment


def test_target_namespace_never_collapses_distinct_case_paths_by_os_name(tmp_path):
    """TR-R3: OS family is not filesystem semantics.

    Windows can host per-directory case-sensitive trees. Distinct resolved path
    spellings must never collapse merely because the host OS is Windows.
    """
    from conductor.review_bridge import _target_state_namespace

    authority = _mkrepo(tmp_path)
    upper = Path("C:/repos/RepoA")
    lower = Path("C:/repos/repoa")
    assert _target_state_namespace(authority, upper) != \
        _target_state_namespace(authority, lower)


def test_target_namespace_case_safety_is_os_family_agnostic(tmp_path):
    """TR-R3: false separation is allowed; cross-target collision is not."""
    from conductor.review_bridge import _target_state_namespace

    authority = _mkrepo(tmp_path)
    upper = Path("/srv/repos/RepoA")
    lower = Path("/srv/repos/repoa")
    assert _target_state_namespace(authority, upper) != \
        _target_state_namespace(authority, lower)
