"""Kilo Code generator — emits the skills.paths[] block for .kilo/kilo.jsonc.

Kilo discovers skills by recursively scanning the paths in its ``skills.paths``
array.  We generate that array from the registry: every canonical repo-source
skill's top-level category directory is included (deduplicated).  External
skills are NOT included here because Kilo resolves those from its own global dir.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import Registry

filename = "kilo.skills-paths.json"  # consumed by orchestrator, merged into kilo.jsonc


def _category_dirs(registry: Registry) -> list[str]:
    """Distinct top-level category dirs for canonical repo skills."""
    dirs: list[str] = []
    seen: set[str] = set()
    for skill in registry.canonical_for_agent("kilo"):
        path = skill.get("path", "")
        if skill.get("source") != "repo" or not path:
            continue
        # Use the first segment after the repo root (e.g. "skills", "agent-skills")
        # plus the category dir, so Kilo scans a manageable subtree.
        parts = Path(path).parts
        if len(parts) >= 2:
            top = "/".join(parts[:2])
            if top not in seen:
                seen.add(top)
                dirs.append(f"./{top}")
    return sorted(dirs)


def render(registry: Registry) -> str:
    """Return the JSON snippet Kilo would merge into kilo.jsonc skills.paths."""
    payload: dict[str, Any] = {
        "skills": {
            "paths": _category_dirs(registry),
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
