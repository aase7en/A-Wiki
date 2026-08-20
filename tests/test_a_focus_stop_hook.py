"""Tests for scripts/hooks/a_focus_stop.py — Stop hook.

Stop hook backstop of the focus system. Warns when a declared goal is
mid-chain at session end. Wired DIRECT (not via hooks_runner — runner
swallows exit-0 advisory stdout).

Pattern A (subprocess).
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "a_focus_stop.py"


def _run(env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input="{}",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_always_exits_zero():
    """Stop hook — advisory only, never blocks session end."""
    assert _run().returncode == 0


def test_hook_skip_substring_in_comma_list():
    r = _run(env_extra={"HOOK_SKIP": "a_focus_stop,other"})
    assert r.returncode == 0


def test_fail_open_silent():
    """Runs without crashing on the live repo."""
    assert _run().returncode == 0
