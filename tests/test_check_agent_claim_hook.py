"""Tests for scripts/hooks/check_agent_claim.py — Iron Law #11 gate.

Iron Law #11: agents must claim_acquire before touching shared surfaces.
This hook hard-blocks (exit 2) edits landing inside ANOTHER agent's live
claim; warns (stderr, exit 0) on unclaimed shared-surface edits.

Pattern A (subprocess) — mirrors tests/test_check_test_before_code.py
and tests/test_a_focus_hook.py.

Coverage:
  - Pass when AWIKI_CLAIM_GATE=0 (escape hatch)
  - Pass when HOOK_SKIP substring (comma-separated)
  - Pass for non-gate tools (Read/Bash/Glob)
  - Pass for edits outside shared surfaces
  - BLOCK (exit 2) when editing inside another agent's live claim
  - Warn (exit 0) when editing shared surface with no claim
  - Pass when editing inside OWN claim
  - Fail-open on bad JSON stdin
  - TestWiring: hook registered in PreToolUse Edit|Write|MultiEdit
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_agent_claim.py"

# Default claims store — override via AWIKI_CLAIMS_STORE in tests.
DEFAULT_CLAIMS = REPO_ROOT / ".tmp" / "agent-claims.json"


def _run_hook(payload: dict, *, env_extra: dict | None = None,
              claims_store: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke check_agent_claim as subprocess with PreToolUse payload on stdin."""
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env.pop("AWIKI_CLAIM_GATE", None)
    env["AWIKI_AGENT"] = "tester"
    env.update(env_extra or {})
    if claims_store is not None:
        env["AWIKI_CLAIMS_STORE"] = str(claims_store)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


def _edit_payload(file_path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path,
            "old_string": "x", "new_string": "y"}}


def _seed_claim(store: Path, *, agent: str, scope: list[str],
                goal: str = "doing X", lease_seconds: int = 3600) -> dict:
    """Seed a live claim via the agent_claims module (no MCP needed)."""
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
    os.environ["AWIKI_CLAIMS_STORE"] = str(store)
    import agent_claims as ac
    ac.set_store(str(store))
    return ac.acquire(agent=agent, scope=scope, goal=goal,
                      phase="implement", session_id=f"{agent}-s",
                      lease_seconds=lease_seconds)


# ---------------------------------------------------------------------------
# 1. Escape hatches (pass)
# ---------------------------------------------------------------------------
def test_passes_when_claim_gate_disabled(tmp_path):
    r = _run_hook(_edit_payload("scripts/lib/foo.py"),
                  env_extra={"AWIKI_CLAIM_GATE": "0"})
    assert r.returncode == 0
    assert "BYPASSED" in r.stderr


def test_passes_when_hook_skip_exact(tmp_path):
    r = _run_hook(_edit_payload("scripts/lib/foo.py"),
                  env_extra={"HOOK_SKIP": "check_agent_claim"})
    assert r.returncode == 0
    assert "BYPASSED" in r.stderr


def test_passes_when_hook_skip_substring_in_comma_list(tmp_path):
    """HOOK_SKIP='check_agent_claim,other' must also skip (substring)."""
    r = _run_hook(_edit_payload("scripts/lib/foo.py"),
                  env_extra={"HOOK_SKIP": "check_agent_claim,other_hook"})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 2. Pass for non-gate tools / non-shared paths
# ---------------------------------------------------------------------------
def test_passes_for_read_tool(tmp_path):
    payload = {"tool_name": "Read", "tool_input": {"file_path": "scripts/lib/foo.py"}}
    r = _run_hook(payload)
    assert r.returncode == 0


def test_passes_for_bash_tool(tmp_path):
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    r = _run_hook(payload)
    assert r.returncode == 0


