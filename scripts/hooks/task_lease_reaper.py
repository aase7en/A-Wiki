"""task_lease_reaper.py — release expired task claims (SessionStart hook).

Neural Spine Phase 1, chunk 6 of 9.

ปัญหา: agent claim task แล้ว crash ไป → task ค้างเป็น 'claimed' ตลอดกาล
→ agent อื่นไม่สามารถรับต่อได้.

แก้: reaper ทำงานทุก SessionStart (เป็น best-effort periodic cleanup):
  1. อ่าน task-board.json
  2. หาทุก task ที่ is_expired() == True
  3. release กลับเป็น 'todo'
  4. log ว่า reaped กี่ตัว

ไม่มี daemon — แค่ hook ที่ SessionStart เรียก. Override: HOOK_SKIP=task_lease_reaper.
Never blocks (exits 0 เสมอ).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import task_board as tb  # noqa: E402

DEFAULT_BOARD_PATH = REPO_ROOT / ".tmp" / "task-board.json"


def reap_expired_claims(board_path: Path | str = DEFAULT_BOARD_PATH) -> int:
    """Release all tasks whose lease has expired. Returns count reaped.

    Best-effort: logs to stderr, returns 0 on any failure. Never raises.
    """
    try:
        board = tb.TaskBoard(board_path)
        tasks = board.list()
    except Exception as e:
        sys.stderr.write(f"[task_lease_reaper] could not read board: {e}\n")
        return 0

    now = time.time()
    reaped = 0
    for t in tasks:
        try:
            if board.is_expired(t, now=now):
                task_id = t.get("id")
                if task_id and board.release(task_id):
                    reaped += 1
                    sys.stderr.write(
                        f"[task_lease_reaper] released expired claim on {task_id} "
                        f"(was claimed by {t.get('claimant', '?')})\n"
                    )
        except Exception as e:
            # Don't let one bad task abort the whole reap
            sys.stderr.write(f"[task_lease_reaper] error on task {t.get('id')}: {e}\n")
    if reaped:
        sys.stderr.write(f"[task_lease_reaper] reaped {reaped} expired claim(s)\n")
    return reaped


def main() -> int:
    """Hook entry point. Reads nothing from stdin. Exits 0 always."""
    if os.environ.get("HOOK_SKIP") == "task_lease_reaper":
        return 0
    try:
        reap_expired_claims()
    except Exception as e:
        sys.stderr.write(f"[task_lease_reaper] unexpected error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
