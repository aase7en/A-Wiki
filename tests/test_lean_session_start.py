"""
Tests for lazy SessionStart (token-save) — AWIKI_LEAN_SESSION_START=1.

Two layers:
1. session_start.py — run_steps(repo_root, lean) keeps only essential steps
   (git pull, cost-gate cleanup, TODOs) and skips informational emitters.
2. .claude/hooks/session-start-*.sh — informational shell hooks early-exit
   silently when the flag is set.

Default (flag unset) behavior must be unchanged: all steps run.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_START = REPO_ROOT / "scripts" / "hooks" / "session_start.py"

spec = importlib.util.spec_from_file_location("session_start_lean_mod", SESSION_START)
assert spec and spec.loader
session_start = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = session_start
spec.loader.exec_module(session_start)


ESSENTIAL = ["git_pull", "clean_stale_cost_declarations", "show_todos"]
SKIPPABLE = [
    "check_wiki_freshness",
    "check_api_keys",
    "maybe_update_model_intel",
    "show_model_tier_hint",
    "check_model_scout_freshness",
    "run_vendor_watch",
]


class TestIsLean:
    def test_default_is_false(self, monkeypatch):
        monkeypatch.delenv("AWIKI_LEAN_SESSION_START", raising=False)
        assert session_start.is_lean() is False

    def test_enabled_by_env(self, monkeypatch):
        monkeypatch.setenv("AWIKI_LEAN_SESSION_START", "1")
        assert session_start.is_lean() is True

    def test_zero_means_off(self, monkeypatch):
        monkeypatch.setenv("AWIKI_LEAN_SESSION_START", "0")
        assert session_start.is_lean() is False


class TestRunSteps:
    def _record_all(self, monkeypatch):
        called: list[str] = []
        for name in ESSENTIAL + SKIPPABLE:
            def _rec(*a, _n=name, **k):
                called.append(_n)
            monkeypatch.setattr(session_start, name, _rec)
        return called

    def test_full_mode_runs_everything(self, monkeypatch):
        called = self._record_all(monkeypatch)
        session_start.run_steps("fake-root", lean=False)
        assert set(called) == set(ESSENTIAL + SKIPPABLE)

    def test_lean_mode_runs_only_essentials(self, monkeypatch):
        called = self._record_all(monkeypatch)
        session_start.run_steps("fake-root", lean=True)
        assert set(called) == set(ESSENTIAL)

    def test_lean_mode_announces_itself_once(self, monkeypatch, capsys):
        self._record_all(monkeypatch)
        session_start.run_steps("fake-root", lean=True)
        err = capsys.readouterr().err
        assert "AWIKI_LEAN_SESSION_START" in err
        assert err.count("\n") <= 2, "lean announcement must stay ~1 line (token-save)"

    def test_full_mode_has_no_lean_announcement(self, monkeypatch, capsys):
        self._record_all(monkeypatch)
        session_start.run_steps("fake-root", lean=False)
        assert "AWIKI_LEAN_SESSION_START" not in capsys.readouterr().err


LEAN_GUARDED_SCRIPTS = [
    ".claude/hooks/session-start-binary-scan.sh",
    ".claude/hooks/session-start-apikey-check.sh",
    ".claude/hooks/build-pharmacy-db.sh",
    ".claude/hooks/wiki-context-check.sh",
]


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
class TestShellHookLeanGuard:
    @pytest.mark.parametrize("script", LEAN_GUARDED_SCRIPTS)
    def test_lean_flag_exits_silently(self, script):
        proc = subprocess.run(
            ["bash", script],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env={**os.environ, "AWIKI_LEAN_SESSION_START": "1"},
            cwd=str(REPO_ROOT),
            timeout=30,
        )
        assert proc.returncode == 0, f"{script}: rc={proc.returncode} err={proc.stderr}"
        assert proc.stdout.strip() == "", f"{script} stdout not silent: {proc.stdout}"
        assert proc.stderr.strip() == "", f"{script} stderr not silent: {proc.stderr}"

    @pytest.mark.parametrize("script", LEAN_GUARDED_SCRIPTS)
    def test_guard_is_if_form_not_and_chain(self, script):
        """`[ cond ] && exit 0` breaks under `set -e` when cond is false — require if-form."""
        body = (REPO_ROOT / script).read_text(encoding="utf-8")
        assert "AWIKI_LEAN_SESSION_START" in body, f"{script} missing lean guard"
        for line in body.splitlines():
            if "AWIKI_LEAN_SESSION_START" in line and "&&" in line and "exit" in line:
                pytest.fail(f"{script}: use if-form guard, not `&& exit 0` (set -e trap): {line}")