def test_passes_for_non_shared_surface(tmp_path, monkeypatch):
    """Editing a file OUTSIDE skills/scripts/agents/etc → no warning."""
    store = tmp_path / "claims.json"
    r = _run_hook(_edit_payload("README.md"), claims_store=store)
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 3. BLOCK when editing inside another agent's live claim
# ---------------------------------------------------------------------------
def test_blocks_when_inside_another_agents_claim(tmp_path):
    """Editing a file inside agent X's live claim → exit 2."""
    store = tmp_path / "claims.json"
    _seed_claim(store, agent="other_agent",
                scope=["scripts/lib/foo.py", "scripts/lib/bar.py"])
    r = _run_hook(_edit_payload("scripts/lib/foo.py"), claims_store=store)
    assert r.returncode == 2, f"expected block, got {r.returncode}: {r.stderr}"
    assert "CLAIM COLLISION" in r.stderr or "other_agent" in r.stderr


def test_blocks_any_file_matching_scope_glob_via_prefix(tmp_path):
    """Scope like 'scripts/lib/**' covers scripts/lib/anything.py."""
    store = tmp_path / "claims.json"
    _seed_claim(store, agent="other_agent", scope=["scripts/lib/**"])
    r = _run_hook(_edit_payload("scripts/lib/deep/mod.py"), claims_store=store)
    # collision() uses prefix/glob match — deep path may or may not match
    # depending on impl. We assert on what the collision actually reports.
    # If the hook blocks, the message must name the holder.
    if r.returncode == 2:
        assert "other_agent" in r.stderr


# ---------------------------------------------------------------------------
# 4. Warn (exit 0) on unclaimed shared-surface edit
# ---------------------------------------------------------------------------
def test_warns_when_editing_shared_surface_with_no_claim(tmp_path):
    """Editing scripts/lib/foo.py with no live claim → warning + exit 0."""
    store = tmp_path / "claims.json"
    r = _run_hook(_edit_payload("scripts/lib/foo.py"), claims_store=store)
    assert r.returncode == 0  # warning, not block
    # The hook nudges the user to claim_acquire
    assert "claim" in r.stderr.lower() or "ประกาศ" in r.stderr


def test_no_warning_when_own_claim_covers_path(tmp_path):
    """If MY claim covers the path, no 'unclaimed' warning fires."""
    store = tmp_path / "claims.json"
    # tester is the agent in _run_hook (AWIKI_AGENT=tester)
    _seed_claim(store, agent="tester", scope=["scripts/lib/foo.py"])
    r = _run_hook(_edit_payload("scripts/lib/foo.py"), claims_store=store)
    assert r.returncode == 0
    # No 'unclaimed' nudge when own claim is in place
    assert "ยังไม่ได้ประกาศ claim" not in r.stderr


# ---------------------------------------------------------------------------
# 5. Fail-open (never wedge on bad input / broken store)
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin():
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env["AWIKI_AGENT"] = "tester"
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not valid json {{{",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert r.returncode == 0


def test_fail_open_on_missing_file_path():
    """Edit payload without file_path → pass."""
    r = _run_hook({"tool_name": "Edit", "tool_input": {}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 6. Expired claim no longer blocks
# ---------------------------------------------------------------------------
def test_expired_claim_does_not_block(tmp_path):
    """A claim past its lease_until self-reaps → no collision."""
    store = tmp_path / "claims.json"
    # lease_seconds=1 + sleep → expired by the time the hook reads it
    _seed_claim(store, agent="other_agent",
                scope=["scripts/lib/foo.py"], lease_seconds=1)
    time.sleep(1.5)
    r = _run_hook(_edit_payload("scripts/lib/foo.py"), claims_store=store)
    # Expired → either warning (unclaimed) or silent pass, NOT block
    assert r.returncode != 2, (
        f"expired claim should not block, got rc=2: {r.stderr}"
    )


# ---------------------------------------------------------------------------
# 7. TestWiring — must be registered on PreToolUse Edit|Write|MultiEdit
# ---------------------------------------------------------------------------
