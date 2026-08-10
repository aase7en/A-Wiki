"""Tests for scripts/hooks/check_delegation_gate.py.

Blocks delegation of sensitive work (wiki edits, AGENTS.md, CLAUDE.md,
sensitive scripts) to subagents — primary agent must do it.

Pattern A (subprocess).
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_delegation_gate.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_task_tool():
    assert _run({"tool_name": "Bash", "tool_input": {"command": "ls"}}).returncode == 0


def test_passes_for_safe_subagent_task():
    """Delegating a non-sensitive task (e.g. grep for foo) → pass."""
    payload = {"tool_name": "Task",
               "tool_input": {"description": "grep for foo",
                              "prompt": "find all occurrences of 'foo'"}}
    assert _run(payload).returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0


class TestWiring:
    def test_registered_in_pretooluse(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PreToolUse", []):
            for h in grp.get("hooks", []):
                if "delegation" in h.get("command", ""):
                    return
        raise AssertionError("check_delegation_gate must be registered on PreToolUse")
