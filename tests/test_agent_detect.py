"""Tests for scripts/lib/agent_detect.py.

Covers each agent fingerprint (claude, codex, zcode, gemini, cursor,
windsurf, cline, antigravity, hermes, kilo, copilot), prefix matches,
first-hit-wins ordering, and fail-soft behavior.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from agent_detect import detect_agent  # noqa: E402


# ---------- happy paths (exact-match env vars) ----------

def test_claude_via_project_dir():
    assert detect_agent({"CLAUDE_PROJECT_DIR": "/x"}) == "claude"


def test_claude_via_claudecode():
    assert detect_agent({"CLAUDECODE": "1"}) == "claude"


def test_codex_via_home():
    assert detect_agent({"CODEX_HOME": "/y"}) == "codex"


def test_codex_via_agent():
    assert detect_agent({"CODEX_AGENT": "research"}) == "codex"


def test_zcode_via_session():
    assert detect_agent({"ZCODE_SESSION": "abc"}) == "zcode"


def test_zcode_via_cli():
    assert detect_agent({"ZCODE_CLI": "1"}) == "zcode"


def test_gemini_via_cli():
    assert detect_agent({"GEMINI_CLI": "1"}) == "gemini"


def test_gemini_via_model():
    assert detect_agent({"GEMINI_MODEL": "gemini-pro"}) == "gemini"


def test_cursor_via_trace_dir():
    assert detect_agent({"CURSOR_TRACE_DIR": "/t"}) == "cursor"


def test_cursor_via_debug():
    assert detect_agent({"CURSOR_DEBUG": "1"}) == "cursor"


def test_windsurf_via_user_data():
    assert detect_agent({"WINDSURF_USER_DATA_DIR": "/w"}) == "windsurf"


def test_windsurf_via_machine_guid():
    assert detect_agent({"WINDSURF_MACHINE_GUID": "abc"}) == "windsurf"


def test_hermes_via_home():
    assert detect_agent({"HERMES_AGENT_HOME": "/h"}) == "hermes"


def test_hermes_via_config():
    assert detect_agent({"HERMES_CONFIG": "/h/cfg"}) == "hermes"


def test_copilot_via_integration_id():
    assert detect_agent({"COPILOT_INTEGRATION_ID": "x"}) == "copilot"


def test_copilot_via_token():
    assert detect_agent({"GITHUB_COPILOT_TOKEN": "tid=abc"}) == "copilot"


# ---------- prefix matches ----------

def test_cline_prefix_any_key():
    assert detect_agent({"CLINE_RULES_DIR": "/r"}) == "cline"
    assert detect_agent({"CLINE_WORKSPACE": "/w"}) == "cline"


def test_antigravity_prefix():
    assert detect_agent({"ANTIGRAVITY_HOME": "/a"}) == "antigravity"


def test_kilo_prefix():
    assert detect_agent({"KILO_CONFIG": "/k"}) == "kilo"


# ---------- ordering + edge cases ----------

def test_first_hit_wins_when_multiple_agents_present():
    # CLAUDE_PROJECT_DIR is checked before CODEX_HOME → claude wins.
    env = {"CLAUDE_PROJECT_DIR": "/x", "CODEX_HOME": "/y"}
    assert detect_agent(env) == "claude"


def test_no_fingerprint_returns_none():
    assert detect_agent({"PATH": "/usr/bin", "HOME": "/h"}) is None


def test_empty_env_returns_none():
    assert detect_agent({}) is None


def test_defaults_to_os_environ_when_no_arg():
    # Smoke test: function should accept no args and return str or None
    # without raising. We don't assert on the value because CI environment
    # may set some of these vars.
    result = detect_agent()
    assert result is None or isinstance(result, str)


# ---------- fail-soft ----------

def test_does_not_raise_on_unusual_env_type():
    # Passing a non-dict mapping-like object should fail-soft to None,
    # not raise (detection must never crash the calling hook).
    class BrokenMapping:
        def __contains__(self, k): raise RuntimeError("boom")
        def __iter__(self): raise RuntimeError("boom")
    # BrokenMapping doesn't satisfy Mapping protocol; detect_agent uses
    # `key in env` and `any(k.startswith(...) for k in env)` — both should
    # fail-soft. The function's try/except must swallow the error.
    result = detect_agent(BrokenMapping())  # type: ignore[arg-type]
    assert result is None
