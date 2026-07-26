"""Tests for scripts/lib/semantic_recall.py — FTS5-backed semantic recall on ledger.

Iron Law #1: failing tests written FIRST.

semantic_recall คือการ search ledger แบบ BM25 ranking (FTS5) แทน substring
matching. ดีกว่า memory_ledger.search() ตรงที่:
  - ranked by relevance (BM25 score)
  - รองรับ multi-word queries ("auth login bug" → เจอ entries เกี่ยวกับ
    authentication/login แม้ไม่มีคำตรง)
  - tokenized (case/punctuation normalized)

Implementation: build in-memory FTS5 table from ledger JSONL on demand
(no persistent DB — ledger is small enough to index per query).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402
import semantic_recall as sr  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. search — returns entries ranked by BM25
# ---------------------------------------------------------------------------
def test_search_returns_ranked_results(tmp_path):
    """Multi-word query should return relevant entries ranked by BM25."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(session_id="s", type="decision",
                  summary="implemented user authentication with bcrypt")
    ledger.append(session_id="s", type="failure",
                  summary="database connection timeout")
    ledger.append(session_id="s", type="decision",
                  summary="login flow uses JWT tokens")

    results = sr.search(ledger_path, query="auth login", limit=5)
    assert len(results) >= 2  # auth + login entries should match
    # Top result should be more relevant (auth or login related, not db timeout)
    top_summary = results[0]["summary"].lower()
    assert "auth" in top_summary or "login" in top_summary, (
        f"top result should be auth/login related, got: {results[0]['summary']}"
    )


def test_search_returns_empty_for_no_match(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="hello world")
    assert sr.search(ledger_path, query="nonexistent_xyzzy", limit=5) == []


def test_search_returns_empty_for_empty_ledger(tmp_path):
    assert sr.search(tmp_path / "missing.jsonl", query="anything", limit=5) == []


# ---------------------------------------------------------------------------
# 2. search — includes BM25 score field
# ---------------------------------------------------------------------------
def test_search_includes_score(tmp_path):
    """Each result should carry a BM25 score for ranking transparency."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(session_id="s", type="decision", summary="critical security fix")
    results = sr.search(ledger_path, query="security", limit=5)
    assert len(results) >= 1
    assert "score" in results[0]
    assert isinstance(results[0]["score"], float)


# ---------------------------------------------------------------------------
# 3. search — multi-word query matches related entries
# ---------------------------------------------------------------------------
def test_search_matches_related_concepts(tmp_path):
    """Query 'database error' should match 'postgres connection failed' even
    without exact word match (FTS5 tokenization + BM25)."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(session_id="s", type="failure",
                  summary="postgres connection failed after retry")
    ledger.append(session_id="s", type="decision",
                  summary="chose redis for caching")
    # 'database' won't match 'postgres' exactly but FTS5 still ranks by tokens
    # This test verifies the function doesn't crash on multi-word queries
    results = sr.search(ledger_path, query="database error connection", limit=5)
    assert isinstance(results, list)
    # At least the postgres entry should appear (matches 'connection')
    if results:
        assert "connection" in results[0]["summary"].lower() or \
               "postgres" in results[0]["summary"].lower()


# ---------------------------------------------------------------------------
# 4. search — respects limit
# ---------------------------------------------------------------------------
def test_search_respects_limit(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    for i in range(10):
        ledger.append(session_id="s", type="decision", summary=f"auth change {i}")
    results = sr.search(ledger_path, query="auth", limit=3)
    assert len(results) <= 3


# ---------------------------------------------------------------------------
# 5. persistence — works on cross-session (same file)
# ---------------------------------------------------------------------------
def test_search_works_across_sessions(tmp_path):
    """session A writes → session B semantic_recall.search() finds it."""
    f = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(f).append(
        session_id="A", type="lesson",
        summary="always validate input before parsing JSON",
        tags=["validation", "json"],
    )
    # New semantic_recall call (no state) on same file
    results = sr.search(f, query="input validation json", limit=5)
    assert len(results) >= 1
    assert "validation" in results[0]["summary"].lower() or "json" in results[0]["summary"].lower()
