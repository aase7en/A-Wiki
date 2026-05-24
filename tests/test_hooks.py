"""
test_hooks.py — Hook integration tests for A-Wiki.

Phase 3 requirement: validate all 10 hooks run correctly
via hooks_runner.py orchestrator.
"""

from __future__ import annotations
import os
import sys
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from hooks_runner import get_hooks, run_hook, HOOKS_DIR


# ── get_hooks ──────────────────────────────────────────────────────────

class TestGetHooks:
    """get_hooks() returns sorted list of hook scripts."""

    def test_returns_list_of_strings(self):
        hooks = get_hooks()
        assert isinstance(hooks, list)
        for h in hooks:
            assert h.endswith(".py")
            assert isinstance(h, str)

    def test_excludes_init(self):
        hooks = get_hooks()
        assert "__init__.py" not in hooks

    def test_respects_hook_skip_env(self, monkeypatch):
        monkeypatch.setenv("HOOK_SKIP", "check_apikey.py,post_wiki_edit.py")
        hooks = get_hooks()
        assert "check_apikey.py" not in hooks
        assert "post_wiki_edit.py" not in hooks

    def test_all_hooks_exist_on_disk(self):
        hooks = get_hooks()
        for h in hooks:
            path = os.path.join(HOOKS_DIR, h)
            assert os.path.isfile(path), f"Hook missing: {path}"


# ── run_hook ───────────────────────────────────────────────────────────

class TestRunHook:
    """run_hook() invokes a hook with input JSON on stdin."""

    def test_unknown_hook_returns_pass(self):
        passed, msg = run_hook("nonexistent.py", {})
        assert passed
        assert msg == ""

    def test_known_hook_accepts_valid_input(self, hook_input):
        """check_apikey passes on clean input."""
        passed, msg = run_hook("check_apikey.py", hook_input)
        assert passed, f"check_apikey failed: {msg}"

    def test_hook_rejects_api_key_in_content(self, hook_input):
        """check_apikey blocks input with API key literals."""
        hook_input["message"]["content"] = (
            "curl -X POST https://api.openai.com/v1/chat/completions "
            "-H 'Authorization: Bearer sk-proj-fake-key-12345'"
        )
        passed, msg = run_hook("check_apikey.py", hook_input)
        assert not passed
        assert "API key" in msg or "api_key" in msg.lower()

    def test_hook_tolerates_missing_fields(self):
        """Hooks should not crash on sparse input."""
        passed, msg = run_hook("check_apikey.py", {"hello": "world"})
        # Should pass (missing fields aren't errors)
        assert passed

    def test_delegation_gate_blocks_no_session(self, hook_input):
        """check_delegation_gate blocks input without session end marker."""
        hook_input["message"]["content"] = (
            "git add . && git commit -m 'test' && git push"
        )
        passed, msg = run_hook("check_delegation_gate.py", hook_input)
        assert not passed
        assert "session" in msg.lower() or "protocol" in msg.lower()

    def test_delegation_gate_passes_with_end_session(self, hook_input):
        """check_delegation_gate passes when session end marker present."""
        hook_input["message"]["content"] = (
            "git add . && git commit -m 'test'\n"
            "session_end: true\n"
            "git push"
        )
        passed, msg = run_hook("check_delegation_gate.py", hook_input)
        assert passed, f"delegation gate failed: {msg}"

    def test_post_wiki_edit_does_not_crash(self, hook_input):
        """post_wiki_edit hook should run without error."""
        passed, msg = run_hook("post_wiki_edit.py", hook_input)
        assert passed, f"post_wiki_edit failed: {msg}"


# ── hooks_runner.py CLI (integration) ─────────────────────────────────

class TestHooksRunnerCLI:
    """Running hooks_runner.py directly as a subprocess."""

    RUNNER = str(REPO_ROOT / "scripts" / "hooks_runner.py")

    def test_stdin_json_passes(self):
        """echo '{}' | python3 hooks_runner.py -> exit 0."""
        result = subprocess.run(
            [sys.executable, self.RUNNER],
            input=json.dumps({"paths": {"wiki": "ok"}}),
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_specific_hook_by_name(self, hook_input):
        """python3 hooks_runner.py check_apikey < input."""
        proc = subprocess.run(
            [sys.executable, self.RUNNER, "check_apikey"],
            input=json.dumps(hook_input),
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr

    def test_specific_hook_without_py_suffix(self, hook_input):
        """python3 hooks_runner.py check_apikey (no .py) works."""
        proc = subprocess.run(
            [sys.executable, self.RUNNER, "check_apikey"],
            input=json.dumps(hook_input),
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr

    def test_hook_with_api_key_blocks(self):
        """hooks_runner.py check_apikey blocks API key content -> exit 2."""
        payload = {
            "message": {
                "content": "Bearer sk-proj-fake-key-abcdef123456"
            }
        }
        proc = subprocess.run(
            [sys.executable, self.RUNNER, "check_apikey"],
            input=json.dumps(payload),
            capture_output=True, text=True,
        )
        assert proc.returncode == 2, f"expected exit 2, got {proc.returncode}"

    def test_all_hooks_run_successfully(self, hook_input):
        """Running all hooks with clean input should pass."""
        proc = subprocess.run(
            [sys.executable, self.RUNNER],
            input=json.dumps(hook_input),
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr