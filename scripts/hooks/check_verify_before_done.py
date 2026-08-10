"""check_verify_before_done.py — Stop advisory hook.

Iron Law #1 corollary: 'done' must be backed by an outcome entry.

The skill 'verify-before-done' appears in 3+ a-* packs (a-debug,
a-flow spine, addyosmani lifecycle) but had no enforcement — agents
could mark a task 'done' without recording what was verified. This
hook turns the skill into an advisory Stop gate.

At session Stop:
  1. Load .tmp/task-board.json → find tasks with status='done' that were
     updated within the last WINDOW_SECONDS (default 3600s = 1h).
  2. For each such task, check .tmp/memory-ledger.jsonl for a type=outcome
     entry that references the task_id.
  3. If a 'done' task has no matching outcome → warn (stdout, exit 0).

This is ADVISORY: it ALWAYS exits 0. Stop hooks must never block the
session from ending (that would lock the agent in). The warning is
surfaced so the agent/user can decide whether to record an outcome.

Wired DIRECT on Stop (not via hooks_runner.py) because the runner uses
capture_output=True and only forwards stderr on exit 2 — an exit-0
advisory hook's stdout warnings would be silently swallowed. See
test_self_audit.py:143-148 for the same contract.

Override: HOOK_SKIP=check_verify_before_done (substring match)

Cross-agent caveat: runs in Claude Code only (substrate Hook). Other
agents must check the task-board state manually at session end.

Rationale: AGENTS.md §Iron Laws (Law #1 corollary) + 'verify-before-done'
skill appearing in a-debug, a-flow spine, addyosmani lifecycle.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Windows console UTF-8 (Thai messages render correctly)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent

DEFAULT_TASK_BOARD = REPO_ROOT / ".tmp" / "task-board.json"
DEFAULT_LEDGER_PATH = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
DEFAULT_WINDOW_SECONDS = 3600  # 1 hour


def _emit(text: str) -> None:
    """Write to STDOUT — this hook is wired DIRECT on Stop, so stdout
    reaches the user (the runner would swallow exit-0 advisory output)."""
    sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _load_done_tasks(task_board_path: Path, *, window_seconds: float) -> list[dict]:
    """Return tasks with status='done' updated within the time window.

    Uses claim_ts (last activity) as the timestamp proxy. Fail-soft:
    returns [] on missing file, corrupt JSON, or any error.
    """
    try:
        if not task_board_path.is_file():
            return []
        data = json.loads(task_board_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    cutoff = time.time() - window_seconds
    out: list[dict] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if t.get("status") != "done":
            continue
        # Use claim_ts if present (last activity); fall back to created_ts.
        ts = t.get("claim_ts") or t.get("created_ts") or 0
        try:
            ts_f = float(ts)
        except (TypeError, ValueError):
            continue
        if ts_f >= cutoff:
            out.append(t)
    return out


def _has_outcome_for(ledger_path: Path, task_id: str) -> bool:
    """True iff the ledger has a type=outcome entry referencing task_id.

    Fail-soft: returns False on missing file or corrupt JSONL (treat as
    'no outcome' — the warning will fire, which is the safe default).
    """
    try:
        if not ledger_path.is_file():
            return False
        # Stream line-by-line (ledger can be large).
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip corrupt line
                if entry.get("type") != "outcome":
                    continue
                # Match if task_id appears in summary, tags, or files.
                summary = (entry.get("summary") or "").lower()
                tags = [str(t).lower() for t in entry.get("tags") or []]
                files = [str(f).lower() for f in entry.get("files") or []]
                hay = " ".join([summary] + tags + files)
                if task_id.lower() in hay:
                    return True
        return False
    except Exception:
        return False


def evaluate(
    task_board_path: Path = DEFAULT_TASK_BOARD,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    *,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
) -> list[str]:
    """Return list of warning messages (empty list = no warnings).

    Pure function — no side effects, no I/O emissions. Caller decides
    how to surface the warnings (stdout for direct-wire Stop hook).
    """
    warnings: list[str] = []
    done_tasks = _load_done_tasks(task_board_path, window_seconds=window_seconds)
    for t in done_tasks:
        task_id = t.get("id", "?")
        if _has_outcome_for(ledger_path, str(task_id)):
            continue
        goal = (t.get("goal") or "")[:60]
        warnings.append(
            f"[verify-before-done] Task {task_id} marked done but no outcome entry. "
            f"goal: '{goal}'. "
            f"Run verify-before-done or memory_remember(type='outcome') to record."
        )
    return warnings


def main() -> int:
    """Hook entry point. Exits 0 always (advisory, never blocks).

    Passes module globals EXPLICITLY to evaluate() (rather than relying
    on default args) so that monkeypatch.setattr(cvb, "DEFAULT_TASK_BOARD",
    ...) in tests takes effect — default args are bound at def-time.
    """
    if "check_verify_before_done" in os.environ.get("HOOK_SKIP", ""):
        return 0
    try:
        warnings = evaluate(DEFAULT_TASK_BOARD, DEFAULT_LEDGER_PATH)
        for w in warnings:
            _emit(w)
    except Exception as e:
        # Fail-soft: never break the session-ending flow.
        sys.stderr.write(f"[verify-before-done] error (fail-soft): {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
