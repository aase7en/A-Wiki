"""Tests for scripts/hooks/check_subagent_fanout.py — Z3 warn-only.

PreToolUse on Agent tool. Warns (exit 0 always) when >=3 subagents would
hit the same provider bucket (the 2026-07-14 rate-limit incident).

Pattern A (subprocess).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_subagent_fanout.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_agent_tool():
    assert _run({"tool_name": "Bash", "tool_input": {}}).returncode == 0


def test_passes_for_single_agent_call():
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "Explore", "prompt": "x"}}
    assert _run(payload).returncode == 0


def test_hook_skip_substring_in_comma_list():
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "Explore", "prompt": "x"}}
    r = _run(payload, env_extra={"HOOK_SKIP": "check_subagent_fanout,other"})
    assert r.returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0


class TestWiring:
    def test_registered_in_pretooluse_agent_matcher(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PreToolUse", []):
            if "Agent" in grp.get("matcher", ""):
                for h in grp.get("hooks", []):
                    if "subagent-fanout" in h.get("command", "") or "subagent_fanout" in h.get("command", ""):
                        return
        raise AssertionError("check_subagent_fanout must be on Agent PreToolUse matcher")
