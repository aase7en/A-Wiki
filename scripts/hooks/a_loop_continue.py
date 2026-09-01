"""a_loop_continue.py — A-Loop ZCode Loop Engineer: Stop-hook continuation driver.

ZCode hooks reference (zcode.z.ai/en/docs/hooks, verified 2026-09-01): a Stop
hook returning {"decision": "block", "reason": ...} makes the main model keep
running — ZCode itself hard-caps this at 3 consecutive continuations. This
hook is the autonomous "NEXT READY NODE ↺" step of the a-loop cycle on ZCode
(skills/awiki/a-loop Loop Engineer mode).

Opt-in per goal: the skill writes .tmp/a-loop-autonomous containing the goal
id. Stale flags self-clean (goal done/missing). Continuation budget is ≤3
per task, resets when the next todo moves (progress happened); a task that
never advances gets an allow + checkpoint advisory instead of an infinite
spin.

Direct-wired in the ZCode user-level config, deliberately NOT via
hooks_runner: the runner soft-classifies Stop hooks (never block) and a
continuation driver is a manager, not an enforcement gate.

NEVER exits non-zero — a Stop driver must not brick Stop.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

import goal_store  # noqa: E402 -- A-Loop Chunk 1 goal lifecycle

ACTIVE_GOAL_STATUSES = {"todo", "claimed", "doing"}
MAX_CONTINUE = int(os.environ.get("AWIKI_ALOOP_MAX_CONTINUE", "3"))
FLAG_NAME = "a-loop-autonomous"
COUNTER_NAME = "a-loop-continuations.json"


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def decide(state_dir: Path) -> dict:
    """Pure decision — no writes, no prints, never raises on bad state.

    Returns {action: allow|block, reason, context, cleanup, new_counter}.
    """
    state_dir = Path(state_dir)
    result = {"action": "allow", "reason": None, "context": None,
              "cleanup": False, "new_counter": None}
    flag = state_dir / FLAG_NAME
    if not flag.exists():
        return result
    try:
        goal_id = flag.read_text(encoding="utf-8").strip()
    except OSError:
        return result
    board = state_dir / "task-board.json"
    if not goal_id or not board.exists():
        result["cleanup"] = True
        return result
    try:
        gs = goal_store.GoalStore(board)
        goals = gs.list_goals()
    except Exception:
        # Corrupt board — degrade to allow; flag kept in case state recovers.
        return result
    goal = next((g for g in goals if g.get("id") == goal_id), None)
    if goal is None or goal.get("status") not in ACTIVE_GOAL_STATUSES:
        result["cleanup"] = True
        return result
    try:
        nxt = gs.next_todo(goal_id)
        progress = gs.goal_progress(goal_id)
    except Exception:
        return result
    if nxt is None:
        result["cleanup"] = True
        result["context"] = (
            f"[a-loop] goal {goal_id} ทุก subtask แล้วเสร็จ — ปิด goal "
            f"(update_goal status=done) แล้วเข้า Phase 3 distill")
        return result
    counter = _read_json(state_dir / COUNTER_NAME, {})
    same_task = (counter.get("task_id") == nxt.get("id")
                 and counter.get("goal_id") == goal_id)
    count = int(counter.get("count", 0)) if same_task else 0
    if count >= MAX_CONTINUE:
        result["context"] = (
            f"[a-loop] continuation budget ครบ {MAX_CONTINUE} รอบสำหรับ "
            f"{nxt.get('id')} (task ไม่คืบ) — checkpoint ลง work order + "
            f"task_board แล้วจบรอบนี้ รอ user สั่ง loop ต่อ (ห้าม spin รอ)")
        return result
    total = max(int(progress.get("total", 0)), 1)
    done = int(progress.get("done", 0))
    result["action"] = "block"
    result["new_counter"] = {"goal_id": goal_id, "task_id": nxt.get("id"),
                             "count": count + 1}
    result["reason"] = (
        f"[a-loop] goal {goal_id} «{goal.get('goal', '?')}» ยังไม่จบ "
        f"({done}/{total} done) — ทำต่อ task ถัดไป: {nxt.get('id')} "
        f"«{nxt.get('goal', '?')}» (รอบ {count + 1}/{MAX_CONTINUE}) "
        f"เสร็จแล้ว task_board update status=done ก่อนขึ้น task ใหม่")
    return result


def _cleanup(state_dir: Path) -> None:
    for name in (FLAG_NAME, COUNTER_NAME):
        try:
            (state_dir / name).unlink(missing_ok=True)
        except OSError:
            pass


def main(state_dir=None) -> int:
    """ZCode Stop hook entry: emit block/allow protocol JSON. Exit 0 always."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    try:
        if state_dir is None:
            state_dir = Path(os.environ.get(
                "AWIKI_ALOOP_STATE_DIR", str(REPO_ROOT / ".tmp")))
        d = decide(state_dir)
        if d["cleanup"]:
            _cleanup(state_dir)
        if d["action"] == "block":
            (state_dir / COUNTER_NAME).write_text(
                json.dumps(d["new_counter"], ensure_ascii=False),
                encoding="utf-8")
            print(json.dumps({"decision": "block", "reason": d["reason"]},
                             ensure_ascii=False))
        elif d["context"]:
            print(json.dumps({"additionalContext": d["context"]},
                             ensure_ascii=False))
    except Exception:
        pass  # a Stop driver must never brick Stop
    return 0


if __name__ == "__main__":
    sys.exit(main())
