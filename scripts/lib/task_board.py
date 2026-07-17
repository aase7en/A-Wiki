"""task_board.py — atomic task claim/release/update for concurrent agents.

Neural Spine primitive #4 (built on atomic_json).

Task Board คือตัวกันชนกันของสมอง A-Wiki. ป้องกัน 2 agents claim task
เดียวกันพร้อมกัน — เหตุการณ์ที่เราเคยเจอ (session_start.py มี <<<<< HEAD
markers เพราะ concurrent session rebase).

Core invariant: claim() is atomic. Uses atomic_json.atomic_update (chunk 1)
which read-modify-writes the JSON file under a cross-process file lock.

Schema (.tmp/task-board.json):
  {
    "tasks": [
      {
        "id": "T1",
        "goal": "refactor X",
        "status": "todo|claimed|doing|done|blocked",
        "claimant": "claude" | null,
        "claim_ts": float | null,
        "lease_ttl": int,         # seconds (lease duration)
        "files": ["..."],
        "parent_goal_id": "G1" | null,
        "notes": ["..."]
      }
    ]
  }

API:
  TaskBoard(path).add(goal, files=[], parent_goal_id=None, lease_minutes=30)
  .claim(task_id, claimant, lease_minutes=30)  → bool (True if won)
  .release(task_id)                            → bool
  .update(task_id, status, note=None)          → bool
  .get(task_id)                                → dict | None
  .list(status=None)                           → list[dict]
  .is_expired(task)                            → bool  (for chunk 6 reaper)

Lease: a claim has a TTL. If claim_ts + lease_ttl < now → expired (claim
considered dead). Chunk 6 (task_lease_reaper.py) will reap expired claims
on SessionStart. Without reaping, crashed agents would lock tasks forever.
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atomic_json  # noqa: E402 -- sibling primitive (chunk 1)

VALID_STATUSES = {"todo", "claimed", "doing", "done", "blocked"}


class TaskBoard:
    """Atomic task board for concurrent agent coordination."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def _empty_state(self) -> dict:
        return {"tasks": [], "version": 1}

    def add(
        self,
        *,
        goal: str,
        files: list[str] | None = None,
        parent_goal_id: str | None = None,
        lease_minutes: int = 30,
    ) -> str:
        """Add a task in 'todo' status. Returns the new task's id."""
        task_id = f"T{uuid.uuid4().hex[:6].upper()}"

        def mutate(state: dict) -> Any:
            state.setdefault("tasks", []).append({
                "id": task_id,
                "goal": goal,
                "status": "todo",
                "claimant": None,
                "claim_ts": None,
                "lease_ttl": lease_minutes * 60,
                "files": list(files) if files else [],
                "parent_goal_id": parent_goal_id,
                "notes": [],
                "created_ts": time.time(),
            })
            return task_id  # return value is what atomic_update yields to caller

        return atomic_json.atomic_update(
            self.path, mutate, missing_default=self._empty_state()
        )

    def claim(
        self,
        task_id: str,
        *,
        claimant: str,
        lease_minutes: int = 30,
    ) -> bool:
        """Atomically claim a task. Returns True if this caller won, else False.

        Wins only if the task exists AND its status is 'todo' (or its existing
        claim has expired — see is_expired()). Done/blocked tasks cannot be
        reclaimed.
        """
        def mutate(state: dict) -> bool:
            for t in state.get("tasks", []):
                if t["id"] != task_id:
                    continue
                # Cannot claim a task that's done/blocked
                if t["status"] in ("done", "blocked"):
                    return False
                # If currently claimed AND the claim is still fresh → fail
                if t["status"] in ("claimed", "doing") and t.get("claimant"):
                    if not self.is_expired(t):
                        return False
                # We win the claim
                t["status"] = "claimed"
                t["claimant"] = claimant
                t["claim_ts"] = time.time()
                t["lease_ttl"] = lease_minutes * 60
                return True
            # Task not found → claim fails
            return False

        return atomic_json.atomic_update(
            self.path, mutate, missing_default=self._empty_state()
        )

    def release(self, task_id: str) -> bool:
        """Release a claimed task back to 'todo'. Returns True if released."""
        def mutate(state: dict) -> bool:
            for t in state.get("tasks", []):
                if t["id"] != task_id:
                    continue
                if t["status"] not in ("claimed", "doing"):
                    return False
                t["status"] = "todo"
                t["claimant"] = None
                t["claim_ts"] = None
                return True
            return False

        return atomic_json.atomic_update(
            self.path, mutate, missing_default=self._empty_state()
        )

    def update(
        self,
        task_id: str,
        *,
        status: str,
        note: str | None = None,
    ) -> bool:
        """Change a task's status, optionally appending a note."""
        if status not in VALID_STATUSES:
            raise ValueError(
                f"invalid status {status!r}; must be one of {sorted(VALID_STATUSES)}"
            )
        def mutate(state: dict) -> bool:
            for t in state.get("tasks", []):
                if t["id"] != task_id:
                    continue
                t["status"] = status
                if note:
                    t.setdefault("notes", []).append(note)
                if status in ("done", "blocked"):
                    # Final states clear the claim (defensive)
                    t["claimant"] = None
                    t["claim_ts"] = None
                return True
            return False

        return atomic_json.atomic_update(
            self.path, mutate, missing_default=self._empty_state()
        )

    def get(self, task_id: str) -> dict | None:
        """Return a single task dict, or None if not found. Read-only."""
        state = self._load()
        for t in state.get("tasks", []):
            if t["id"] == task_id:
                return t
        return None

    def list(self, *, status: str | None = None) -> list[dict]:
        """List tasks, optionally filtered by status. Oldest-first."""
        state = self._load()
        tasks = state.get("tasks", [])
        if status is None:
            return list(tasks)
        return [t for t in tasks if t.get("status") == status]

    def is_expired(self, task: dict, *, now: float | None = None) -> bool:
        """True if a claimed task's lease has expired.

        Returns False for non-claimed tasks (no lease to expire).
        """
        if task.get("status") not in ("claimed", "doing"):
            return False
        claim_ts = task.get("claim_ts")
        lease_ttl = task.get("lease_ttl", 0)
        if claim_ts is None:
            return False
        now = now if now is not None else time.time()
        return (now - claim_ts) > lease_ttl

    def _load(self) -> dict:
        """Read current state. Returns empty state if file missing."""
        if not self.path.is_file():
            return self._empty_state()
        import json
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self._empty_state()
