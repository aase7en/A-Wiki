"""Gemini CLI generator — emits the skills{} block for .gemini/settings.json.

Gemini maps named skill collections to directories.  We group canonical repo
skills by category and emit a {category: "./relative/path"} map.
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .. import Registry

filename = "gemini.skills.json"


def render(registry: Registry) -> str:
    groups: dict[str, list[str]] = defaultdict(list)
    for skill in registry.canonical_for_agent("gemini"):
        if skill.get("source") != "repo":
            continue
        category = skill.get("category", "uncategorized")
        path = skill.get("path", "")
        # group by top-level dir (skills/<cat> or agent-skills/<cat>)
        parts = path.split("/")
        if len(parts) >= 2:
            top = "/".join(parts[:2])
            if top not in groups[category]:
                groups[category].append(top)

    skills_map: dict[str, str] = {}
    for category, dirs in sorted(groups.items()):
        # Gemini expects one path per named collection; use category as key.
        skills_map[category] = f"../{dirs[0]}" if dirs else ""

    payload: dict[str, Any] = {"skills": skills_map}
    return json.dumps(payload, indent=2, ensure_ascii=False)
