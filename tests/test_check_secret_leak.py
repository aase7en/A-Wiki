"""Tests for scripts/hooks/check_secret_leak.py — Iron Law #6 gate.

Iron Law #6: private/heavy data stays in drive/. This hook scans tool
payloads and git staged-diffs for real-looking secrets (OpenAI/GitHub/
AWS/Slack/JWT patterns) and blocks (exit 2) when found.

Pattern A (subprocess) — mirrors tests/test_check_test_before_code.py.

Coverage:
  - Pass when payload contains no secret-like tokens
  - BLOCK when payload contains sk-XXX (OpenAI-style)
  - BLOCK when payload contains GitHub token ghp_XXX
  - BLOCK when payload contains AWS AKIA key
  - BLOCK when payload contains Slack token xoxb-XXX
  - BLOCK when payload contains JWT eyJ...
  - Pass when token is an obvious placeholder (sk-XXXX, YOUR_API_KEY)
  - Fail-open on non-JSON stdin
  - Pass when no payload fields (empty tool_input)
  - TestWiring: registered on PreToolUse
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_secret_leak.py"


def _run(payload: dict, *, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


# ---------------------------------------------------------------------------
# 1. Pass cases (no secret-like tokens)
# ---------------------------------------------------------------------------
def test_passes_when_payload_has_no_secrets():
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "foo.py", "content": "x = 1\n"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_when_only_normal_text():
    payload = {"tool_name": "Edit",
               "tool_input": {"file_path": "README.md",
                              "old_string": "hello",
                              "new_string": "world"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_when_tool_input_empty():
    r = _run({"tool_name": "Bash", "tool_input": {}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 2. BLOCK cases (real-looking secrets)
# ---------------------------------------------------------------------------
def test_blocks_openai_style_key():
    """sk- prefix + 24+ chars = real-looking OpenAI key → block."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'API_KEY = "sk-' + "A" * 40 + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2
    assert "secret" in r.stderr.lower() or "leak" in r.stderr.lower()


def test_blocks_github_classic_token():
    """ghp_ + 36+ chars = GitHub classic token → block."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'TOKEN = "ghp_' + "B" * 36 + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2


def test_blocks_aws_access_key():
    """AKIA + exactly 16 uppercase alphanumeric chars = AWS access key → block.

    Must avoid placeholder markers like 'EXAMPLE', 'XXXX', 'TEST', 'YOUR'
    in the 16-char suffix or the placeholder check will suppress the match.
    """
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        # AKIA + 16 random-looking chars, no placeholder words
        "content": 'AWS_KEY = "AKIA' + "B9C2JK7M4PQR8STZ" + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2


def test_blocks_slack_token():
    """xoxb- + 20+ chars = Slack bot token → block."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'SLACK = "xoxb-' + "1" * 40 + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2


def test_blocks_jwt_token():
    """eyJ...eyJ...signature = JWT → block."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'JWT = "eyJ' + "A" * 20 + ".eyJ" + "B" * 20 + "." + "C" * 20 + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2


def test_blocks_secret_anywhere_in_payload():
    """Secret in a nested field (not just content) → still detected."""
    payload = {"tool_name": "Bash", "tool_input": {
        # Use chars that aren't placeholder markers (avoid 'xxxx', 'test', etc.)
        "command": 'echo "sk-' + "AbCdEf" * 8 + '"',
    }}
    r = _run(payload)
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 3. Placeholder allowlist (false-positive prevention)
# ---------------------------------------------------------------------------
def test_passes_when_token_is_placeholder():
    """sk-XXXX-style placeholder → not blocked."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'API_KEY = "sk-XXXXXXXXXXXXXXXXXXXXXXXX"',  # all X
    }}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_when_your_api_key_marker():
    """YOUR_API_KEY-style marker → not blocked."""
    payload = {"tool_name": "Write", "tool_input": {
        "file_path": "config.py",
        "content": 'os.environ["YOUR_API_KEY"]  # set this in Drive .secrets',
    }}
    r = _run(payload)
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 4. Fail-open
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin():
    env = dict(os.environ)
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{{{ not valid json",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 5. TestWiring
# ---------------------------------------------------------------------------
class TestWiring:
    def test_registered_in_pretooluse(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            cmds = [h.get("command", "") for h in grp.get("hooks", [])]
            for c in cmds:
                if "check-secret-leak" in c or "check_secret_leak" in c:
                    return
        raise AssertionError(
            "check_secret_leak must be registered on PreToolUse in settings.json"
        )

    def test_routed_through_hooks_runner(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            for h in grp.get("hooks", []):
                c = h.get("command", "")
                if "secret_leak" in c or "secret-leak" in c:
                    assert "hooks_runner" in c
                    return
        raise AssertionError("check_secret_leak not on PreToolUse")
