"""Tests for scripts/lib/task_board.py — atomic task claim/release/update.

Iron Law #1: failing tests written FIRST.

Task Board คือตัวกันชนกันของสมอง A-Wiki. ป้องกัน 2 agents claim task
เดียวกันพร้อมกัน (เราเคยเจอ: session_start.py มี <<<<< HEAD markers).

Schema (.tmp/task-board.json):
  {
    "tasks": [
      {
        "id": "T1",
        "goal": "refactor X",
        "status": "todo|claimed|doing|done|blocked",
        "claimant": "claude" | null,
        "claim_ts": float | null,
        "lease_ttl": int,        # seconds
        "files": ["..."],
        "parent_goal_id": "G1" | null,
        "notes": ["..."]
      }
    ]
  }

Core invariant: claim() is atomic — exactly one agent wins, others lose.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import task_board as tb  # noqa: E402 -- module under test (created by this chunk)


def _seed_board(tmp_path: Path) -> tuple[tb.TaskBoard, str, str]:
    """Create a board with 2 tasks. Returns (board, task1_id, task2_id).

    IDs are returned by add() (not hardcoded) because the board generates
    random unique ids — tests must use the real ids, not 'T1'/'T2'.
    """
    board = tb.TaskBoard(tmp_path / "tasks.json")
    id_a = board.add(goal="task A", files=["scripts/a.py"])
    id_b = board.add(goal="task B", files=["scripts/b.py"])
    # Stash ids as attributes for backward-compat with tests written before
    # this refactor — they can read board._seed_ids if they need them.
    board._seed_ids = (id_a, id_b)
    return board, id_a, id_b


# ---------------------------------------------------------------------------
# 1. add — creates a task in 'todo' status
# ---------------------------------------------------------------------------
def test_add_creates_todo_task(tmp_path):
    board = tb.TaskBoard(tmp_path / "tasks.json")
    task_id = board.add(goal="refactor X", files=["scripts/x.py"])
    assert task_id is not None
    tasks = board.list()
    assert len(tasks) == 1
    t = tasks[0]
    assert t["goal"] == "refactor X"
    assert t["status"] == "todo"
    assert t["claimant"] is None
    assert t["files"] == ["scripts/x.py"]
    assert t["id"] == task_id


def test_add_assigns_unique_ids(tmp_path):
    board = tb.TaskBoard(tmp_path / "tasks.json")
    id1 = board.add(goal="A")
    id2 = board.add(goal="B")
    assert id1 != id2


# ---------------------------------------------------------------------------
# 2. claim — atomic, only one agent wins
# ---------------------------------------------------------------------------
def test_claim_succeeds_for_free_task(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    won = board.claim(t1_id, claimant="claude", lease_minutes=30)
    assert won is True
    t1 = board.get(t1_id)
    assert t1["status"] == "claimed"
    assert t1["claimant"] == "claude"
    assert t1["claim_ts"] is not None
    assert t1["lease_ttl"] == 30 * 60


def test_claim_fails_if_already_claimed(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude", lease_minutes=30)
    # Second agent tries to claim the same task
    won = board.claim(t1_id, claimant="codex", lease_minutes=30)
    assert won is False, "second claim must fail — task already claimed"
    t1 = board.get(t1_id)
    assert t1["claimant"] == "claude", "claimant must remain the first winner"


def test_claim_fails_for_done_task(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude")
    board.update(t1_id, status="done")
    won = board.claim(t1_id, claimant="codex")
    assert won is False


# ---------------------------------------------------------------------------
# 3. claim — concurrent claims, exactly one wins (THE race-condition test)
# ---------------------------------------------------------------------------
def test_concurrent_claims_exactly_one_wins(tmp_path):
    """20 agents try to claim the same task simultaneously → 1 wins, 19 lose."""
    board = tb.TaskBoard(tmp_path / "tasks.json")
    task_id = board.add(goal="contended task")
    N = 20
    barrier = threading.Barrier(N)
    winners: list[str] = []
    winners_lock = threading.Lock()

    def try_claim(agent_id):
        barrier.wait()
        won = board.claim(task_id, claimant=f"agent-{agent_id}", lease_minutes=5)
        if won:
            with winners_lock:
                winners.append(f"agent-{agent_id}")

    threads = [threading.Thread(target=try_claim, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(winners) == 1, (
        f"exactly 1 agent must win the claim, got {len(winners)}: {winners} — "
        f"locking is broken; race condition allowed multiple claims"
    )


# ---------------------------------------------------------------------------
# 4. release — returns task to 'todo'
# ---------------------------------------------------------------------------
def test_release_returns_task_to_todo(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude")
    released = board.release(t1_id)
    assert released is True
    t1 = board.get(t1_id)
    assert t1["status"] == "todo"
    assert t1["claimant"] is None
    assert t1["claim_ts"] is None


def test_release_fails_for_unclaimed_task(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    released = board.release(t1_id)  # never claimed
    assert released is False


# ---------------------------------------------------------------------------
# 5. update — change status + add note
# ---------------------------------------------------------------------------
def test_update_changes_status(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude")
    updated = board.update(t1_id, status="doing", note="started implementation")
    assert updated is True
    t1 = board.get(t1_id)
    assert t1["status"] == "doing"
    assert "started implementation" in t1["notes"]


def test_update_rejects_invalid_status(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    with pytest.raises(ValueError):
        board.update(t1_id, status="garbage")


# ---------------------------------------------------------------------------
# 6. TTL lease expiry — reaper releases expired claims (chunk 6 will use this)
# ---------------------------------------------------------------------------
def test_is_expired_detects_old_claim(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    # claim with 0-minute lease → immediately expired
    board.claim(t1_id, claimant="claude", lease_minutes=0)
    t1 = board.get(t1_id)
    assert board.is_expired(t1) is True


def test_is_expired_false_for_fresh_claim(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude", lease_minutes=30)
    t1 = board.get(t1_id)
    assert board.is_expired(t1) is False


# ---------------------------------------------------------------------------
# 7. list — filtering by status
# ---------------------------------------------------------------------------
def test_list_filters_by_status(tmp_path):
    board, t1_id, t2_id = _seed_board(tmp_path)
    board.claim(t1_id, claimant="claude")
    board.update(t2_id, status="done")
    todo_tasks = board.list(status="todo")
    assert len(todo_tasks) == 0
    claimed = board.list(status="claimed")
    assert len(claimed) == 1
    assert claimed[0]["id"] == t1_id


# ---------------------------------------------------------------------------
# 8. persistence — survives TaskBoard recreation (cross-session)
# ---------------------------------------------------------------------------
def test_task_board_survives_recreation(tmp_path):
    """agent A creates+claims → agent B (new instance) sees the state."""
    f = tmp_path / "tasks.json"
    board_a = tb.TaskBoard(f)
    task_id = board_a.add(goal="cross-session task")
    board_a.claim(task_id, claimant="claude")

    board_b = tb.TaskBoard(f)
    tasks = board_b.list()
    assert len(tasks) == 1
    assert tasks[0]["claimant"] == "claude"
    assert tasks[0]["status"] == "claimed"


# ---------------------------------------------------------------------------
# 9. get — single task lookup
# ---------------------------------------------------------------------------
def test_get_returns_task_by_id(tmp_path):
    board, t1_id, _ = _seed_board(tmp_path)
    t = board.get(t1_id)
    assert t is not None
    assert t["goal"] == "task A"


def test_get_returns_none_for_missing(tmp_path):
    board, _, _ = _seed_board(tmp_path)
    assert board.get("DOES_NOT_EXIST") is None
