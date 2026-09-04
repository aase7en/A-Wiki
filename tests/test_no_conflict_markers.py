"""Guard: tracked wiki markdown must not carry git conflict markers.

Origin: a broken stash-pop/auto-commit (c343542c era, 2026-08-20 night-shift
log) landed nested ``<<<<<<< Updated upstream ... >>>>>>> Stashed changes``
blocks inside 6 nested wiki CLAUDE.md files, and ``gen-index.py`` date
refreshes kept propagating the corrupted structure. This test fails on any
regression so the corruption cannot silently return.

Only marker-only lines that are never valid markdown are checked:
``<<<<<<< `` and ``>>>>>>> `` prefixes. A bare ``=======`` line is legal
setext-heading markup and is deliberately not flagged.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MARKER_PREFIXES = ("<<<<<<< ", ">>>>>>> ")


def _tracked_wiki_markdown() -> list[tuple[str, str]]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "--", "wiki/*.md", "wiki/**/*.md"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise AssertionError(f"git ls-files unavailable: {exc}") from exc
    files = []
    for rel in (line.strip() for line in out.splitlines() if line.strip()):
        path = REPO_ROOT / rel
        if path.is_file():
            files.append((rel, path.read_text(encoding="utf-8", errors="replace")))
    return files


def test_tracked_files_exist() -> None:
    assert _tracked_wiki_markdown(), "no tracked wiki markdown found"


def test_no_conflict_markers_in_tracked_wiki_markdown() -> None:
    offenders: dict[str, list[int]] = {}
    for rel, text in _tracked_wiki_markdown():
        bad = [
            lineno for lineno, line in enumerate(text.splitlines(), start=1)
            if line.startswith(MARKER_PREFIXES)
        ]
        if bad:
            offenders[rel] = bad
    if offenders:
        detail = "; ".join(f"{rel}: lines {lins[:5]}" for rel, lins in sorted(offenders.items()))
        raise AssertionError(
            f"git conflict markers present in tracked wiki markdown ({len(offenders)} files): {detail}"
        )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(0)
