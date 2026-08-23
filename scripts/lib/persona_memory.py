"""persona_memory.py — Slice E2: each a-council critic remembers own lessons.

Personas are the SAME reviewer across sessions — filtering the shared
ledger by persona gives each critic its own memory without new stores.
"""
from __future__ import annotations

import json
from pathlib import Path

PERSONAS = ("code-reviewer", "test-engineer", "security-auditor",
            "web-performance-auditor")


def persona_entries(ledger: Path, persona: str, limit: int = 20) -> list[dict]:
    if persona not in PERSONAS:
        raise ValueError(f"unknown persona {persona!r}; valid: {PERSONAS}")
    if not Path(ledger).is_file():
        return []
    out = []
    for line in reversed(Path(ledger).read_text(encoding="utf-8").splitlines()):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        hay = " ".join([e.get("summary", "")]
                       + [str(t) for t in e.get("tags", [])]).lower()
        if persona.lower() in hay or str(e.get("persona", "")).lower() == persona:
            out.append(e)
            if len(out) >= limit:
                break
    return out
