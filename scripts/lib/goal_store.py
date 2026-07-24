"""goal_store.py — thin wrapper over task_board for A-Loop goal lifecycle.

Neural Spine Phase 2 / A-Loop Chunk 1.

ไม่สร้าง data structure ใหม่ — ใช้ task_board ที่มี (Neural Spine chunk 5).
แยก "goal" (top-level task, parent_goal_id=None, id prefix G) จาก "subtask"
(task ที่มี parent_goal_id, id prefix T). เพราะ task_board.add() ใช้ prefix
T เหมือนกันทั้งคู่ เราแค่ override id prefix ตอนสร้าง goal.

API:
  GoalStore(path).create_goal(objective) → goal_id (G...)
  .add_subtask(goal_id, goal, files)     → task_id (T...)
  .get_goal(goal_id)                     → {goal, subtasks}
  .list_goals()                          → [goal dicts] (top-level only)
  .goal_progress(goal_id)                → {total, done, doing, todo, blocked, percent_done}
  .update_goal(goal_id, status)          → bool
  .next_todo(goal_id)                    → task dict | None (first undone subtask)

Cross-session: ทุก state อยู่ใน task_board.json → survives compact + restart.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_board  # noqa: E402 -- Neural Spine chunk 5

VALID_GOAL_STATUSES = {"todo", "claimed", "doing", "done", "blocked"}


class GoalStore:
    """Goal lifecycle on top of TaskBoard. Goals = top-level tasks (no parent)."""

    def __init__(self, path: Path | str):
        self.board = task_board.TaskBoard(path)
        self.path = self.board.path

    def create_goal(self, *, objective: str, files: list[str] | None = None) -> str:
        """Create a top-level goal. Returns goal id (G...).

        A goal is just a task with parent_goal_id=None and id prefix G (so
        list_goals can filter it from subtasks cheaply).
        """
        goal_id = f"G{uuid.uuid4().hex[:6].upper()}"
        # We can't use board.add() because it forces T prefix; inject directly
        # via the same atomic_update pattern.
        import atomic_json
        import time

        def mutate(state: dict) -> str:
            state.setdefault("tasks", []).append({
                "id": goal_id,
                "goal": objective,
                "status": "todo",
                "claimant": None,
                "claim_ts": None,
                "lease_ttl": 0,  # goals aren't claimable; subtasks are
                "files": list(files) if files else [],
                "parent_goal_id": None,  # marks this as a top-level goal
                "notes": [],
                "created_ts": time.time(),
                "is_goal": True,  # explicit marker (belt + suspenders)
            })
            return goal_id

        return atomic_json.atomic_update(
            self.path, mutate, missing_default=self.board._empty_state()
        )

    def add_subtask(
        self,
        goal_id: str,
        *,
        goal: str,
        files: list[str] | None = None,
        lease_minutes: int = 30,
    ) -> str:
        """Add a subtask under a goal. Returns task id (T...)."""
        return self.board.add(
            goal=goal,
            files=files,
            parent_goal_id=goal_id,
            lease_minutes=lease_minutes,
        )

    def get_goal(self, goal_id: str) -> dict | None:
        """Return {goal, subtasks} aggregate view, or None if goal missing."""
        all_tasks = self.board.list()
        goal_task = next((t for t in all_tasks if t["id"] == goal_id), None)
        if goal_task is None:
            return None
        subtasks = [t for t in all_tasks if t.get("parent_goal_id") == goal_id]
        return {
            "goal": {**goal_task, "objective": goal_task["goal"]},
            "subtasks": subtasks,
        }

    def list_goals(self) -> list[dict]:
        """List only top-level goals (parent_goal_id is None).

        Identifies goals by: parent_goal_id is None AND id starts with 'G'.
        The id-prefix check is the cheap filter; parent check is the semantic one.
        """
        all_tasks = self.board.list()
        return [
            t for t in all_tasks
            if t.get("parent_goal_id") is None
            and (t["id"].startswith("G") or t.get("is_goal") is True)
        ]

    def goal_progress(self, goal_id: str) -> dict:
        """Return {total, done, doing, todo, blocked, percent_done} for a goal.

        Counts subtasks only (not the goal itself).
        """
        view = self.get_goal(goal_id)
        if view is None:
            return {"total": 0, "done": 0, "doing": 0, "todo": 0,
                    "blocked": 0, "percent_done": 0}
        subtasks = view["subtasks"]
        total = len(subtasks)
        if total == 0:
            return {"total": 0, "done": 0, "doing": 0, "todo": 0,
                    "blocked": 0, "percent_done": 0}
        counts = {"done": 0, "doing": 0, "todo": 0, "blocked": 0, "claimed": 0}
        for s in subtasks:
            st = s.get("status", "todo")
            if st in counts:
                counts[st] += 1
            else:
                counts["todo"] += 1
        # claimed counts as todo (not started executing yet)
        effective_todo = counts["todo"] + counts["claimed"]
        done = counts["done"]
        pct = round(100.0 * done / total, 1) if total else 0
        return {
            "total": total,
            "done": done,
            "doing": counts["doing"],
            "todo": effective_todo,
            "blocked": counts["blocked"],
            "percent_done": pct,
        }

    def update_goal(self, goal_id: str, *, status: str) -> bool:
        """Change a goal's status (done/blocked/etc)."""
        if status not in VALID_GOAL_STATUSES:
            raise ValueError(
                f"invalid status {status!r}; must be one of {sorted(VALID_GOAL_STATUSES)}"
            )
        return self.board.update(goal_id, status=status)

    def next_todo(self, goal_id: str) -> dict | None:
        """Return the first subtask in 'todo' status (oldest-first).

        Used by A-Loop Phase 2 to drive the loop: 'what's next to claim?'.
        Returns None if all subtasks are done/blocked.
        """
        view = self.get_goal(goal_id)
        if view is None:
            return None
        for s in view["subtasks"]:
            if s.get("status") in ("todo", "claimed"):
                return s
        return None
