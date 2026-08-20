"""Entry gate — the continuity gate as a machine verdict (read-only).

GO/NO-GO before an agent starts a topic:
  1. COLLAB.md readable?                      -> collab_read
  2. topic conflicts a live claim/branch?     -> no_conflict (+ conflicts[])
  3. a claim row is suggested for the agent   -> claim_row (best-effort)
"""
from __future__ import annotations

import re
from pathlib import Path

from .state import parse_claims, list_branches


def _slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")


def entry_gate(repo_root: Path | None = None, topic: str = "",
               agent: str = "unknown") -> dict:
    root = Path(repo_root) if repo_root else Path.cwd()
    collab = root / "COLLAB.md"
    claims = parse_claims(collab)
    branches = list_branches(root)

    topic_slug = _slug(topic)
    conflicts: list[str] = []
    for c in claims:
        hay = " ".join([c["chunk"], c["branch"], c["scope"]]).lower()
        if topic_slug and (topic_slug in hay.replace("|", "-") or
                           topic.lower() in hay):
            conflicts.append(f"{c['chunk']} (agent={c['agent'] or '?'}, "
                             f"branch={c['branch'] or '?'})")
    for b in branches:
        if topic_slug and topic_slug in b.lower():
            conflicts.append(f"branch:{b}")

    checks = {
        "collab_read": collab.is_file(),
        "no_conflict": not conflicts,
        "agent_named": bool(agent and agent != "unknown"),
    }
    verdict = "GO" if all(checks.values()) else "NO-GO"
    claim_row = (f"| {topic_slug or 'task'} | {agent} | today | <scope> | "
                 f"<branch> |")
    return {"verdict": verdict, "checks": checks, "conflicts": conflicts,
            "claim_row": claim_row, "topic": topic, "agent": agent}
