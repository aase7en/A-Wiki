"""ZCode generator — emits the skills manifest for .zcode/.

ZCode discovers skills via the .zcode/skills/ directory. Historically this was
a 330-entry symlink farm where 306 links pointed at a STALE ~/.claude/skills/
snapshot, drifting from the repo (USA-1 audit gap G4).

This generator emits a manifest (the canonical skill list with repo-relative
paths) that the linker consumes to recreate the symlink farm POINTING INTO THE
REPO — not into ~/.claude/skills/. This fixes the drift permanently and makes
ZCode a first-class registry-driven agent.

See: docs/architecture/universal-skill-architecture.md §3.4 (USA-1, chunk C1).
"""
from __future__ import annotations

import json
from typing import Any

from .. import Registry

filename = "zcode.skills.manifest.json"


def _skill_entries(registry: Registry) -> list[dict[str, str]]:
    """Canonical skills visible to ZCode, with the symlink target each entry needs.

    Each entry gives the linker enough to recreate .zcode/skills/<name> as a
    symlink into the repo (not into ~/.claude/skills/).
    """
    entries: list[dict[str, str]] = []
    for skill in registry.canonical_for_agent("zcode"):
        path = skill.get("path", "")
        if skill.get("source") != "repo" or not path:
            # Non-repo skills (external-installed) are resolved by ZCode's own
            # global dir; the linker does not manage them.
            continue
        entries.append({
            "name": skill["name"],
            "target": path,  # repo-relative path to the SKILL.md directory
            "domain": ",".join(skill.get("domain", [])),
        })
    entries.sort(key=lambda e: e["name"])
    return entries


def render(registry: Registry) -> str:
    """Return the ZCode skills manifest JSON.

    Consumed by scripts/link-agent-configs.sh to rebuild .zcode/skills/ as a
    symlink farm pointing into the repo. Schema:
        {
          "schema": "zcode-skills-manifest/v1",
          "source": "skills-registry.json",
          "link_root": ".zcode/skills",
          "skills": [
            {"name": "<skill>", "target": "<repo-relative dir>", "domain": "..."},
            ...
          ]
        }
    """
    payload: dict[str, Any] = {
        "schema": "zcode-skills-manifest/v1",
        "source": "skills-registry.json",
        "link_root": ".zcode/skills",
        "skills": _skill_entries(registry),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
