"""Tests for scripts/hooks/check_git_rebase_safety.py — Z3 warn-only.

Warn-only PreToolUse on Bash. Auto-backs up HEAD + warns about unpushed
commits before `git pull --rebase` or `git rebase`. Never blocks.

Pattern A (subprocess).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_git_rebase_safety.py"


def _run(cmd: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_git_command():
    assert _run("ls -la").returncode == 0


def test_passes_for_safe_git():
    assert _run("git status").returncode == 0


def test_hook_skip_substring_in_comma_list():
    r = _run("git pull --rebase", env_extra={"HOOK_SKIP": "check_git_rebase_safety,other"})
    assert r.returncode == 0


def test_rebase_command_does_not_block():
    """Warn-only — even on rebase, exit 0 (never blocks)."""
    r = _run("git pull --rebase")
    assert r.returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0


class TestWiring:
    def test_registered_in_pretooluse_bash_matcher(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PreToolUse", []):
            if "Bash" in grp.get("matcher", ""):
                for h in grp.get("hooks", []):
                    if "rebase" in h.get("command", ""):
                        return
        raise AssertionError("check_git_rebase_safety must be on Bash PreToolUse matcher")
