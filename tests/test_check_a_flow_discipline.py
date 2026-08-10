"""Tests for scripts/hooks/check_a_flow_discipline.py — Iron Law #1 corollary.

Iron Law: NO IMPLEMENTATION WITHOUT PLAN APPROVED FIRST.
When A-Flow is active and phase is ask/design/plan, this hook BLOCKS
(exit 2) Edit/Write/MultiEdit. After IMPLEMENT, only files in
allowed_files (or all if allowed_files empty) may be edited.

Pattern A (subprocess) — mirrors tests/test_check_agent_claim_hook.py.

Coverage:
  - Pass when HOOK_SKIP override (substring)
  - Pass for non-gate tools (Read/Bash)
  - Pass when A-Flow not active (state.active=False)
  - Pass when phase=implement (post-PLAN)
  - Pass when editing .tmp/ files (state writes)
  - Pass for trivial edits (<5 char diff, comment-only, whitespace)
  - BLOCK when phase=ask/design/plan + non-trivial edit
  - BLOCK when phase=implement but file not in allowed_files
  - Fail-open on non-JSON stdin
  - TestWiring: registered on PreToolUse
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_a_flow_discipline.py"


def _run(payload: dict, *, env_extra: dict | None = None,
         focus_state: dict | None = None,
         focus_file: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env.pop("ZCODE_SESSION_ID", None)
    env.pop("CLAUDE_SESSION_ID", None)
    env.pop("CODEX_SESSION_ID", None)
    env.update(env_extra or {})

    # Seed focus state to a specific session-id file
    if focus_state is not None:
        sid = "hooktest_discipline"
        env["CLAUDE_SESSION_ID"] = sid
        fpath = focus_file or (REPO_ROOT / ".tmp" / f"a-focus-{sid}.json")
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(json.dumps(focus_state, ensure_ascii=False), encoding="utf-8")

    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


def _active_state(phase: str, *, allowed: list[str] | None = None) -> dict:
    return {
        "active": True, "skill": "a-flow", "goal": "test",
        "phase": phase,
        "allowed_files": allowed if allowed is not None else [],
        "started_ts": 1, "completed_phases": [], "notes": [],
    }


def _edit(file_path: str, *, old="x", new="y") -> dict:
    return {"tool_name": "Edit",
            "tool_input": {"file_path": file_path,
                           "old_string": old, "new_string": new}}


# ---------------------------------------------------------------------------
# 1. Pass cases (no enforcement)
# ---------------------------------------------------------------------------
def test_passes_when_hook_skip_exact():
    """HOOK_SKIP=check_a_flow_discipline → skip."""
    r = _run(_edit("scripts/lib/foo.py"),
             env_extra={"HOOK_SKIP": "check_a_flow_discipline"},
             focus_state=_active_state("ask"))
    assert r.returncode == 0


def test_passes_when_hook_skip_substring_in_comma_list():
    """HOOK_SKIP='check_a_flow_discipline,other' → skip (substring)."""
    r = _run(_edit("scripts/lib/foo.py"),
             env_extra={"HOOK_SKIP": "check_a_flow_discipline,other_hook"},
             focus_state=_active_state("ask"))
    assert r.returncode == 0


def test_passes_for_read_tool():
    r = _run({"tool_name": "Read",
              "tool_input": {"file_path": "scripts/lib/foo.py"}},
             focus_state=_active_state("ask"))
    assert r.returncode == 0


def test_passes_for_bash_tool():
    r = _run({"tool_name": "Bash", "tool_input": {"command": "echo hi"}},
             focus_state=_active_state("ask"))
    assert r.returncode == 0


def test_passes_when_a_flow_not_active():
    """No active session state → pass."""
    inactive = {"active": False, "skill": None, "goal": None, "phase": None,
                "allowed_files": [], "started_ts": None,
                "completed_phases": [], "notes": []}
    r = _run(_edit("scripts/lib/foo.py"), focus_state=inactive)
    assert r.returncode == 0


def test_passes_when_phase_is_implement():
    """Phase=implement (post-PLAN) → pass (allowed_files empty = permissive)."""
    r = _run(_edit("scripts/lib/foo.py"),
             focus_state=_active_state("implement", allowed=[]))
    assert r.returncode == 0


def test_passes_when_editing_tmp_files():
    """Editing .tmp/foo.json is always allowed (state writes)."""
    r = _run(_edit(".tmp/state.json"),
             focus_state=_active_state("ask"))
    assert r.returncode == 0


def test_passes_for_trivial_edit():
    """<5 char diff is trivial → auto-skip even in PRE-IMPLEMENT phase."""
    # diff of "x" → "y" is 0 net char change (both 1 char), diff_size=0 < 5
    r = _run(_edit("scripts/lib/foo.py", old="a", new="b"),
             focus_state=_active_state("ask"))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 2. BLOCK cases (PRE-IMPLEMENT + non-trivial edit)
# ---------------------------------------------------------------------------
def test_blocks_when_phase_is_ask_and_edit_is_significant():
    """Phase=ask + large edit → BLOCK."""
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "scripts/lib/foo.py",
                              "content": "def new_function():\n    return 42\n"}}
    r = _run(payload, focus_state=_active_state("ask"))
    assert r.returncode == 2


def test_blocks_when_phase_is_design_and_large_write():
    """Phase=design + Write → BLOCK."""
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "src/auth.py",
                              "content": "import os\n\ndef auth():\n    pass\n"}}
    r = _run(payload, focus_state=_active_state("design"))
    assert r.returncode == 2


def test_blocks_when_phase_is_plan_and_large_write():
    """Phase=plan + Write → BLOCK."""
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "src/main.py",
                              "content": "def main():\n    return 0\n"}}
    r = _run(payload, focus_state=_active_state("plan"))
    assert r.returncode == 2


def test_blocks_when_phase_implement_but_file_not_in_allowed():
    """Phase=implement + allowed_files=['src/foo.py'] + editing src/bar.py → BLOCK."""
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "src/bar.py",
                              "content": "def bar():\n    return 1\n"}}
    r = _run(payload, focus_state=_active_state("implement", allowed=["src/foo.py"]))
    assert r.returncode == 2


def test_passes_when_phase_implement_and_file_in_allowed():
    """Phase=implement + file in allowed_files → pass."""
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "src/foo.py",
                              "content": "def foo():\n    return 1\n"}}
    r = _run(payload, focus_state=_active_state("implement", allowed=["src/foo.py"]))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 3. Fail-open
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin():
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{{{ broken json",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert r.returncode == 0


def test_passes_when_file_path_missing():
    r = _run({"tool_name": "Edit", "tool_input": {}},
             focus_state=_active_state("ask"))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 4. TestWiring
# ---------------------------------------------------------------------------
class TestWiring:
    def test_registered_in_pretooluse_edit_matcher(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            if "Edit" not in grp.get("matcher", ""):
                continue
            cmds = [h.get("command", "") for h in grp.get("hooks", [])]
            for c in cmds:
                if "check-a-flow-discipline" in c or "check_a_flow_discipline" in c:
                    return
        raise AssertionError(
            "check_a_flow_discipline must be registered on Edit|Write|MultiEdit"
        )

    def test_routed_through_hooks_runner(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            for h in grp.get("hooks", []):
                c = h.get("command", "")
                if "a_flow_discipline" in c or "a-flow-discipline" in c:
                    assert "hooks_runner" in c
                    return
        raise AssertionError("check_a_flow_discipline not on PreToolUse")


# Cleanup any leftover state file
def _cleanup():
    sid = "hooktest_discipline"
    f = REPO_ROOT / ".tmp" / f"a-focus-{sid}.json"
    try:
        f.unlink()
    except FileNotFoundError:
        pass


import atexit
atexit.register(_cleanup)
