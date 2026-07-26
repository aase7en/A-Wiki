"""semantic_recall.py — FTS5-backed semantic search over Memory Ledger.

Tier 2 #5. Upgrades memory_recall from substring matching to BM25 ranking.

Why FTS5 (not sqlite-vec/fastembed):
  - sqlite-vec + fastembed are optional deps not installed in base env
  - FTS5 is in Python stdlib (sqlite3) → zero deps, always works
  - BM25 ranking is 'semantic-ish' — tokenized, multi-word, ranked by relevance
  - For true embedding-based semantic search, layer sqlite-vec on top later
    (optional backend — see BACKEND note below)

Design:
  - Builds an in-memory FTS5 table from ledger JSONL on each search call
  - Ledger is small (capped at MAX_LOAD_ENTRIES=200 by chunk C fix) → fast
  - Indexes summary + tags (concatenated) as the searchable text

API:
  search(ledger_path, query, limit=10) → list[{...entry, score}]
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_ledger  # noqa: E402


def _normalize_text(text: str) -> str:
    """Normalize text for FTS5 indexing.

    Lowercase, strip punctuation that confuses tokenizer, collapse whitespace.
    Keeps alphanumeric + spaces + underscores (tags are often kebab/snake).
    """
    if not text:
        return ""
    text = text.lower()
    # Replace non-alphanumeric (except _ and -) with space
    text = re.sub(r"[^a-z0-9_\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def search(
    ledger_path: Path | str,
    query: str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Semantic search over Memory Ledger using FTS5 BM25 ranking.

    Returns list of entries (with all original fields + 'score' field),
    ranked by BM25 relevance, descending. Empty list if no matches.

    The query is matched against summary + tags. Multi-word queries work
    (FTS5 tokenizes and ranks by term frequency × inverse doc frequency).
    """
    ledger = memory_ledger.MemoryLedger(ledger_path)
    entries = ledger._load_all()
    if not entries or not query.strip():
        return []

    # Build in-memory FTS5 table
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE ledger_fts USING fts5("
            "summary, tags, type, content='external', tokenize='unicode61')"
        )
        for i, e in enumerate(entries):
            summary = _normalize_text(e.get("summary", ""))
            tags = _normalize_text(" ".join(e.get("tags", [])))
            etype = _normalize_text(e.get("type", ""))
            conn.execute(
                "INSERT INTO ledger_fts(rowid, summary, tags, type) VALUES (?, ?, ?, ?)",
                (i, summary, tags, etype),
            )
        conn.commit()

        # Build BM25 query — FTS5 expects space-separated tokens.
        # Use prefix query (token*) for better recall — "auth" matches
        # "authentication", "authorized", etc. OR semantics for multi-word.
        norm_query = _normalize_text(query)
        tokens = [t for t in norm_query.split() if t]
        if not tokens:
            return []
        # Each token → "token*" (prefix match) joined by OR
        fts_query = " OR ".join(f"{t}*" for t in tokens)

        cursor = conn.execute(
            "SELECT rowid, bm25(ledger_fts) AS score "
            "FROM ledger_fts WHERE ledger_fts MATCH ? "
            "ORDER BY score LIMIT ?",
            (fts_query, limit),
        )
        rows = cursor.fetchall()
        # bm25() returns NEGATIVE scores (more negative = more relevant)
        # Convert to positive for intuitive ranking
        results = []
        for rowid, score in rows:
            entry = dict(entries[rowid])
            entry["score"] = float(-score)  # flip sign: higher = more relevant
            results.append(entry)
        return results
    finally:
        conn.close()
