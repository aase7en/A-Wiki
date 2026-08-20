"""Tests for scripts/hooks/check_bash_no_branch.py — solo-wiki policy.

Blocks git checkout -b / switch -c / branch <name> / worktree add.
A-Wiki policy: commit directly to main only. No branches/PRs.

Pattern A (subprocess).
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_bash_no_branch.py"


def _run(cmd: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_git_command():
    assert _run("ls -la").returncode == 0


def test_passes_for_safe_git_status():
    assert _run("git status").returncode == 0


def test_passes_for_git_log():
    assert _run("git log --oneline").returncode == 0


def test_passes_for_branch_listing():
    assert _run("git branch -a").returncode == 0


def test_blocks_checkout_b():
    assert _run("git checkout -b feature/x").returncode == 2


def test_blocks_switch_c():
    assert _run("git switch -c new-feature").returncode == 2


def test_blocks_branch_create():
    assert _run("git branch new-branch").returncode == 2


def test_blocks_worktree_add():
    assert _run("git worktree add ../foo").returncode == 2


def test_passes_for_existing_branch_checkout():
    assert _run("git checkout main").returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0
