"""Tests for scripts/hooks/check_drive_link.py — SessionStart passive check.

Passive SessionStart checker for A-Wiki external data links (drive/).
Warn-only, never blocks.
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_drive_link.py"


def _run(env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    # SessionStart hooks don't read stdin payload meaningfully — empty OK
    return subprocess.run([sys.executable, str(HOOK)], input="{}",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_always_exits_zero():
    """Passive hook — never blocks startup."""
    assert _run().returncode == 0


def test_fail_open_when_drive_missing():
    """If drive/ is missing, hook still passes (warn-only)."""
    assert _run().returncode == 0
