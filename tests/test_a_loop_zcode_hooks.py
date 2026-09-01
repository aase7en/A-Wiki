"""Tests for ZCode Loop Engineer hooks — Iron Law #1: failing tests FIRST.

Covers 3 modules (skills/awiki/a-loop Loop Engineer mode on ZCode):

  scripts/hooks/a_loop_continue.py  — Stop hook: request continuation while an
                                      autonomous a-loop goal still has todos
                                      (ZCode docs: decision "block" + reason,
                                      hard-capped at 3 consecutive continues).
  scripts/hooks/a_loop_ssot.py      — SessionStart hook: inject a-loop SSoT
                                      (active goal + next todo + recent WO
                                      checkpoints) as additionalContext.
  scripts/hooks/zcode_hook_loader.py — machine-local dispatcher for the
                                      ZCode user-level config: no-op when the
                                      target script is absent (non-A-Wiki
                                      projects stay silent), forwards
                                      stdin/stdout/exit-code otherwise.

Design contracts under test:
  - a_loop_continue NEVER exits non-zero (a Stop driver must not brick Stop)
  - autonomous mode is opt-in per goal via flag file .tmp/a-loop-autonomous
    containing the goal id (stale flags self-clean, never loop old goals)
  - continuation budget ≤3 per task; budget resets when the next todo moves
    (progress happened); stuck task → allow stop + advisory context
  - a_loop_ssot stays silent when no active goals (zero noise normal sessions)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import goal_store  # noqa: E402
import a_loop_continue as alc  # noqa: E402 -- module under test
import a_loop_ssot as assot  # noqa: E402
import zcode_hook_loader as zhl  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _seed_goal(state_dir: Path, *, n_subtasks: int = 2) -> tuple[str, list[str]]:
    """Create one active goal with subtasks on a fresh task board."""
    gs = goal_store.GoalStore(state_dir / "task-board.json")
    gid = gs.create_goal(objective="ship ZCode loop engineer")
    tids = [gs.add_subtask(gid, goal=f"subtask {i}") for i in range(n_subtasks)]
    return gid, tids


def _set_flag(state_dir: Path, goal_id: str) -> None:
    (state_dir / "a-loop-autonomous").write_text(goal_id, encoding="utf-8")


def _set_counter(state_dir: Path, goal_id: str, task_id: str, count: int) -> None:
    (state_dir / "a-loop-continuations.json").write_text(
        json.dumps({"goal_id": goal_id, "task_id": task_id, "count": count}),
        encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. a_loop_continue.decide — pure decision logic
# ---------------------------------------------------------------------------

def test_continue_allows_when_no_state(tmp_path):
    """No board / no flag → allow, silent (normal sessions unaffected)."""
    assert alc.decide(tmp_path)["action"] == "allow"


def test_continue_allows_without_flag_even_with_active_goal(tmp_path):
    """Autonomous mode is opt-in: active goal alone must not force a loop."""
    gid, _ = _seed_goal(tmp_path)
    assert gid
    assert alc.decide(tmp_path)["action"] == "allow"


def test_continue_blocks_with_next_todo(tmp_path):
    """Flag + active goal + remaining todo → block with task id in reason."""
    gid, tids = _seed_goal(tmp_path)
    _set_flag(tmp_path, gid)
    d = alc.decide(tmp_path)
    assert d["action"] == "block"
    assert tids[0] in d["reason"], f"reason must name next todo {tids[0]}: {d}"
    assert d["new_counter"]["count"] == 1


def test_continue_budget_cap_allows_after_three(tmp_path):
    """Same task still next after 3 continues → allow stop + advisory."""
    gid, tids = _seed_goal(tmp_path, n_subtasks=1)
    _set_flag(tmp_path, gid)
    _set_counter(tmp_path, gid, tids[0], 3)
    d = alc.decide(tmp_path)
    assert d["action"] == "allow"
    assert d["context"] and "checkpoint" in d["context"].lower()


def test_continue_resets_budget_when_task_progressed(tmp_path):
    """Counter stored for an old task but next todo moved → fresh budget."""
    gid, tids = _seed_goal(tmp_path, n_subtasks=2)
    _set_flag(tmp_path, gid)
    _set_counter(tmp_path, gid, "TOLD", 3)  # stale task → progress happened
    d = alc.decide(tmp_path)
    assert d["action"] == "block"
    assert d["new_counter"]["count"] == 1, "budget must reset on task change"
    assert d["new_counter"]["task_id"] == tids[0]


def test_continue_cleans_up_when_goal_complete(tmp_path):
    """Goal all-done (or flag stale) → allow + cleanup flag/counter."""
    gid, tids = _seed_goal(tmp_path, n_subtasks=1)
    gs = goal_store.GoalStore(tmp_path / "task-board.json")
    gs.update_goal(gid, status="done")
    gs.board.update(tids[0], status="done")
    _set_flag(tmp_path, gid)
    d = alc.decide(tmp_path)
    assert d["action"] == "allow"
    assert d["cleanup"] is True  # decide() is pure; main() performs removal
    rc = alc.main(state_dir=tmp_path)
    assert rc == 0
    assert not (tmp_path / "a-loop-autonomous").exists()
    assert not (tmp_path / "a-loop-continuations.json").exists()


def test_continue_stale_flag_for_missing_goal_allows(tmp_path):
    """Flag names a goal that no longer exists → allow + cleanup."""
    _set_flag(tmp_path, "GDEAD")
    d = alc.decide(tmp_path)
    assert d["action"] == "allow"
    alc.main(state_dir=tmp_path)
    assert not (tmp_path / "a-loop-autonomous").exists()


def test_continue_never_crashes_on_corrupt_board(tmp_path):
    """Corrupt JSON board must degrade to allow, never raise."""
    _set_flag(tmp_path, "G1")
    (tmp_path / "task-board.json").write_text("{not json", encoding="utf-8")
    assert alc.decide(tmp_path)["action"] == "allow"


# ---------------------------------------------------------------------------
# 2. a_loop_continue.main — end-to-end contract with ZCode Stop protocol
# ---------------------------------------------------------------------------

def test_continue_main_emits_block_json_and_persists_counter(tmp_path, capsys):
    gid, tids = _seed_goal(tmp_path)
    _set_flag(tmp_path, gid)
    rc = alc.main(state_dir=tmp_path)
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["decision"] == "block"
    assert tids[0] in out["reason"]
    saved = json.loads((tmp_path / "a-loop-continuations.json").read_text("utf-8"))
    assert saved["count"] == 1 and saved["task_id"] == tids[0]


def test_continue_main_allow_prints_nothing_on_plain_allow(tmp_path, capsys):
    rc = alc.main(state_dir=tmp_path)  # no state at all
    assert rc == 0
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# 3. a_loop_ssot — SessionStart SSoT injection
# ---------------------------------------------------------------------------

def test_ssot_silent_when_no_goals(tmp_path):
    assert assot.build_context(tmp_path, tmp_path) is None


def test_ssot_context_names_goal_and_next_todo(tmp_path):
    gid, tids = _seed_goal(tmp_path, n_subtasks=3)
    gs = goal_store.GoalStore(tmp_path / "task-board.json")
    gs.board.update(tids[0], status="done")  # 1/3 done
    ctx = assot.build_context(tmp_path, tmp_path)
    assert ctx is not None
    assert gid in ctx and tids[1] in ctx
    assert "1/3" in ctx  # progress fraction


def test_ssot_includes_recent_wo_checkpoint(tmp_path):
    gid, _ = _seed_goal(tmp_path)
    wo_dir = tmp_path / "docs" / "work-orders"
    wo_dir.mkdir(parents=True)
    (wo_dir / "WO-X-1.md").write_text(
        "# WO-X-1\n\nStatus: ACTIVE\n\n## Checkpoint\n- did a thing\n",
        encoding="utf-8")
    ctx = assot.build_context(tmp_path, tmp_path)
    assert "WO-X-1" in ctx and "ACTIVE" in ctx


def test_ssot_never_crashes_on_corrupt_state(tmp_path):
    (tmp_path / "task-board.json").write_text("{{{{", encoding="utf-8")
    assert assot.build_context(tmp_path, tmp_path) is None


# ---------------------------------------------------------------------------
# 4. zcode_hook_loader — user-level config dispatcher
# ---------------------------------------------------------------------------

def test_loader_noop_when_target_missing(tmp_path):
    assert zhl.run(tmp_path / "nope.py", [], b"") == 0


def test_loader_forwards_stdin_stdout_and_exit_codes(tmp_path):
    target = tmp_path / "echo_hook.py"
    target.write_text(
        "import sys\n"
        "data = sys.stdin.buffer.read()\n"
        "print('seen:' + data.decode())\n"
        "sys.exit(2)\n",
        encoding="utf-8")
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = zhl.run(target, [], b"ping")
    assert rc == 2, "exit code 2 (block) must pass through for gate hooks"
    assert "seen:ping" in buf.getvalue()


def test_loader_normalizes_unexpected_exit_codes(tmp_path):
    """Child exiting 7 (bug) must not surface as hook error noise → 0."""
    target = tmp_path / "boom.py"
    target.write_text("import sys\nprint('x')\nsys.exit(7)\n", encoding="utf-8")
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        assert zhl.run(target, [], b"") == 0
