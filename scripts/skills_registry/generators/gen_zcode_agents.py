"""ZCode *agents* generator — emits the subagents manifest for .zcode/agents/.

Distinct from gen_zcode.py, which emits the *skills* manifest for .zcode/skills/.
This generator emits a manifest of registry entries whose ``category`` is
``subagent`` — i.e. specialized domain subagent definitions (medical, finance,
coding, ...) that ZCode loads from ``~/.zcode/agents/<name>.md``.

The linker (scripts/link-agent-configs.sh) consumes this manifest to recreate
``.zcode/agents/`` as a symlink farm pointing INTO THE REPO at
``agents/subagents/<name>.md`` — not into a stale snapshot.

Registry entries must carry the frontmatter fields ZCode expects
(``name``, ``description``, ``tools``, ``model``, ``color``) in a companion
``agents/subagents/<name>.md`` file. The registry entry itself records the
metadata (domain, lifecycle_phase, status) for governance (Iron Law #9); the
``.md`` file is the actual subagent definition ZCode reads.

See: docs/protocols/subagent-model-routing.md
     docs/architecture/universal-skill-architecture.md
"""
from __future__ import annotations

import json
from typing import Any

from .. import Registry

filename = "zcode.agents.manifest.json"


def _agent_entries(registry: Registry) -> list[dict[str, str]]:
    """Subagent entries visible to ZCode, with symlink target each needs.

    Filters the registry to entries where ``category == "subagent"`` and
    ``source == "repo"``. Each entry gives the linker enough to recreate
    ``.zcode/agents/<name>`` as a symlink into the repo.
    """
    entries: list[dict[str, str]] = []
    for skill in registry.skills:
        if skill.get("category") != "subagent":
            continue
        if skill.get("source") != "repo":
            continue
        path = skill.get("path", "")
        if not path:
            continue
        entries.append({
            "name": skill["name"],
            # path points at the .md file directly (e.g. agents/subagents/x.md);
            # the linker links .zcode/agents/<name>.md -> repo path.
            "target": path,
            "domain": ",".join(skill.get("domain", [])),
            "model": skill.get("model", ""),
        })
    entries.sort(key=lambda e: e["name"])
    return entries


def render(registry: Registry) -> str:
    """Return the ZCode agents manifest JSON.

    Consumed by scripts/link-agent-configs.sh to rebuild .zcode/agents/ as a
    symlink farm pointing into the repo. Schema:
        {
          "schema": "zcode-agents-manifest/v1",
          "source": "skills-registry.json",
          "link_root": ".zcode/agents",
          "agents": [
            {"name": "<agent>", "target": "<repo-relative .md>", "domain": "...", "model": "..."},
            ...
          ]
        }
    """
    payload: dict[str, Any] = {
        "schema": "zcode-agents-manifest/v1",
        "source": "skills-registry.json",
        "link_root": ".zcode/agents",
        "agents": _agent_entries(registry),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
