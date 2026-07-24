"""Tests for scripts/lib/goal_store.py — thin wrapper over task_board for goals.

Iron Law #1: failing tests written FIRST.

goal_store คือ wrapper บางๆ บน task_board ที่ทำ goal lifecycle:
  - create_goal(objective) → returns goal_id (G...)
  - add_subtask(goal_id, goal, files) → task ใต้ goal (parent_goal_id)
  - get_goal(goal_id) → goal + subtasks (aggregate view)
  - list_goals() → เฉพาะ goals (กรอง tasks ที่มี parent)
  - goal_progress(goal_id) → {total, done, doing, todo, blocked} %
  - update_goal(goal_id, status) → mark goal done/blocked

ไม่สร้าง data structure ใหม่ — ใช้ task_board ที่มี + ใช้ parent_goal_id
เพื่อแยก "goal" (top-level) จาก "task" (มี parent).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import goal_store as gs  # noqa: E402 -- module under test (created here)
import task_board as tb  # noqa: E402 -- dependency (chunk 5 of Neural Spine)


# ---------------------------------------------------------------------------
# 1. create_goal — writes a top-level goal task with id prefix G...
# ---------------------------------------------------------------------------
def test_create_goal_returns_goal_id(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="ship feature X")
    assert goal_id.startswith("G"), f"goal id must start with G, got {goal_id}"
    # verify it's on the board as a task
    board = tb.TaskBoard(tmp_path / "tasks.json")
    t = board.get(goal_id)
    assert t is not None
    assert t["goal"] == "ship feature X"
    assert t["parent_goal_id"] is None  # top-level = no parent
    assert t["status"] == "todo"


def test_create_goal_assigns_unique_ids(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    g1 = store.create_goal(objective="goal 1")
    g2 = store.create_goal(objective="goal 2")
    assert g1 != g2


# ---------------------------------------------------------------------------
# 2. add_subtask — creates a task under a goal (parent_goal_id set)
# ---------------------------------------------------------------------------
def test_add_subtask_links_to_parent(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="refactor module")
    sub_id = store.add_subtask(goal_id, goal="extract helper function", files=["scripts/x.py"])
    assert sub_id.startswith("T")  # subtasks use task prefix T
    board = tb.TaskBoard(tmp_path / "tasks.json")
    t = board.get(sub_id)
    assert t["parent_goal_id"] == goal_id
    assert t["files"] == ["scripts/x.py"]


# ---------------------------------------------------------------------------
# 3. get_goal — returns goal + its subtasks (aggregate view)
# ---------------------------------------------------------------------------
def test_get_goal_returns_goal_and_subtasks(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="multi-step goal")
    store.add_subtask(goal_id, goal="step 1")
    store.add_subtask(goal_id, goal="step 2")
    view = store.get_goal(goal_id)
    assert view["goal"]["id"] == goal_id
    assert view["goal"]["objective"] == "multi-step goal"
    assert len(view["subtasks"]) == 2
    assert all(s["parent_goal_id"] == goal_id for s in view["subtasks"])


def test_get_goal_returns_none_for_missing(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    assert store.get_goal("GDOESNOTEXIST") is None


# ---------------------------------------------------------------------------
# 4. list_goals — only top-level goals (tasks WITHOUT parent_goal_id)
# ---------------------------------------------------------------------------
def test_list_goals_excludes_subtasks(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    g1 = store.create_goal(objective="goal A")
    g2 = store.create_goal(objective="goal B")
    store.add_subtask(g1, goal="subtask of A")
    store.add_subtask(g1, goal="another subtask of A")
    goals = store.list_goals()
    assert len(goals) == 2  # only top-level, not subtasks
    ids = {g["id"] for g in goals}
    assert g1 in ids and g2 in ids


def test_list_goals_empty_when_no_goals(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    assert store.list_goals() == []


# ---------------------------------------------------------------------------
# 5. goal_progress — aggregate status counts
# ---------------------------------------------------------------------------
def test_goal_progress_counts_subtask_statuses(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="trackable goal")
    s1 = store.add_subtask(goal_id, goal="done task")
    s2 = store.add_subtask(goal_id, goal="todo task")
    s3 = store.add_subtask(goal_id, goal="doing task")
    board = tb.TaskBoard(tmp_path / "tasks.json")
    board.update(s1, status="done")
    board.update(s3, status="doing")
    prog = store.goal_progress(goal_id)
    assert prog["total"] == 3
    assert prog["done"] == 1
    assert prog["doing"] == 1
    assert prog["todo"] == 1
    assert prog["blocked"] == 0
    # percent done (excluding the goal itself)
    assert prog["percent_done"] == pytest.approx(33.33, abs=0.1)


def test_goal_progress_zero_when_no_subtasks(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="empty goal")
    prog = store.goal_progress(goal_id)
    assert prog["total"] == 0
    assert prog["percent_done"] == 0


# ---------------------------------------------------------------------------
# 6. update_goal — mark goal status (done/blocked)
# ---------------------------------------------------------------------------
def test_update_goal_changes_status(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="finishable goal")
    ok = store.update_goal(goal_id, status="done")
    assert ok is True
    view = store.get_goal(goal_id)
    assert view["goal"]["status"] == "done"


def test_update_goal_rejects_invalid_status(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="x")
    with pytest.raises(ValueError):
        store.update_goal(goal_id, status="garbage")


# ---------------------------------------------------------------------------
# 7. persistence — survives GoalStore recreation (cross-session resume)
# ---------------------------------------------------------------------------
def test_goal_store_survives_recreation(tmp_path):
    """Critical for A-Loop: session A creates goal → compact → session B resumes."""
    f = tmp_path / "tasks.json"
    store_a = gs.GoalStore(f)
    goal_id = store_a.create_goal(objective="cross-session goal")
    store_a.add_subtask(goal_id, goal="step 1")

    store_b = gs.GoalStore(f)  # new instance = new session
    goals = store_b.list_goals()
    assert len(goals) == 1
    assert goals[0]["id"] == goal_id
    view = store_b.get_goal(goal_id)
    assert len(view["subtasks"]) == 1


# ---------------------------------------------------------------------------
# 8. next_todo — find next subtask to work on (the loop driver)
# ---------------------------------------------------------------------------
def test_next_todo_returns_first_undone_subtask(tmp_path):
    """A-Loop Phase 2 needs: 'what's the next task to claim?'"""
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="sequential goal")
    s1 = store.add_subtask(goal_id, goal="first")
    s2 = store.add_subtask(goal_id, goal="second")
    s3 = store.add_subtask(goal_id, goal="third")
    board = tb.TaskBoard(tmp_path / "tasks.json")
    board.update(s1, status="done")  # first done
    nxt = store.next_todo(goal_id)
    assert nxt is not None
    assert nxt["id"] == s2  # second is next


def test_next_todo_returns_none_when_all_done(tmp_path):
    store = gs.GoalStore(tmp_path / "tasks.json")
    goal_id = store.create_goal(objective="completed goal")
    s1 = store.add_subtask(goal_id, goal="only task")
    board = tb.TaskBoard(tmp_path / "tasks.json")
    board.update(s1, status="done")
    assert store.next_todo(goal_id) is None
