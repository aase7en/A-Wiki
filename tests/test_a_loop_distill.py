"""Tests for scripts/hooks/a_loop_distill.py — Phase 3 idea distiller.

Iron Law #1: failing tests written FIRST.

a_loop_distill คือ Stop hook ที่ scan memory_ledger หา patterns:
  - failure ที่ซ้ำกัน (same tag/summary) → propose idea "ควรมี guard สำหรับ X"
  - outcome ที่ดี → propose idea "pattern นี้ใช้ได้ น่า generalize"

ถ้าเจอ → memory_remember(type="idea") → SessionStart แสดง
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402
import a_loop_distill as ald  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. count_failure_patterns — counts failures grouped by tag/keyword
# ---------------------------------------------------------------------------
def test_count_failure_patterns_finds_repeated(tmp_path):
    """3 failures with same tag → pattern count 3."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"import error in module {i}", tags=["import-error"])
    patterns = ald.count_failure_patterns(ledger_path)
    assert any(p["count"] >= 3 for p in patterns), (
        f"expected a pattern with count>=3, got {patterns}"
    )


def test_count_failure_patterns_ignores_isolated(tmp_path):
    """A failure seen only once should not be flagged as a pattern."""
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="failure", summary="one-off typo", tags=["typo"])
    patterns = ald.count_failure_patterns(ledger_path, min_count=2)
    assert patterns == [], "isolated failure should not be a pattern"


def test_count_failure_patterns_ignores_non_failures(tmp_path):
    """Decisions/outcomes should not be counted as failure patterns."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(5):
        ledger.append(session_id="s", type="decision", summary=f"commit {i}")
    patterns = ald.count_failure_patterns(ledger_path)
    assert patterns == [], "decisions are not failures"


# ---------------------------------------------------------------------------
# 2. propose_ideas — writes idea entries for repeated patterns
# ---------------------------------------------------------------------------
def test_propose_ideas_writes_to_ledger(tmp_path):
    """When a failure pattern repeats ≥3, an idea entry should be written."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"permission denied on file {i}", tags=["permission"])
    ideas_before = len(ledger.search("idea", limit=100))
    # Actually search for type=idea
    all_entries = ledger._load_all()
    ideas_before = sum(1 for e in all_entries if e.get("type") == "idea")

    n_proposed = ald.propose_ideas(ledger_path, min_count=3)

    all_entries = ledger._load_all()
    ideas_after = sum(1 for e in all_entries if e.get("type") == "idea")
    assert n_proposed >= 1, "should propose at least 1 idea for repeated failure"
    assert ideas_after > ideas_before, "idea entries should increase"
    # The proposed idea should reference the failure pattern
    ideas = [e for e in all_entries if e.get("type") == "idea"]
    assert any("permission" in e["summary"].lower() for e in ideas), (
        f"proposed idea should mention the pattern, got: {ideas}"
    )


def test_propose_ideas_no_ideas_for_no_patterns(tmp_path):
    """No repeated failures → no ideas proposed."""
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="failure", summary="lonely failure", tags=["x"])
    n = ald.propose_ideas(ledger_path, min_count=3)
    assert n == 0


# ---------------------------------------------------------------------------
# 3. propose_ideas — idempotent (doesn't double-propose)
# ---------------------------------------------------------------------------
def test_propose_ideas_idempotent(tmp_path):
    """Running propose_ideas twice should not double-propose the same idea."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"timeout on api {i}", tags=["timeout"])
    first = ald.propose_ideas(ledger_path, min_count=3)
    second = ald.propose_ideas(ledger_path, min_count=3)
    # Second run should detect the idea already exists and skip
    assert first >= 1
    assert second == 0, (
        f"second run should not re-propose (idempotent), got {second}"
    )


# ---------------------------------------------------------------------------
# 4. main — hook entry point, exits 0
# ---------------------------------------------------------------------------
def test_main_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(ald, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert ald.main() == 0


def test_main_respects_hook_skip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOOK_SKIP", "a_loop_distill")
    monkeypatch.setattr(ald, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert ald.main() == 0


# ---------------------------------------------------------------------------
# 5. auto_propose_skill — when pattern ≥3, draft skill proposal (no register)
# ---------------------------------------------------------------------------
def test_auto_propose_skill_creates_proposal_entry(tmp_path):
    """When 3+ failures share a tag → distill should auto-draft a skill proposal.

    The draft is written as a ledger type=idea entry tagged
    'skill-proposal' so SessionStart surfaces it for user review.
    """
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"import error module {i}", tags=["import-error"])
    n = ald.auto_propose_skill(ledger_path, min_count=3)
    assert n >= 1, "should draft at least 1 skill proposal"
    # Verify the proposal is in ledger as type=idea with skill-proposal tag
    entries = ledger._load_all()
    proposals = [e for e in entries
                 if e.get("type") == "idea"
                 and "skill-proposal" in e.get("tags", [])]
    assert len(proposals) >= 1
    assert any("guard-import-error" in e["summary"].lower()
               or "guard-import" in e["summary"].lower()
               for e in proposals), (
        f"proposal should reference guard-import pattern, got: {[p['summary'] for p in proposals]}"
    )


def test_auto_propose_skill_idempotent(tmp_path):
    """Running auto_propose twice should not double-propose."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"timeout api {i}", tags=["timeout"])
    first = ald.auto_propose_skill(ledger_path, min_count=3)
    second = ald.auto_propose_skill(ledger_path, min_count=3)
    assert first >= 1
    assert second == 0, f"second run should not re-propose, got {second}"


def test_auto_propose_skill_no_action_when_below_threshold(tmp_path):
    """2 failures (below min_count=3) → no proposal."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(2):
        ledger.append(session_id="s", type="failure",
                      summary=f"rare bug {i}", tags=["rare"])
    n = ald.auto_propose_skill(ledger_path, min_count=3)
    assert n == 0


# ---------------------------------------------------------------------------
# 6. main now auto-calls auto_propose_skill (in addition to propose_ideas)
# ---------------------------------------------------------------------------
def test_main_runs_both_distill_and_propose(monkeypatch, tmp_path):
    """main() should call both propose_ideas + auto_propose_skill."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(3):
        ledger.append(session_id="s", type="failure",
                      summary=f"regex bug {i}", tags=["regex"])
    monkeypatch.setattr(ald, "DEFAULT_LEDGER_PATH", ledger_path)
    ald.main()
    entries = ledger._load_all()
    ideas = [e for e in entries if e.get("type") == "idea"]
    proposals = [e for e in ideas if "skill-proposal" in e.get("tags", [])]
    distill_ideas = [e for e in ideas if "distill:" in str(e.get("tags", []))]
    assert len(distill_ideas) >= 1, "propose_ideas should still run"
    assert len(proposals) >= 1, "auto_propose_skill should also run"
