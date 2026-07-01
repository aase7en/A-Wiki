"""Cline generator — emits the skills discovery paths for .clinerules/.

Cline discovers skills by scanning directories configured in .clinerules/.
Like Kilo, we emit the category dirs of canonical repo skills.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import Registry

filename = "cline.skills-paths.json"


def _category_dirs(registry: Registry) -> list[str]:
    """Distinct top-level category dirs for canonical repo skills (Kilo parity)."""
    dirs: list[str] = []
    seen: set[str] = set()
    for skill in registry.canonical_for_agent("cline"):
        path = skill.get("path", "")
        if skill.get("source") != "repo" or not path:
            continue
        parts = Path(path).parts
        if len(parts) >= 2:
            top = "/".join(parts[:2])
            if top not in seen:
                seen.add(top)
                dirs.append(f"./{top}")
    return sorted(dirs)


def render(registry: Registry) -> str:
    """Return JSON snippet for Cline skills discovery paths."""
    payload: dict[str, Any] = {
        "skills": {
            "paths": _category_dirs(registry),
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
