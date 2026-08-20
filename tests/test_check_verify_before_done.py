"""Tests for scripts/hooks/check_verify_before_done.py — Stop advisory hook.

Iron Law #1 corollary: 'done' must be backed by an outcome entry.

The skill 'verify-before-done' appears in 3+ a-* packs (a-debug,
a-flow spine, addyosmani lifecycle) but had no enforcement. This hook
turns it into an advisory Stop hook: at session end, if a task was
recently marked 'done' but no memory_ledger outcome entry references
it, the hook warns (stdout, exit 0).

Pattern B (in-process import + monkeypatch) — mirrors test_self_audit.py.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import check_verify_before_done as cvb  # noqa: E402
import memory_ledger as ml  # noqa: E402


def _write_task_board(path: Path, tasks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"tasks": tasks, "version": 1}, ensure_ascii=False),
        encoding="utf-8",
    )


def _make_done_task(task_id: str = "T123abc", *, age_seconds: float = 60) -> dict:
    """A task marked done ~1 minute ago (within the default 1h window)."""
    return {
        "id": task_id,
        "goal": "do something",
        "status": "done",
        "claimant": "me",
        "claim_ts": time.time() - age_seconds - 60,
        "lease_ttl": 1800,
        "files": [],
        "parent_goal_id": None,
        "notes": [],
        "created_ts": time.time() - age_seconds - 120,
    }


# ---------------------------------------------------------------------------
# 1. Pass cases (nothing to verify)
# ---------------------------------------------------------------------------
def test_passes_when_no_task_board(monkeypatch, tmp_path):
    """Missing task-board.json → pass silently (fail-soft)."""
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tmp_path / "missing.json")
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert cvb.main() == 0


def test_passes_when_no_done_tasks(monkeypatch, tmp_path):
    """A task-board with no 'done' tasks → pass silently."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [
        {"id": "T1", "status": "todo", "goal": "pending",
         "claim_ts": None, "lease_ttl": 0, "files": [], "notes": [],
         "parent_goal_id": None, "created_ts": time.time()},
    ])
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert cvb.main() == 0


def test_passes_when_done_task_is_old(monkeypatch, tmp_path):
    """A 'done' task older than the window (default 1h) → not checked."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task(age_seconds=7200)])  # 2h ago
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert cvb.main() == 0


# ---------------------------------------------------------------------------
# 2. Warn cases (done without outcome)
# ---------------------------------------------------------------------------
def test_warns_when_done_without_outcome(monkeypatch, tmp_path, capsys):
    """Task marked done + no outcome entry → warn on stdout, exit 0."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task(task_id="Taa1111")])
    ledger_path = tmp_path / "ledger.jsonl"
    # Ledger exists but has no type=outcome entries
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="some unrelated decision")
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", ledger_path)
    rc = cvb.main()
    assert rc == 0  # advisory, never blocks
    out = capsys.readouterr().out
    assert "verify-before-done" in out.lower() or "outcome" in out.lower(), (
        f"expected advisory warning on stdout, got: {out!r}"
    )


def test_warns_for_each_unverified_done_task(monkeypatch, tmp_path, capsys):
    """Multiple done tasks without outcomes → one warning per task."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [
        _make_done_task(task_id="T1aaaa", age_seconds=60),
        _make_done_task(task_id="T2bbbb", age_seconds=120),
    ])
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", ledger_path)
    cvb.main()
    out = capsys.readouterr().out
    # Both task ids should appear in the warning
    assert "T1aaaa" in out
    assert "T2bbbb" in out


# ---------------------------------------------------------------------------
# 3. Pass when outcome exists
# ---------------------------------------------------------------------------
def test_passes_silently_when_done_has_outcome(monkeypatch, tmp_path, capsys):
    """Task marked done + outcome entry references it → no warning."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task(task_id="T1aaaa")])
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(
        session_id="s", type="outcome",
        summary="Task T1aaaa verified: 21 tests green, no regressions",
        tags=["verify-before-done"])
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", ledger_path)
    cvb.main()
    out = capsys.readouterr().out
    # Should NOT warn (outcome exists)
    assert "verify-before-done" not in out.lower() or "T1aaaa" not in out, (
        f"expected no warning when outcome exists, got: {out!r}"
    )


# ---------------------------------------------------------------------------
# 4. Fail-soft (corrupt state files)
# ---------------------------------------------------------------------------
def test_passes_on_corrupt_task_board(monkeypatch, tmp_path):
    """Corrupt JSON in task-board.json → pass silently."""
    tb = tmp_path / "task-board.json"
    tb.parent.mkdir(parents=True, exist_ok=True)
    tb.write_text("{ this is not valid json }}}", encoding="utf-8")
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert cvb.main() == 0


def test_passes_on_corrupt_ledger(monkeypatch, tmp_path):
    """Corrupt JSONL in memory-ledger.jsonl → pass silently."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task()])
    ledger_path = tmp_path / "ledger.jsonl"
    ledger_path.write_text("not valid jsonl\n{also broken\n", encoding="utf-8")
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", ledger_path)
    assert cvb.main() == 0


# ---------------------------------------------------------------------------
# 5. HOOK_SKIP override
# ---------------------------------------------------------------------------
def test_hook_skip_exact_match(monkeypatch, tmp_path, capsys):
    """HOOK_SKIP=check_verify_before_done → skip, no output."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task()])
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setenv("HOOK_SKIP", "check_verify_before_done")
    cvb.main()
    out = capsys.readouterr().out
    assert out == "", f"HOOK_SKIP should suppress output, got: {out!r}"


def test_hook_skip_substring_in_comma_list(monkeypatch, tmp_path, capsys):
    """HOOK_SKIP='check_verify_before_done,other' → also skip."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [_make_done_task()])
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tb)
    monkeypatch.setattr(cvb, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setenv("HOOK_SKIP", "check_verify_before_done,other_hook")
    cvb.main()
    out = capsys.readouterr().out
    assert out == ""


# ---------------------------------------------------------------------------
# 6. Pure-function unit tests
# ---------------------------------------------------------------------------
def test_load_done_tasks_returns_empty_on_missing_file(monkeypatch, tmp_path):
    """_load_done_tasks returns [] when the file is missing."""
    monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD", tmp_path / "nope.json")
    assert cvb._load_done_tasks(tmp_path / "nope.json", window_seconds=3600) == []


def test_load_done_tasks_filters_by_window(monkeypatch, tmp_path):
    """Tasks older than the window are excluded."""
    tb = tmp_path / "task-board.json"
    _write_task_board(tb, [
        _make_done_task(task_id="Trecent", age_seconds=60),
        _make_done_task(task_id="Told", age_seconds=7200),  # 2h, outside window
    ])
    recent = cvb._load_done_tasks(tb, window_seconds=3600)
    ids = [t["id"] for t in recent]
    assert "Trecent" in ids
    assert "Told" not in ids


def test_has_outcome_for_task(monkeypatch, tmp_path):
    """_has_outcome_for returns True when ledger has matching outcome."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(
        session_id="s", type="outcome",
        summary="Task Taa1111 verified", tags=[])
    assert cvb._has_outcome_for(ledger_path, "Taa1111") is True
    assert cvb._has_outcome_for(ledger_path, "Tzz9999") is False


# ---------------------------------------------------------------------------
# 7. TestWiring — must be wired DIRECT on Stop (not via hooks_runner)
# ---------------------------------------------------------------------------
