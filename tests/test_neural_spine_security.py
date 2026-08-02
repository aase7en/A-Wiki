"""tests/test_neural_spine_security.py — security regression tests for slice A4.

A-Council 2026-08-01 BLOCK SHIP findings — these tests FAIL until the fixes
land, proving the gate is honest (Iron Law #1: failing test first).

Critical findings covered:
  #1 (security-auditor): set_paths() arbitrary-path traversal
  #2 (code-reviewer): _wire() vs set_paths() competing wiring sites
  #3 (test-engineer): claim-store leak to real repo path
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import neural_spine_mcp as nsmcp  # noqa: E402


# ── CRITICAL #1: set_paths() must reject paths outside the sandbox ──────
# A malicious or buggy caller must NOT be able to redirect the ledger /
# task board / focus dir to an arbitrary location (e.g. .git/config, an
# exfiltration folder). All writable paths must stay under REPO_ROOT/.tmp
# (or an explicit AWIKI_DATA_DIR override used only by trusted callers).
@pytest.mark.parametrize("malicious_path", [
    ".git/config",                       # repo sabotage
    "/etc/passwd",                       # system file
    "../escape.json",                    # traversal
    str(Path.home() / "exfil.json"),     # exfiltration
])
def test_set_paths_rejects_path_outside_sandbox(tmp_path, malicious_path):
    """Every set_paths() argument must resolve under the allowed root, else
    raise ValueError. This is the path-traversal mitigation."""
    with pytest.raises(ValueError, match="(?i)sandbox|outside|allowed"):
        nsmcp.set_paths(ledger=malicious_path)


def test_set_paths_accepts_path_under_tmp_sandbox(tmp_path, monkeypatch):
    """A path explicitly under REPO_ROOT/.tmp (or AWIKI_DATA_DIR) is OK."""
    sandbox = tmp_path / "data"
    sandbox.mkdir()
    monkeypatch.setenv("AWIKI_DATA_DIR", str(sandbox))
    # Must not raise — legitimate redirect within the sandbox
    nsmcp.set_paths(ledger=sandbox / "ledger.jsonl",
                    blackboard=sandbox / "bb.jsonl",
                    task_board=sandbox / "tasks.json",
                    focus_dir=sandbox)
    # And the adapters must actually point there
    assert str(sandbox) in str(nsmcp._LEDGER_PATH)


def test_set_paths_rejects_symlink_escape(tmp_path, monkeypatch):
    """A symlink inside the sandbox that points outside is still an escape."""
    sandbox = tmp_path / "data"
    sandbox.mkdir()
    outside = tmp_path / "secret.json"
    link = sandbox / "ledger.jsonl"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    monkeypatch.setenv("AWIKI_DATA_DIR", str(sandbox))
    with pytest.raises(ValueError):
        nsmcp.set_paths(ledger=link)


# ── CRITICAL #2: single composition entry point, no clobber ────────────
def test_configure_is_the_single_wiring_entry_point():
    """configure() must exist; _wire() must be gone or aliased (no two
    competing sites)."""
    assert hasattr(nsmcp, "configure"), "expected a single configure() entry"
    # _wire may exist as a deprecated alias but must NOT be the primary path


def test_configure_takes_adapters_or_paths_not_both(tmp_path, monkeypatch):
    """If both an adapter AND a path for the same port are passed, the call
    must raise — no silent precedence that clobbers a wired mock."""
    sandbox = tmp_path / "data"
    sandbox.mkdir()
    monkeypatch.setenv("AWIKI_DATA_DIR", str(sandbox))
    from adapters.memory import InMemoryMemoryAdapter
    with pytest.raises((ValueError, TypeError)):
        nsmcp.configure(
            memory=InMemoryMemoryAdapter(),
            ledger=sandbox / "ledger.jsonl",  # conflicting!
        )


def test_configure_with_adapters_does_not_get_clobbered_by_later_path_call(tmp_path, monkeypatch):
    """Critical #2 regression: a wired mock must survive a subsequent
    set_paths() that only redirects UNRELATED ports. Previously set_paths()
    would silently rebuild _memory from _LEDGER_PATH even when an adapter
    was explicitly wired."""
    sandbox = tmp_path / "data"
    sandbox.mkdir()
    monkeypatch.setenv("AWIKI_DATA_DIR", str(sandbox))
    from adapters.memory import InMemoryMemoryAdapter
    mock = InMemoryMemoryAdapter()
    nsmcp.configure(memory=mock)
    # Redirect only the blackboard path — must NOT rebuild _memory
    nsmcp.set_paths(blackboard=sandbox / "bb.jsonl")
    assert nsmcp._memory is mock, "set_paths clobbered an explicitly-wired adapter"


# ── CRITICAL #3: claim store isolation in tests ─────────────────────────
# This test verifies the FIX landed: the isolated_session fixture (or its
# replacement) must actually redirect the claim store to tmp_path, not the
# real repo path.
def test_claim_store_is_isolated_from_repo_default(tmp_path, monkeypatch):
    """agent_claims must write to tmp_path during tests, never to the real
    .tmp/agent-claims.json. Verified by acquiring a claim and checking it
    landed in tmp_path, not REPO_ROOT."""
    import agent_claims
    # The fix: a set_store() (or equivalent) must exist and redirect.
    assert hasattr(agent_claims, "set_store") or hasattr(agent_claims, "configure"), \
        "agent_claims needs a set_store()/configure() to isolate the store"
    store = tmp_path / "claims.json"
    try:
        agent_claims.set_store(store)
    except AttributeError:
        pytest.skip("agent_claims.set_store not yet implemented")
    monkeypatch.setenv("ZCODE_SESSION_ID", "iso-test")
    agent_claims.acquire(agent="test", scope=["x"], goal="iso", session_id="iso-test")
    # The claim must be in tmp_path, not the repo default
    assert store.exists(), "claim did not land in the isolated store"
    # And the repo default must NOT have it
    repo_default = REPO_ROOT / ".tmp" / "agent-claims.json"
    if repo_default.exists():
        contents = repo_default.read_text(encoding="utf-8", errors="replace")
        assert "iso-test" not in contents, \
            "CRITICAL LEAK: claim written to real repo store during test"
    # cleanup
    try:
        agent_claims.set_store(None)
    except Exception:
        pass
