"""<AGENT_NAME> generator — TEMPLATE. Copy to gen_<agent>.py and edit the 4 TODOs.

How <AGENT_NAME> discovers skills: <TODO: one line — e.g. "scans configured
dir paths under .<agent>/" or "reads a manifest JSON">

See: docs/protocols/plugin-generator-spec.md (USA-1 §3, the 3-step plugin workflow).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import Registry

filename = "<TODO-agent>.skills-paths.json"  # TODO 1: surface filename


def _category_dirs(registry: Registry) -> list[str]:
    """Distinct top-level category dirs for canonical repo skills (<AGENT_NAME> view)."""
    dirs: list[str] = []
    seen: set[str] = set()
    # TODO 2: replace "<TODO-agent>" with the agent's registry name.
    for skill in registry.canonical_for_agent("<TODO-agent>"):
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
    """Return JSON snippet for <AGENT_NAME> skills discovery paths.

    TODO 3: if the agent needs a manifest (name → target) instead of dir paths,
    switch to the gen_zcode.py pattern. If it needs full metadata, see
    gen_hermes.py. If it reads Markdown, see gen_agents_md.py.
    """
    payload: dict[str, Any] = {
        "skills": {
            "paths": _category_dirs(registry),
            "source": "skills-registry.json",
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)

# TODO 4 (outside this file): register in scripts/regen-skill-surfaces.py
#   GENERATORS dict + import, then add the agent to link-agent-configs.sh.
