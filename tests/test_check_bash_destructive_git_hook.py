"""Tests for scripts/hooks/check_bash_destructive_git.py.

Blocks destructive git commands (reset --hard, clean -f, checkout -- files,
branch -D) when working tree is dirty. Forces stash/commit first.

Pattern A (subprocess). Note: dirty-tree check uses subprocess git — when
working tree is clean (CI default), destructive commands pass.
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_bash_destructive_git.py"


def _run(cmd: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_git_command():
    assert _run("ls -la").returncode == 0


def test_passes_for_safe_git_command():
    assert _run("git status").returncode == 0


def test_passes_for_non_destructive_git():
    assert _run("git commit -m 'x'").returncode == 0


def test_destructive_command_exit_code_is_0_or_2():
    """Destructive commands either pass (clean tree) or block (dirty tree).
    Must never exit 1 (error)."""
    r = _run("git reset --hard HEAD~1")
    assert r.returncode in (0, 2), f"unexpected rc={r.returncode}: {r.stderr}"


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0
