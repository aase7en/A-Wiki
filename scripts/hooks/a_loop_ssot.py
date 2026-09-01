"""a_loop_ssot.py — A-Loop ZCode Loop Engineer: SessionStart SSoT injection.

Implements "RECOVER SSoT / VERIFY ACTUAL STATE" of the a-loop cycle on ZCode:
every session start inside a repo that has an active a-loop goal gets the
goal state (objective, progress, NEXT READY NODE) plus the most recent
work-order checkpoints injected as additionalContext — any agent resumes
without the user re-pasting anything (the cross-agent handoff contract in
docs/protocols/cross-agent-work-orders.md).

Silent (no output) when no active goals exist — zero noise for normal
sessions and non-A-Wiki projects (the zcode_hook_loader no-ops entirely when
the script is absent). Never raises.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"
sys.path.insert(0, str(LIB_DIR))

import goal_store  # noqa: E402

ACTIVE_GOAL_STATUSES = {"todo", "claimed", "doing"}
_STATUS_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)


def _recent_work_orders(repo_root: Path, limit: int = 2) -> list[tuple[str, str]]:
    """Most recently modified WO files with their Status line (cheap SSoT)."""
    wo_dir = repo_root / "docs" / "work-orders"
    if not wo_dir.is_dir():
        return []
    try:
        files = sorted(
            (p for p in wo_dir.glob("WO-*.md") if p.is_file()),
            key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    except OSError:
        return []
    out = []
    for p in files:
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:2000]
            m = _STATUS_RE.search(head)
            out.append((p.stem, m.group(1).strip() if m else "status?"))
        except OSError:
            continue
    return out


def build_context(state_dir: Path, repo_root: Path) -> str | None:
    """SSoT text for active a-loop goals, or None when there is nothing."""
    state_dir = Path(state_dir)
    board = state_dir / "task-board.json"
    if not board.exists():
        return None
    try:
        gs = goal_store.GoalStore(board)
        goals = [g for g in gs.list_goals()
                 if g.get("status") in ACTIVE_GOAL_STATUSES]
    except Exception:
        return None
    if not goals:
        return None
    lines = ["[a-loop SSoT — ทำต่อจากนี้ ห้ามเริ่มใหม่]"]
    for g in goals[:3]:
        gid = g.get("id", "?")
        try:
            prog = gs.goal_progress(gid)
            nxt = gs.next_todo(gid)
        except Exception:
            continue
        done = int(prog.get("done", 0))
        total = int(prog.get("total", 0))
        entry = (f"- goal {gid} «{g.get('goal', '?')}» — {done}/{total} done")
        if nxt:
            entry += (f" | NEXT: {nxt.get('id')} «{nxt.get('goal', '?')}»")
        else:
            entry += " | ทุก subtask แล้วเสร็จ (ปิด goal → Phase 3 distill)"
        lines.append(entry)
    wos = _recent_work_orders(Path(repo_root))
    if wos:
        lines.append("- WO ล่าสุด: "
                     + "; ".join(f"{name} ({status})" for name, status in wos))
    lines.append("- ก่อน mutation: อ่าน COLLAB.md (lanes+claims) และทำต่อจาก "
                 "Checkpoint ล่าสุดของ WO ที่เกี่ยวข้อง")
    return "\n".join(lines)


def main(state_dir=None, repo_root=None) -> int:
    """ZCode SessionStart hook entry: emit additionalContext JSON or nothing."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    try:
        state_dir = Path(state_dir or os.environ.get(
            "AWIKI_ALOOP_STATE_DIR", str(REPO_ROOT / ".tmp")))
        repo_root = Path(repo_root or REPO_ROOT)
        ctx = build_context(state_dir, repo_root)
        if ctx:
            print(json.dumps({"additionalContext": ctx}, ensure_ascii=False))
    except Exception:
        pass  # SessionStart injection must never block a session
    return 0


if __name__ == "__main__":
    sys.exit(main())
