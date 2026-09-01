"""A-Loop v2 — Phase 9: connect the A-Loop execute phase to the review-bus
state machine (review_bus.py, Phase 8).

Contract: a task may only be marked complete when its review cycle is
READY; CHANGES_REQUIRED pushes the loop back into fixing (with the
finding ids); a stale approval at an old SHA re-opens review — the loop
keeps cycling until everything aligns. This adapter reads git state via
pure file IO (no subprocess) and never mutates goal/task stores.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import review_bus as rb  # noqa: E402
from a_loop_review import ALoopReview  # noqa: E402


def _setup(tmp_path):
    bus = rb.ReviewBus(tmp_path / "review-bus", phase="P9")
    loop = ALoopReview(bus, git_dir=REPO_ROOT / ".git")
    return bus, loop


def test_open_review_binds_task_to_fresh_cycle_at_current_head(tmp_path):
    bus, loop = _setup(tmp_path)
    cid = loop.open_review_for_task("T-101", ["python -m pytest tests/ -q"])
    doc = bus.load(cid)
    assert doc["head_sha"] and len(doc["head_sha"]) >= 7
    assert doc["required_tests"] == ["python -m pytest tests/ -q"]
    assert (tmp_path / "review-bus" / "task-T-101.json").is_file()


def test_gate_pending_until_reviewed(tmp_path):
    bus, loop = _setup(tmp_path)
    loop.open_review_for_task("T-102", ["t"])
    g = loop.task_gate("T-102")
    assert g["allow_complete"] is False
    assert g["status"] == "REVIEW_REQUESTED"


def test_gate_blocks_with_blocker_ids_on_changes_required(tmp_path):
    bus, loop = _setup(tmp_path)
    loop.open_review_for_task("T-103", ["t"])
    bus.add_finding(severity="blocker", area="core", summary="race")
    bus.set_verdict(reviewer="r", verdict="CHANGES_REQUIRED")
    g = loop.task_gate("T-103")
    assert g["allow_complete"] is False
    assert g["status"] == "CHANGES_REQUIRED"
    assert "R-P9-001" in g["blockers"]


def test_gate_allows_when_cycle_ready(tmp_path):
    bus, loop = _setup(tmp_path)
    cid = loop.open_review_for_task("T-104", ["t"])
    head = bus.load(cid)["head_sha"]
    bus.add_finding(severity="note", area="docs", summary="t")
    bus.verify_finding("R-P9-001")
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha=head, ok=True)
    bus.record_ci(ok=True)
    g = loop.task_gate("T-104")
    assert g["allow_complete"] is True and g["status"] == "READY"


def test_stale_sha_reopens_review_so_loop_keeps_cycling(tmp_path):
    """Fix commit = NEW head: approval at the old head must not complete
    the task — the loop goes back around (Phase-9 loop semantics)."""
    bus, loop = _setup(tmp_path)
    cid = loop.open_review_for_task("T-105", ["t"])
    head = bus.load(cid)["head_sha"]
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha=head, ok=True)
    bus.record_ci(ok=True)
    assert loop.task_gate("T-105")["allow_complete"] is True
    # fix lands at a new head -> record_retest at the new sha
    new_head = "f" * 40
    bus.record_retest(sha=new_head, ok=True)
    g = loop.task_gate("T-105")
    assert g["allow_complete"] is False, "stale approval must reopen the loop"
    assert g["status"] == "REVIEW_REQUESTED"


def test_gate_unknown_task_is_explicit(tmp_path):
    _, loop = _setup(tmp_path)
    g = loop.task_gate("T-404")
    assert g["allow_complete"] is False
    assert g["status"] == "NO_REVIEW"


# ── RB-1: worktree-safe exact HEAD resolution ────────────────────────
def _mini_repo(tmp_path: Path):
    """Real one-commit repo; returns (repo_root, head_sha)."""
    r = tmp_path / "repo"
    r.mkdir()

    def git(*a):
        subprocess.run(["git", *a], cwd=r, check=True,
                       capture_output=True, timeout=30)

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (r / "f.txt").write_text("x", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "c1")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=r, check=True,
                         capture_output=True, text=True,
                         timeout=30).stdout.strip()
    return r, sha


def test_head_sha_resolves_in_normal_checkout(tmp_path):
    repo, sha = _mini_repo(tmp_path)
    bus = rb.ReviewBus(tmp_path / "bus", phase="RB")
    loop = ALoopReview(bus, git_dir=repo / ".git")
    assert loop.head_sha() == sha


def test_head_sha_resolves_in_linked_worktree_gitfile(tmp_path):
    """Linked worktree: .git is a gitfile POINTER, not a directory — the
    exact condition that broke head_sha() (WO RB-1 regression)."""
    repo, sha = _mini_repo(tmp_path)
    wt = tmp_path / "linked-wt"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt)],
                   check=True, capture_output=True, timeout=60)
    git_path = wt / ".git"
    assert git_path.is_file(), "linked worktree .git must be a gitfile"
    bus = rb.ReviewBus(tmp_path / "bus", phase="RB")
    loop = ALoopReview(bus, git_dir=git_path)
    assert loop.head_sha() == sha


def test_head_sha_supports_detached_head(tmp_path):
    repo, sha = _mini_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach"],
                   check=True, capture_output=True, timeout=30)
    bus = rb.ReviewBus(tmp_path / "bus2", phase="RB")
    loop = ALoopReview(bus, git_dir=repo / ".git")
    assert loop.head_sha() == sha


def test_head_sha_fails_explicitly_on_missing_git_dir(tmp_path):
    bus = rb.ReviewBus(tmp_path / "bus3", phase="RB")
    loop = ALoopReview(bus, git_dir=tmp_path / "nonexistent")
    with pytest.raises(rb.ReviewBusError):
        loop.head_sha()


def test_head_sha_fails_explicitly_on_invalid_gitfile(tmp_path):
    bad = tmp_path / "repo2"
    bad.mkdir()
    (bad / ".git").write_text("garbage without gitdir prefix",
                              encoding="utf-8")
    bus = rb.ReviewBus(tmp_path / "bus4", phase="RB")
    loop = ALoopReview(bus, git_dir=bad / ".git")
    with pytest.raises(rb.ReviewBusError):
        loop.head_sha()


def test_head_sha_never_falls_back_on_git_failure(tmp_path):
    """A directory that is not a git dir must raise, never return a
    guessed/stale SHA."""
    empty = tmp_path / "empty-git"
    empty.mkdir()
    bus = rb.ReviewBus(tmp_path / "bus5", phase="RB")
    loop = ALoopReview(bus, git_dir=empty)
    with pytest.raises(rb.ReviewBusError):
        loop.head_sha()
