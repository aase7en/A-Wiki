"""OpenClaw generator — emits the skills discovery paths for .openclaw/.

OpenClaw discovers skills by scanning configured paths under .openclaw/.
Like the other path-scanning agents (Kilo/Cline/Codex/Windsurf), we emit
the distinct top-level category dirs of canonical repo skills so OpenClaw
sees the same canonical set as every other agent.

See: docs/architecture/universal-skill-architecture.md §3 (USA-1, chunk C1).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import Registry

filename = "openclaw.skills-paths.json"


def _category_dirs(registry: Registry) -> list[str]:
    """Distinct top-level category dirs for canonical repo skills (OpenClaw view)."""
    dirs: list[str] = []
    seen: set[str] = set()
    for skill in registry.canonical_for_agent("openclaw"):
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
    """Return JSON snippet for OpenClaw skills discovery paths."""
    payload: dict[str, Any] = {
        "skills": {
            "paths": _category_dirs(registry),
            "source": "skills-registry.json",
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
