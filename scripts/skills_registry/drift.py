"""Drift detection — compare generated surfaces against what the registry would produce.

A "surface" is any generated per-agent artifact (kilo.jsonc skills block, Gemini
settings.json skills block, AGENTS.md table, symlink farm contents).  The
orchestrator (regen-skill-surfaces.py) calls these helpers in ``--check`` mode
(CI) to refuse merges that would leave surfaces stale.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import DriftError, Registry


def detect(
    registry_path: Path | str,
    surfaces_dir: Path | str,
    generated: dict[str, str],
) -> list[str]:
    """Return a list of drift descriptions. Empty = surfaces are in sync.

    Parameters
    ----------
    registry_path : path to skills-registry.json (for stamping generated_at).
    surfaces_dir  : directory where surface files live.
    generated     : mapping {surface_filename: expected_content} the orchestrator
                    produced from the registry this run.
    """
    errors: list[str] = []
    surfaces_dir = Path(surfaces_dir)

    for filename, expected in generated.items():
        surface_path = surfaces_dir / filename
        if not surface_path.exists():
            errors.append(f"drift: {filename} missing from {surfaces_dir}")
            continue
        actual = surface_path.read_text(encoding="utf-8")
        if _normalize(actual) != _normalize(expected):
            errors.append(f"drift: {filename} content does not match registry output")

    return errors


def detect_and_raise(
    registry_path: Path | str,
    surfaces_dir: Path | str,
    generated: dict[str, str] | None = None,
) -> None:
    """Like detect(), but raise DriftError on the first mismatch (for CI)."""
    if generated is None:
        generated = {}
    errors = detect(registry_path, surfaces_dir, generated)
    if errors:
        raise DriftError("; ".join(errors))


def _normalize(text: str) -> str:
    """Strip the volatile generated_at stamp so timestamp noise doesn't read as drift."""
    # Replace any ISO-8601 timestamp in a generated_at field with a placeholder.
    import re
    return re.sub(r'"generated_at"\s*:\s*"[^"]*"', '"generated_at": "STAMPED"', text)


__all__ = ["detect", "detect_and_raise"]
