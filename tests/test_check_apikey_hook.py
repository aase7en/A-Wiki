"""Tests for scripts/hooks/check_apikey.py — Iron Law #6 corollary.

Pattern A (subprocess). Scans Bash commands for --api-key/--token/--key
literals to prevent session-log secret exposure.

Coverage: pass on non-Bash, pass on safe command, BLOCK on --api-key=AIza...,
BLOCK on --token sk-..., pass on placeholder, fail-open, TestWiring.
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_apikey.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def _bash(cmd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def test_passes_for_non_bash():
    assert _run({"tool_name": "Read", "tool_input": {}}).returncode == 0


def test_passes_for_safe_command():
    assert _run(_bash("ls -la")).returncode == 0


def test_passes_for_git_command():
    assert _run(_bash("git status")).returncode == 0


def test_blocks_api_key_flag():
    r = _run(_bash('curl --api-key "AIza' + "SyB1234567890abcdefghijklmnopqrstuv" + '" https://x'))
    assert r.returncode == 2


def test_blocks_token_flag():
    r = _run(_bash('cli --token "sk-' + "AbCdEf1234567890abcdefghijklmnop" + '"'))
    assert r.returncode == 2


def test_passes_when_placeholder_token():
    r = _run(_bash('curl --api-key YOUR_API_KEY https://x'))
    assert r.returncode == 0


def test_passes_when_no_command():
    assert _run({"tool_name": "Bash", "tool_input": {}}).returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0
