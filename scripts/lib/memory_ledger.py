"""memory_ledger.py — event-sourced cross-session memory for A-Wiki brain.

Neural Spine primitive #2 (built on atomic_json).

Memory Ledger แก้ปัญหา: session-memory.md เป็น manual, append-only
knowledge graph ไม่ได้เก็บ decisions/lessons/failures แบบ searchable,
และทุกอย่างหายตอน context compact.

Schema (1 บรรทัดต่อ entry, JSONL):
  {
    "ts": float,             # time.time()
    "session_id": str,       # which agent session wrote it
    "type": str,             # decision|lesson|failure|outcome|idea
    "summary": str,          # human-readable 1-line summary
    "files": [str],          # files touched (optional)
    "tags": [str],           # topic tags (optional)
    "parent_ts": float|null  # link to parent entry (thread)
  }

Writers (auto-captured by scripts/hooks/memory_capture.py):
  - PostToolUse commit     → type=decision, summary=commit msg, files=changed
  - hook block             → type=failure, summary=reason, tags=[hook name]
  - Stop                   → type=outcome, summary=session summary
  - /remember              → type per arg

Readers:
  - SessionStart           → replay_for_context(interest_tags=...) → inject
  - MCP memory_recall      → search(query) → matching entries

Iron Law #6: writer redacts obvious secrets before persisting (reuses the
regex family from scripts/hooks/check_secret_leak.py).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atomic_json  # noqa: E402 -- sibling primitive (chunk 1)

VALID_TYPES = {"decision", "lesson", "failure", "outcome", "idea"}

# Secret-redaction patterns. Conservative: redact anything that looks like a
# common secret format so a captured commit/block message can't leak a key.
_SECRET_PATTERNS = [
    # OpenAI / Anthropic / Gemini-style API keys (lower threshold = safer)
    re.compile(r"\b(sk-[A-Za-z0-9_\-]{8,})\b"),
    re.compile(r"\b(sk-ant-[A-Za-z0-9_\-]{8,})\b"),
    # Generic high-entropy tokens (32+ hex/base64 chars after a prefix word)
    re.compile(r"\b(?:api[_-]?key|token|secret|password|pwd)[\"'\s:=]+([A-Za-z0-9_\-]{32,})\b", re.IGNORECASE),
    # Google API keys / OAuth tokens
    re.compile(r"\b(AIza[A-Za-z0-9_\-]{30,})\b"),
    # Bearer tokens
    re.compile(r"\b(Bearer\s+[A-Za-z0-9_\-\.]{20,})\b"),
]
_REDACTED = "***"


def _redact(text: str) -> str:
    """Replace likely-secret substrings with ***. Best-effort, never raises."""
    if not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(_REDACTED, out)
    return out


class MemoryLedger:
    """Append-only event-sourced memory store.

    Construction is cheap (no file read). Reads lazily parse the JSONL.
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def append(
        self,
        *,
        session_id: str,
        type: str,
        summary: str,
        files: list[str] | None = None,
        tags: list[str] | None = None,
        parent_ts: float | None = None,
    ) -> float:
        """Append one entry. Returns the entry's ts.

        Validates type. Redacts secrets from summary. Files/tags normalized.
        """
        if type not in VALID_TYPES:
            raise ValueError(
                f"invalid type {type!r}; must be one of {sorted(VALID_TYPES)}"
            )
        ts = time.time()
        entry: dict[str, Any] = {
            "ts": ts,
            "session_id": session_id or "unknown",
            "type": type,
            "summary": _redact(str(summary)) if summary else "",
            "files": list(files) if files else [],
            "tags": [str(t) for t in tags] if tags else [],
            "parent_ts": parent_ts,
        }
        atomic_json.atomic_append_jsonl(self.path, entry)
        return ts

    def _load_all(self) -> list[dict]:
        """Read every entry as a list of dicts. Returns [] if file missing."""
        if not self.path.is_file():
            return []
        out: list[dict] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip corrupt line — append-only must be robust
        return out

    def recent(self, limit: int = 25) -> list[dict]:
        """Return last ``limit`` entries, newest-first. Default 25."""
        all_entries = self._load_all()
        if limit <= 0:
            limit = len(all_entries) or 1
        return list(reversed(all_entries[-limit:]))

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Substring search over summary + tags, case-insensitive. Newest-first.

        We intentionally avoid SQLite FTS5 here to keep this primitive
        dependency-free and robust. For semantic search, the MCP layer
        (memory_recall) can layer sqlite-vec on top later.
        """
        if not query:
            return []
        q = query.lower()
        all_entries = self._load_all()
        hits = [
            e for e in all_entries
            if q in (e.get("summary", "")).lower()
            or any(q in str(t).lower() for t in e.get("tags", []))
        ]
        return list(reversed(hits[-limit:]))

    def replay_for_context(
        self,
        *,
        interest_tags: list[str] | None = None,
        interest_files: list[str] | None = None,
        limit: int = 10,
        since_ts: float | None = None,
    ) -> list[dict]:
        """Return entries relevant to current work, for SessionStart injection.

        Filters:
          - interest_tags:  if entry shares any tag → relevant
          - interest_files: if entry touched any file → relevant
          - since_ts:       only entries after this timestamp
        If no filters given, returns recent N (general replay).
        """
        all_entries = self._load_all()
        interest_tags_lower = {t.lower() for t in (interest_tags or [])}
        interest_files_set = {str(f) for f in (interest_files or [])}

        def relevant(e: dict) -> bool:
            if since_ts is not None and e.get("ts", 0) < since_ts:
                return False
            if not interest_tags_lower and not interest_files_set:
                return True  # no filter → all relevant
            entry_tags = {str(t).lower() for t in e.get("tags", [])}
            entry_files = set(e.get("files", []))
            if interest_tags_lower and (entry_tags & interest_tags_lower):
                return True
            if interest_files_set and (entry_files & interest_files_set):
                return True
            return False

        hits = [e for e in all_entries if relevant(e)]
        return list(reversed(hits[-limit:]))
