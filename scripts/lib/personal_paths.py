#!/usr/bin/env python3
"""Resolve private local A-Wiki files with public-clone fallbacks."""
from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def first_existing(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def session_memory_path(root: Path | None = None, *, allow_example: bool = True) -> Path | None:
    root = root or repo_root()
    candidates = [
        root / "wiki" / "context" / "session-memory.md",
        root / "drive" / "personal" / "journal" / "wiki-context-session-memory.md",
        root / "drive" / "personal" / "journal" / "session-memory.md",
    ]
    if allow_example:
        candidates.append(root / "wiki" / "context" / "session-memory.md.example")
    return first_existing(candidates)


def log_path(root: Path | None = None, *, allow_example: bool = True) -> Path | None:
    root = root or repo_root()
    candidates = [
        root / "log.md",
        root / "drive" / "personal" / "journal" / "log.md",
    ]
    if allow_example:
        candidates.append(root / "log.md.example")
    return first_existing(candidates)

