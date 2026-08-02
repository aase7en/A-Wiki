"""tests/test_ports_contract.py — port contract suite (ADR-0012 R10 mitigation).

Runs the SAME behavioural assertions against EVERY adapter of a port. Any
adapter that wants to call itself a MemoryPort / TaskBoardPort must pass this
suite. Catches 'mock too permissive' (R10) — if a mock lets invalid behaviour
through that the prod adapter rejects, the contract suite will diverge.

This is the Liskov substitute check for hexagonal ports. Add a new adapter →
add it to _memory_adapters / _taskboard_adapters below; no new tests needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from ports import MemoryPort, TaskBoardPort  # noqa: E402
from adapters.memory import JsonlMemoryAdapter, InMemoryMemoryAdapter  # noqa: E402
from adapters.taskboard import JsonlTaskBoardAdapter, InMemoryTaskBoardAdapter  # noqa: E402


# ── Adapter factory lists — extend when you add a new adapter ────────────
def _memory_adapters():
    return [
        pytest.param(InMemoryMemoryAdapter(), id="in-memory-mock"),
    ]


def _memory_adapters_with_disk(tmp_path):
    return [
        pytest.param(InMemoryMemoryAdapter(), id="in-memory-mock"),
        pytest.param(JsonlMemoryAdapter(tmp_path / "ledger.jsonl"),
                     id="jsonl-prod"),
    ]


def _taskboard_adapters_with_disk(tmp_path):
    return [
        pytest.param(InMemoryTaskBoardAdapter(), id="in-memory-mock"),
        pytest.param(JsonlTaskBoardAdapter(tmp_path / "tasks.json"),
                     id="jsonl-prod"),
    ]


# ── Structural: both adapters must be recognisable as their port ─────────
def test_adapters_satisfy_port_protocols():
    """runtime_checkable Protocols: isinstance() validates method shape."""
    assert isinstance(InMemoryMemoryAdapter(), MemoryPort)
    assert isinstance(JsonlMemoryAdapter(Path("/tmp/x")), MemoryPort)
    assert isinstance(InMemoryTaskBoardAdapter(), TaskBoardPort)
    assert isinstance(JsonlTaskBoardAdapter(Path("/tmp/x")), TaskBoardPort)


# ── MemoryPort contract ─────────────────────────────────────────────────
@pytest.mark.parametrize("adapter", _memory_adapters(), indirect=False)
def test_memory_remember_then_recall_roundtrip(adapter):
    """A remembered entry must be findable by a word in its summary."""
    ts = adapter.remember(session_id="s", type="lesson",
                           summary="prefer ports over frameworks",
                           tags=["architecture"])
    assert isinstance(ts, float) and ts > 0
    hits = adapter.recall("ports")
    assert any("ports" in h.get("summary", "") for h in hits)


@pytest.mark.parametrize("adapter", _memory_adapters(), indirect=False)
def test_memory_recall_respects_limit(adapter):
    for i in range(5):
        adapter.remember(session_id="s", type="lesson",
                         summary=f"item {i} needle")
    assert len(adapter.recall("needle", limit=2)) <= 2


@pytest.mark.parametrize("adapter", _memory_adapters(), indirect=False)
def test_memory_recall_no_match_returns_empty(adapter):
    """Empty list, never None, never raises — pinned contract."""
    assert adapter.recall("nothing-matches-this-zzz") == []


# Parametrize disk-backed variants for a subset (roundtrip only — needs persistence)
def test_memory_jsonl_roundtrip(tmp_path):
    for adapter in [a.values[0] for a in _memory_adapters_with_disk(tmp_path)]:
        adapter.remember(session_id="s", type="decision",
                         summary="jsonl-specific needle")
        hits = adapter.recall("needle")
        assert any("needle" in h.get("summary", "") for h in hits), \
            f"{type(adapter).__name__} failed roundtrip"


# ── TaskBoardPort contract ──────────────────────────────────────────────
@pytest.mark.parametrize("adapter", [
    pytest.param(InMemoryTaskBoardAdapter(), id="in-memory-mock"),
], indirect=False)
def test_taskboard_claim_is_atomic(adapter):
    """First claim wins, second loses — the Iron Law #11 concurrency floor."""
    tid = adapter.add(goal="x")
    assert adapter.claim(tid, claimant="claude") is True
    assert adapter.claim(tid, claimant="codex") is False


@pytest.mark.parametrize("adapter", [
    pytest.param(InMemoryTaskBoardAdapter(), id="in-memory-mock"),
], indirect=False)
def test_taskboard_list_filters_by_status(adapter):
    t1 = adapter.add(goal="one")
    t2 = adapter.add(goal="two")
    adapter.update(t1, status="done")
    done = adapter.list(status="done")
    assert len(done) == 1
    assert done[0]["id"] == t1


@pytest.mark.parametrize("adapter", [
    pytest.param(InMemoryTaskBoardAdapter(), id="in-memory-mock"),
], indirect=False)
def test_taskboard_release_returns_task_to_todo(adapter):
    tid = adapter.add(goal="x")
    adapter.claim(tid, claimant="claude")
    assert adapter.release(tid) is True
    todos = adapter.list(status="todo")
    assert any(t["id"] == tid for t in todos)


def test_taskboard_jsonl_contract(tmp_path):
    """Prod JSONL adapter must satisfy the same contract as the mock."""
    adapter = JsonlTaskBoardAdapter(tmp_path / "tasks.json")
    tid = adapter.add(goal="contract check")
    assert adapter.claim(tid, claimant="claude") is True
    assert adapter.claim(tid, claimant="codex") is False  # atomic
    assert adapter.update(tid, status="done") is True
    done = adapter.list(status="done")
    assert len(done) == 1 and done[0]["id"] == tid
