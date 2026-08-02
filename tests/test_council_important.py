"""tests/test_council_important.py — A-Council 2026-08-02 important findings.

Covers the gaps the test-engineer + code-reviewer personas flagged after the
3 critical fixes landed. Each test is a char-test or contract addition that
would have caught the gap on its own.

Findings covered (see A-Council thread m1785590361720-84b214):
  - lease-expiry reclaim path untested (test-eng #3) → contract test
  - a_flow_state focus interop normalization untested (test-eng #4) → char-test
  - prod validates inputs mock accepts → Liskov divergence (code-review #3)
  - FORBIDDEN_IN_PORTS expansion needs coverage (security-auditor)
  - hook Edit/new_string branch untested (test-eng #9)
  - hook Windows backslash path untested (test-eng #10)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import neural_spine_mcp as nsmcp  # noqa: E402
from adapters.taskboard import InMemoryTaskBoardAdapter, JsonlTaskBoardAdapter  # noqa: E402


# Re-use the autouse-style sandbox by re-declaring a minimal version here.
@pytest.fixture(autouse=True)
def _sandbox(tmp_path, monkeypatch):
    monkeypatch.setenv("AWIKI_DATA_DIR", str(tmp_path))
    import agent_claims
    agent_claims.set_store(tmp_path / "claims.json")
    yield tmp_path
    try:
        agent_claims.set_store(None)
    except Exception:
        pass


# ── test-eng #3: lease-expiry reclaim must be claimable by another agent ─
def test_taskboard_expired_lease_can_be_reclaimed(tmp_path):
    """The whole point of the TTL lease: a crashed agent's task can be
    re-claimed after expiry. Prod honours this via is_expired(); the mock
    must too, or the contract suite can't detect a regression."""
    import time
    adapter = JsonlTaskBoardAdapter(tmp_path / "tasks.json")
    tid = adapter.add(goal="abandoned")
    # First agent claims with a 0-minute lease → expires immediately.
    assert adapter.claim(tid, claimant="crashed", lease_minutes=0) is True
    time.sleep(1.1)  # ensure the timestamp moves past the 0-second TTL
    # A DIFFERENT agent must be able to reclaim it now.
    reclaimed = adapter.claim(tid, claimant="rescuer", lease_minutes=30)
    assert reclaimed is True, \
        "expired-lease task was not reclaimable — Iron Law #11 self-reap broken"


# ── test-eng #4: a_flow_state interop normalization on read ─────────────
def test_focus_read_normalizes_a_flow_state_key_spelling(tmp_path, monkeypatch):
    """If a_flow_state.py wrote the focus file with its own key spelling
    (completed_phases / started_ts / active), focus_get must normalise to
    the keys THIS module uses (phases_done / started_at / complete), else
    the Stop hook nags about a finished run."""
    monkeypatch.setenv("ZCODE_SESSION_ID", "interop-test")
    # Simulate a_flow_state writing the file directly
    focus_path = tmp_path / "a-focus-interop-test.json"
    focus_path.write_text(json.dumps({
        "skill": "a-plan",
        "phase": "implement",
        "completed_phases": ["ask", "design"],
        "started_ts": 1000,
        "active": False,  # a_flow_state's "done" spelling
    }), encoding="utf-8")
    monkeypatch.setattr(nsmcp, "_FOCUS_DIR", tmp_path)
    state = nsmcp.TOOLS["focus_get"]["fn"]({})
    assert state is not None, "focus_get returned None for a file a_flow_state wrote"
    # Normalised keys must be present
    assert state.get("phases_done") == ["ask", "design"]
    assert state.get("started_at") == 1000
    assert state.get("complete") is True


# ── code-review #3: prod validates, mock must too (Liskov) ──────────────
def test_taskboard_update_invalid_status_rejected_by_both_adapters(tmp_path):
    """The contract suite's whole point (R10 mitigation). Both adapters
    must reject the SAME bad input. Prod enforces VALID_STATUSES; the mock
    must mirror it so a divergence cannot hide."""
    adapters = [
        InMemoryTaskBoardAdapter(),
        JsonlTaskBoardAdapter(tmp_path / "tasks.json"),
    ]
    for adapter in adapters:
        tid = adapter.add(goal="x")
        with pytest.raises(ValueError, match="invalid status"):
            adapter.update(tid, status="not-a-real-status")


def test_taskboard_release_on_nonexistent_returns_false_both_adapters(tmp_path):
    """test-eng #2: release guard clauses were dead-untested. Pin them on
    BOTH adapters."""
    adapters = [
        InMemoryTaskBoardAdapter(),
        JsonlTaskBoardAdapter(tmp_path / "tasks.json"),
    ]
    for adapter in adapters:
        assert adapter.release("does-not-exist") is False


def test_taskboard_release_on_done_task_returns_false_both_adapters(tmp_path):
    """A done task cannot be released back to todo. Pin on both adapters."""
    adapters = [
        InMemoryTaskBoardAdapter(),
        JsonlTaskBoardAdapter(tmp_path / "tasks.json"),
    ]
    for adapter in adapters:
        tid = adapter.add(goal="x")
        adapter.update(tid, status="done")
        assert adapter.release(tid) is False


# ── security-auditor: FORBIDDEN_IN_PORTS now covers the RCE surface ─────
_hook_spec = importlib.util.spec_from_file_location(
    "chk_hex_important", REPO_ROOT / "scripts" / "hooks" / "check_hexagonal_boundary.py",
)
chk = importlib.util.module_from_spec(_hook_spec)
_hook_spec.loader.exec_module(chk)


@pytest.mark.parametrize("dangerous_import", [
    "import os",
    "import pickle",
    "import ctypes",
    "import marshal",
    "import shutil",
    "import socket",
    "import importlib",
    "from os import system",
])
def test_hook_blocks_high_risk_primitives(dangerous_import):
    """The expanded FORBIDDEN list must catch RCE-adjacent imports a port
    has no business pulling in."""
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/lib/ports/evil.py",
            "content": dangerous_import,
        },
    }))
    try:
        rc = chk.main()
    finally:
        sys.stdin = old_stdin
    assert rc == 2, f"expected block for: {dangerous_import}"


# ── test-eng #9: hook Edit/new_string branch ────────────────────────────
def test_hook_blocks_violation_in_edit_new_string_field():
    """Edit/MultiEdit carry the new content in `new_string`, not `content`.
    That branch was uncovered — pin it."""
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "scripts/lib/ports/x.py",
            "new_string": "import sqlite3\n",
        },
    }))
    try:
        rc = chk.main()
    finally:
        sys.stdin = old_stdin
    assert rc == 2


# ── test-eng #10: Windows backslash path handling ───────────────────────
def test_hook_handles_windows_backslash_paths():
    """Windows tools emit backslash paths. _is_in_ports_dir must still
    recognise them (the repo runs on win32)."""
    assert chk._is_in_ports_dir("scripts\\lib\\ports\\x.py") is True
    assert chk._is_in_ports_dir("scripts\\lib\\adapters\\x.py") is False


def test_hook_blocks_backslash_path_violation():
    """End-to-end: a Windows-style path to a ports file with a violation
    must be blocked."""
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts\\lib\\ports\\x.py",
            "content": "import sqlite3",
        },
    }))
    try:
        rc = chk.main()
    finally:
        sys.stdin = old_stdin
    assert rc == 2
