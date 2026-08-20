"""Tests for scripts/hooks/check_cost_tier.py.

Pattern A (subprocess). Forces cost-tier declaration before primary-model
Edit/Write/Agent calls. HOOK_SKIP substring escape hatch.
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_cost_tier.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_when_hook_skip_exact():
    r = _run({"tool_name": "Edit", "tool_input": {"file_path": "x.py"}},
             env_extra={"HOOK_SKIP": "check_cost_tier"})
    assert r.returncode == 0


def test_passes_when_hook_skip_substring_in_comma_list():
    r = _run({"tool_name": "Edit", "tool_input": {"file_path": "x.py"}},
             env_extra={"HOOK_SKIP": "check_cost_tier,other"})
    assert r.returncode == 0


def test_passes_for_read_tool():
    assert _run({"tool_name": "Read", "tool_input": {}}).returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0
