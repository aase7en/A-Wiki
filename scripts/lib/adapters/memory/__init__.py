"""adapters/memory — production MemoryPort backed by the JSONL ledger.

ADR-0012 slice A4. Implements scripts/lib/ports.MemoryPort by delegating to
the existing memory_ledger.MemoryLedger primitive. This is the ONLY place
that knows about the JSONL file format — swap this adapter to change the
storage without touching the application core.
"""
from __future__ import annotations

from pathlib import Path
import sys

# Adapter → application/domain: import the primitive we wrap.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # scripts/lib
import memory_ledger  # noqa: E402


class JsonlMemoryAdapter:
    """Production adapter: MemoryPort backed by memory_ledger.MemoryLedger."""

    def __init__(self, ledger_path: Path | str) -> None:
        self._ledger = memory_ledger.MemoryLedger(Path(ledger_path))

    def recall(self, query: str, limit: int = 10) -> list[dict]:
        return self._ledger.search(query, limit=limit)

    def semantic_recall(self, query: str, limit: int = 10) -> list[dict]:
        # A-Council 2026-08-02 (code-review #5 + security-auditor minor):
        # narrow the except to ImportError so genuine bugs inside the
        # semantic_recall module surface instead of being silently masked
        # as a substring fallback. A corrupt/substituted ranker should be
        # visible, not indistinguishable from "no match".
        try:
            import semantic_recall  # type: ignore
        except ImportError:
            return self._ledger.search(query, limit=limit)
        # Let semantic_recall.search raise on real failure — do not swallow.
        return semantic_recall.search(self._ledger.path, query, limit=limit)

    def remember(self, *, session_id: str, type: str, summary: str,
                 files: list[str] | None = None,
                 tags: list[str] | None = None) -> float:
        return self._ledger.append(
            session_id=session_id, type=type, summary=summary,
            files=files or [], tags=tags or [],
        )


class InMemoryMemoryAdapter:
    """Mock adapter: MemoryPort backed by a plain list. For headless tests.

    Has NO persistence and NO BM25 — only the substring recall that the
    char-test pins. Together with JsonlMemoryAdapter it satisfies the
    ADR-0012 acceptance rule "≥2 adapters per port" and proves the port is
    a real seam (Cockburn: 'two adapters = a real seam')."""

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def recall(self, query: str, limit: int = 10) -> list[dict]:
        q = query.lower()
        hits = [e for e in self._entries
                if q in e.get("summary", "").lower()
                or any(q in t.lower() for t in e.get("tags", []))]
        return hits[:limit]

    def semantic_recall(self, query: str, limit: int = 10) -> list[dict]:
        # Mock has no BM25 — substring is the documented fallback.
        return self.recall(query, limit=limit)

    def remember(self, *, session_id: str, type: str, summary: str,
                 files: list[str] | None = None,
                 tags: list[str] | None = None) -> float:
        import time
        ts = time.time()
        self._entries.append({
            "ts": ts, "session_id": session_id, "type": type,
            "summary": summary, "files": files or [], "tags": tags or [],
        })
        return ts
