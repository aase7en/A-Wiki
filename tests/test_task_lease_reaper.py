"""Tests for scripts/hooks/task_lease_reaper.py — release expired task claims.

Iron Law #1: failing tests written FIRST.

Reaper ทำงานเป็น periodic hook (SessionStart) เพื่อคืน task ที่ agent
claim ไว้แต่ crash ไปแล้ว กลับเป็น 'todo' ให้ agent อื่นรับต่อได้.

ไม่มี daemon — เรียกตอน SessionStart และเป็น best-effort (never blocks).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import task_board as tb  # noqa: E402
import task_lease_reaper as reaper  # noqa: E402 -- module under test (created here)


def _board_with_claim(tmp_path: Path, *, lease_minutes: int, age_seconds: float):
    """Create a board with one claimed task, optionally back-dated."""
    board = tb.TaskBoard(tmp_path / "tasks.json")
    task_id = board.add(goal="will be reaped", lease_minutes=lease_minutes)
    board.claim(task_id, claimant="doomed-agent", lease_minutes=lease_minutes)
    if age_seconds > 0:
        # Back-date the claim_ts to simulate elapsed time
        import json
        state = json.loads((tmp_path / "tasks.json").read_text(encoding="utf-8"))
        for t in state["tasks"]:
            if t["id"] == task_id:
                t["claim_ts"] = time.time() - age_seconds
        (tmp_path / "tasks.json").write_text(json.dumps(state), encoding="utf-8")
    return board, task_id


# ---------------------------------------------------------------------------
# 1. reap_expired_claims — releases tasks whose lease has expired
# ---------------------------------------------------------------------------
def test_reap_releases_expired_claim(tmp_path):
    board, task_id = _board_with_claim(tmp_path, lease_minutes=0, age_seconds=60)
    # Task is claimed + lease expired
    t = board.get(task_id)
    assert board.is_expired(t) is True
    # Reaper releases it
    reaped = reaper.reap_expired_claims(tmp_path / "tasks.json")
    assert reaped == 1
    t = board.get(task_id)
    assert t["status"] == "todo"
    assert t["claimant"] is None


def test_reap_keeps_fresh_claim(tmp_path):
    """A claim that's still within its lease must NOT be reaped."""
    board, task_id = _board_with_claim(tmp_path, lease_minutes=30, age_seconds=5)
    reaped = reaper.reap_expired_claims(tmp_path / "tasks.json")
    assert reaped == 0
    t = board.get(task_id)
    assert t["status"] == "claimed"
    assert t["claimant"] == "doomed-agent"


def test_reap_ignores_unclaimed_tasks(tmp_path):
    """Tasks in 'todo' status have no lease to expire — reaper leaves them."""
    board = tb.TaskBoard(tmp_path / "tasks.json")
    board.add(goal="free task")
    reaped = reaper.reap_expired_claims(tmp_path / "tasks.json")
    assert reaped == 0


def test_reap_multiple_expired_returns_count(tmp_path):
    """If 3 tasks are expired, reap returns 3 and releases all."""
    board = tb.TaskBoard(tmp_path / "tasks.json")
    for i in range(3):
        tid = board.add(goal=f"task-{i}", lease_minutes=0)
        board.claim(tid, claimant=f"agent-{i}", lease_minutes=0)
    import time as _t
    _t.sleep(0.01)  # ensure claim_ts is in the past relative to now
    reaped = reaper.reap_expired_claims(tmp_path / "tasks.json")
    assert reaped == 3


# ---------------------------------------------------------------------------
# 2. reap — handles missing/corrupt board gracefully
# ---------------------------------------------------------------------------
def test_reap_returns_zero_when_board_missing(tmp_path):
    """No task-board.json → nothing to reap. Don't crash."""
    reaped = reaper.reap_expired_claims(tmp_path / "nonexistent.json")
    assert reaped == 0


def test_reap_returns_zero_when_board_corrupt(tmp_path):
    """Corrupt JSON → log + return 0, don't crash."""
    f = tmp_path / "tasks.json"
    f.write_text("{ this is not valid json", encoding="utf-8")
    reaped = reaper.reap_expired_claims(f)
    assert reaped == 0


# ---------------------------------------------------------------------------
# 3. main — hook entry point, exits 0 (never blocks)
# ---------------------------------------------------------------------------
def test_main_exits_zero(monkeypatch, tmp_path):
    """Reaper is a SessionStart hook — must exit 0, never block session."""
    monkeypatch.setattr(reaper, "DEFAULT_BOARD_PATH", tmp_path / "tasks.json")
    assert reaper.main() == 0


def test_main_respects_hook_skip(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOOK_SKIP", "task_lease_reaper")
    monkeypatch.setattr(reaper, "DEFAULT_BOARD_PATH", tmp_path / "tasks.json")
    assert reaper.main() == 0
