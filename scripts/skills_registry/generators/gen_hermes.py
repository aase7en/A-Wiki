"""Hermes generator — emits the opt-in skill manifest for Pi5 Hermes.

Unlike the other generators (Kilo/Cline/Antigravity/Gemini), this one is
**opt-in**: a skill appears in ``hermes.skills.json`` only when its ``agents``
list explicitly names ``"hermes"``.  Skills tagged ``agents: ["all"]`` are
deliberately EXCLUDED.

Rationale
---------
Hermes runs 24/7 on Raspberry Pi 5 against free-tier models (DeepSeek
V4-Flash, Gemini-Flash-Lite — see ``scripts/hermes/model-pool/model-pool.json``)
with 8k-32k context windows and a read-only A-Wiki mount.  Preloading all 331
canonical skills would blow the context budget, so Hermes surfaces a small
(~40-50) hand-picked set: lifecycle skills, Telegram-relevant domains (wiki,
pharmacy, thai), and key meta-skills.  Tagging is done in ``skills-registry.json``;
this generator only reads it.

Consumers
---------
- ``scripts/hermes/awiki-init-pi5.sh`` (Chunk C) reads this manifest to decide
  which skill dirs to symlink into ``~/.hermes/skills/``.
- ``scripts/hermes/persona-orchestrator.sh`` (Chunk B) reads it to enumerate the
  skill set for fan-out reports.

See: docs/architecture/hermes-cross-agent-handoff.md (Chunk A)
"""
from __future__ import annotations

import json
from typing import Any

from .. import Registry

filename = "hermes.skills.json"


def _hermes_skills(registry: Registry) -> list[dict[str, Any]]:
    """Skills explicitly tagged for Hermes.

    Mirrors ``Registry.canonical_for_agent("hermes")`` for canonical skills
    (which already covers the ``"all" OR agent`` rule), then additionally
    surfaces aliases whose own ``agents`` list opts into Hermes — so a thin
    alias can route a hermes-only entrypoint to a canonical skill.
    """
    out: list[dict[str, Any]] = []
    for skill in registry.skills:
        agents = skill.get("agents") or []
        if "hermes" not in agents:
            continue
        out.append(skill)
    return out


def render(registry: Registry) -> str:
    """Return the JSON manifest of skills explicitly tagged for Hermes.

    Output shape::

        {
          "skills": [
            {"name": ..., "path": ..., "domain": ..., "lifecycle_phase": ..., ...},
            ...
          ]
        }

    The entry carries the full registry record so consumers (symlink plan,
    persona orchestrator) have everything they need without re-loading the
    registry.  Output is deterministic: entries are sorted by name, and JSON
    is dumped with ``sort_keys=False`` so dict field order stays stable across
    runs (idempotency contract).
    """
    skills = sorted(_hermes_skills(registry), key=lambda s: s.get("name", ""))
    payload: dict[str, Any] = {"skills": skills}
    return json.dumps(payload, indent=2, ensure_ascii=False)
