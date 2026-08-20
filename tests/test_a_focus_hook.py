"""Tests for the focus-guard hooks (A-Suite C5).

Design constraint these tests enforce: the PreToolUse guard is ADVISORY.
It must never exit 2 unless AWIKI_FOCUS_ENFORCE=1 is set explicitly.

Two independent reasons, both discovered while surveying the repo:
  1. .gemini/settings.json wires BeforeTool with matcher "*" to a bare
     `hooks_runner.py` (no hook name), so EVERY file in scripts/hooks/ runs on
     EVERY Gemini tool call. A new hook with an unguarded exit-2 path is a
     repo-wide hazard, not a local one.
  2. The DESIGN phase legitimately writes files (ADRs, specs, plan docs), so a
     phase gate that blocks writes has no safe allowlist — it would produce
     false blocks on exactly the work it is meant to protect.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_a_focus.py"
STOP_HOOK = REPO_ROOT / "scripts" / "hooks" / "a_focus_stop.py"


def run_hook(hook: Path, payload: dict, env_extra: dict | None = None, focus_dir: Path | None = None):
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env["CLAUDE_SESSION_ID"] = "hooktest"
    if focus_dir is not None:
        env["AWIKI_FOCUS_DIR"] = str(focus_dir)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


def write_focus(focus_dir: Path, **over):
    state = {
        "skill": "a-plan", "goal": "design the dashboard", "phase": "ask",
        "phases_done": [], "session_id": "hooktest",
    }
    state.update(over)
    focus_dir.mkdir(parents=True, exist_ok=True)
    (focus_dir / "a-focus-hooktest.json").write_text(
        json.dumps(state, ensure_ascii=False), encoding="utf-8"
    )
    return state


EDIT_PY = {"tool_name": "Edit", "tool_input": {"file_path": "scripts/thing.py"}}


class TestPreToolUseGuard:
    def test_no_focus_file_is_a_silent_pass(self, tmp_path):
        r = run_hook(HOOK, EDIT_PY, focus_dir=tmp_path)
        assert r.returncode == 0
        assert r.stderr.strip() == ""

    def test_off_phase_write_warns_but_does_not_block(self, tmp_path):
        write_focus(tmp_path, phase="ask")
        r = run_hook(HOOK, EDIT_PY, focus_dir=tmp_path)
        assert r.returncode == 0, "guard must be advisory by default"
        assert "ask" in r.stderr

    def test_on_phase_write_is_silent(self, tmp_path):
        write_focus(tmp_path, phase="implement")
        r = run_hook(HOOK, EDIT_PY, focus_dir=tmp_path)
        assert r.returncode == 0
        assert r.stderr.strip() == ""

    @pytest.mark.parametrize("path", [
        "docs/adr/001-thing.md", "wiki/context/notes.md",
        ".tmp/scratch.json", "PLAN.md",
    ])
    def test_design_phase_writing_docs_is_never_flagged(self, tmp_path, path):
        """ASK/DESIGN legitimately produce ADRs, specs and plans."""
        write_focus(tmp_path, phase="design")
        r = run_hook(HOOK, {"tool_name": "Write", "tool_input": {"file_path": path}},
                     focus_dir=tmp_path)
        assert r.returncode == 0
        assert r.stderr.strip() == ""

    def test_enforce_env_upgrades_the_warning_to_a_block(self, tmp_path):
        write_focus(tmp_path, phase="ask")
        r = run_hook(HOOK, EDIT_PY, {"AWIKI_FOCUS_ENFORCE": "1"}, focus_dir=tmp_path)
        assert r.returncode == 2
        assert "ask" in r.stderr

    def test_non_write_tools_are_ignored(self, tmp_path):
        write_focus(tmp_path, phase="ask")
        for tool in ("Read", "Grep", "Glob", "Bash"):
            r = run_hook(HOOK, {"tool_name": tool, "tool_input": {}}, focus_dir=tmp_path)
            assert r.returncode == 0
            assert r.stderr.strip() == ""

    def test_hook_skip_bypasses_visibly(self, tmp_path):
        write_focus(tmp_path, phase="ask")
        r = run_hook(HOOK, EDIT_PY, {"HOOK_SKIP": "check_a_focus"}, focus_dir=tmp_path)
        assert r.returncode == 0

    def test_corrupt_focus_file_fails_open(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "a-focus-hooktest.json").write_text("{not json", encoding="utf-8")
        r = run_hook(HOOK, EDIT_PY, focus_dir=tmp_path)
        assert r.returncode == 0

    def test_malformed_stdin_fails_open(self, tmp_path):
        env = dict(os.environ); env["AWIKI_FOCUS_DIR"] = str(tmp_path)
        r = subprocess.run([sys.executable, str(HOOK)], input="not json",
                           capture_output=True, text=True, env=env,
                           cwd=str(REPO_ROOT), timeout=30)
        assert r.returncode == 0

    def test_thai_output_does_not_crash_on_cp874(self, tmp_path):
        """Windows consoles default to cp874 — the UTF-8 preamble is mandatory."""
        write_focus(tmp_path, phase="ask", goal="ออกแบบ dashboard พลังงาน")
        env = {"PYTHONIOENCODING": "cp874"}
        r = run_hook(HOOK, EDIT_PY, env, focus_dir=tmp_path)
        assert r.returncode == 0
        assert "Traceback" not in r.stderr


class TestStopHook:
    def test_no_focus_is_a_silent_pass(self, tmp_path):
        r = run_hook(STOP_HOOK, {}, focus_dir=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_incomplete_focus_is_reported_on_stdout(self, tmp_path):
        write_focus(tmp_path, phase="design", phases_done=["ask"])
        r = run_hook(STOP_HOOK, {}, focus_dir=tmp_path)
        assert r.returncode == 0, "Stop hook must never block the session ending"
        # Direct-wired, so stdout is what reaches the user.
        assert "design" in r.stdout

    def test_completed_focus_is_not_nagged_about(self, tmp_path):
        write_focus(tmp_path, phase=None, phases_done=list(
            ["ask", "design", "plan", "implement", "review", "debug", "test"]),
            complete=True)
        r = run_hook(STOP_HOOK, {}, focus_dir=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_corrupt_state_fails_open(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "a-focus-hooktest.json").write_text("{bad", encoding="utf-8")
        r = run_hook(STOP_HOOK, {}, focus_dir=tmp_path)
        assert r.returncode == 0


class TestWiring:
    def test_pretooluse_guard_is_routed_through_registry_event_sweep(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = [
            h.get("command", "")
            for grp in cfg["hooks"].get("PreToolUse", [])
            for h in grp.get("hooks", [])
        ]
        assert any(
            "hooks_runner.py --provider claude --event PreToolUse" in c
            for c in commands
        )
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
        import registry
        entry = registry.HOOK_REGISTRY["check_a_focus"]
        assert "PreToolUse" in entry["events"]
        assert entry["classification"] == "hard"

    def test_stop_hook_is_wired_via_registry_event_sweep_with_context(self):
        """Phase 6 keeps Stop advisory output visible through runner context."""
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        stop_cmds = [
            h.get("command", "")
            for grp in cfg["hooks"].get("Stop", [])
            for h in grp.get("hooks", [])
        ]
        assert any(
            "hooks_runner.py --provider claude --event Stop" in c
            for c in stop_cmds
        ), "Stop must enter the canonical registry event sweep"
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
        import registry
        entry = registry.HOOK_REGISTRY["a_focus_stop"]
        assert "Stop" in entry["events"]
        assert entry["allow_context_stdout"] is True
