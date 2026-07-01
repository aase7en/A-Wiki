"""Antigravity generator — emits the skills discovery config for .antigravity/.

Antigravity (Anthropic's agent) reads agent rules from .antigravity/ config.
Like Claude, it auto-discovers skills from configured paths. We emit the
category dirs of canonical repo skills so Antigravity can scan them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import Registry

filename = "antigravity.skills-paths.json"


def _category_dirs(registry: Registry) -> list[str]:
    """Distinct top-level category dirs for canonical repo skills."""
    dirs: list[str] = []
    seen: set[str] = set()
    for skill in registry.canonical_for_agent("antigravity"):
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
    """Return JSON snippet for Antigravity skills discovery paths."""
    payload: dict[str, Any] = {
        "skills": {
            "paths": _category_dirs(registry),
            "source": "skills-registry.json",
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
