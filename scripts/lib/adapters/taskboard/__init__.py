"""adapters/taskboard — production + mock TaskBoardPort.

ADR-0012 slice A4. Two adapters prove TaskBoardPort is a real seam:
  - JsonlTaskBoardAdapter (prod): wraps task_board.TaskBoard
  - InMemoryTaskBoardAdapter (mock): for headless tests
"""
from __future__ import annotations

from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import task_board  # noqa: E402


class JsonlTaskBoardAdapter:
    """Production adapter: TaskBoardPort backed by task_board.TaskBoard."""

    def __init__(self, tasks_path: Path | str) -> None:
        self._path = Path(tasks_path)
        self._board = task_board.TaskBoard(self._path)

    def add(self, *, goal: str, files: list[str] | None = None,
            parent_goal_id: str | None = None,
            lease_minutes: int = 30) -> str:
        return self._board.add(
            goal=goal, files=files or [],
            parent_goal_id=parent_goal_id, lease_minutes=lease_minutes,
        )

    def claim(self, task_id: str, *, claimant: str,
              lease_minutes: int = 30) -> bool:
        return self._board.claim(
            task_id, claimant=claimant, lease_minutes=lease_minutes,
        )

    def release(self, task_id: str) -> bool:
        return self._board.release(task_id)

    def update(self, task_id: str, *, status: str,
               note: str | None = None) -> bool:
        return self._board.update(task_id, status=status, note=note)

    def list(self, *, status: str | None = None) -> list[dict]:
        return self._board.list(status=status)


class InMemoryTaskBoardAdapter:
    """Mock adapter: TaskBoardPort backed by an in-process dict.

    Implements the same atomicity contract the prod board guarantees:
    claim() is 'atomic' (first caller wins, second loses), and an expired
    lease CAN be reclaimed by another agent (the Iron Law #11 self-reap
    floor). This lets the char-test verify behaviour without touching disk.

    A-Council 2026-08-02 (code-review #3): mirrors prod's VALID_STATUSES
    validation in update() so the contract suite cannot mask a divergence.
    """

    _VALID_STATUSES = {"todo", "claimed", "doing", "done", "blocked"}

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}

    def add(self, *, goal: str, files: list[str] | None = None,
            parent_goal_id: str | None = None,
            lease_minutes: int = 30) -> str:
        tid = f"t{uuid.uuid4().hex[:8]}"
        self._tasks[tid] = {
            "id": tid, "goal": goal, "files": files or [],
            "parent_goal_id": parent_goal_id,
            "status": "todo", "claimant": None,
            "claim_ts": None, "lease_ttl": None,
        }
        return tid

    def claim(self, task_id: str, *, claimant: str,
              lease_minutes: int = 30) -> bool:
        import time
        t = self._tasks.get(task_id)
        if t is None:
            return False
        if t["status"] in ("done", "blocked"):
            return False
        # If currently claimed/doing AND the claim is still fresh → fail.
        # Mirrors prod's is_expired() logic.
        if t["status"] in ("claimed", "doing") and t.get("claimant"):
            if not self._is_expired(t):
                return False
        # We win the claim (or re-claim the expired one)
        t["status"] = "claimed"
        t["claimant"] = claimant
        t["claim_ts"] = time.time()
        t["lease_ttl"] = lease_minutes * 60
        return True

    @staticmethod
    def _is_expired(task: dict) -> bool:
        """Mirror prod's lease-expiry check: claim_ts + lease_ttl < now."""
        import time
        if not task.get("claim_ts") or not task.get("lease_ttl"):
            return False
        return (task["claim_ts"] + task["lease_ttl"]) < time.time()

    def release(self, task_id: str) -> bool:
        t = self._tasks.get(task_id)
        if t is None or t["status"] not in ("claimed", "doing"):
            return False
        t["status"] = "todo"
        t["claimant"] = None
        t["claim_ts"] = None
        return True

    def update(self, task_id: str, *, status: str,
               note: str | None = None) -> bool:
        # A-Council 2026-08-02: mirror prod validation so the contract
        # suite catches divergence instead of hiding it.
        if status not in self._VALID_STATUSES:
            raise ValueError(
                f"invalid status {status!r}; must be one of "
                f"{sorted(self._VALID_STATUSES)}"
            )
        t = self._tasks.get(task_id)
        if t is None:
            return False
        t["status"] = status
        if note is not None:
            t.setdefault("notes", []).append(note)
        return True

    def list(self, *, status: str | None = None) -> list[dict]:
        if status is None:
            return list(self._tasks.values())
        return [t for t in self._tasks.values() if t["status"] == status]
