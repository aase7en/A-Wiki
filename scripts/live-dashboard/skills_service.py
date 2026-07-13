"""Skills service for the Live Dashboard.

Reads skills-registry.json and answers filtered/queried views for the
"🧩 Skills" dashboard tab. Per-agent visibility uses the registry's
canonical_for_agent() logic — the dashboard only shows skills an agent can
actually invoke.

Caching: the registry is loaded lazily and reloaded when the file mtime
changes, so edits to skills-registry.json show up on the next request without
restarting the server.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry  # noqa: E402

REGISTRY_FILE = REPO_ROOT / "skills-registry.json"

# Known agents — used for the agent dropdown + skill_count per agent.
KNOWN_AGENTS = ["all", "claude", "codex", "zcode", "gemini", "antigravity",
                "hermes", "kilo", "cline", "cursor", "windsurf", "openclaw"]

# Fields exposed in list view (compact). Detail view returns everything.
LIST_FIELDS = (
    "name", "domain", "lifecycle_phase", "category", "invocation",
    "th_description", "when_to_use", "agents", "status", "path",
)

_cache: dict[str, Any] = {"registry": None, "mtime": 0.0, "loaded": 0.0}


def _load_registry() -> Registry:
    """Lazily load + cache the registry; reload when file mtime changes."""
    try:
        mtime = REGISTRY_FILE.stat().st_mtime
    except OSError:
        mtime = 0.0
    now = time.time()
    if _cache["registry"] is None or mtime != _cache["mtime"]:
        try:
            _cache["registry"] = Registry.load(REGISTRY_FILE)
            _cache["mtime"] = mtime
            _cache["loaded"] = now
        except Exception:
            # Keep last good cache if reload fails — never crash the server.
            if _cache["registry"] is None:
                raise
    return _cache["registry"]


def _skill_list_item(skill: dict[str, Any]) -> dict[str, Any]:
    """Compact view of a skill for the list endpoint."""
    return {k: skill.get(k) for k in LIST_FIELDS}


def _matches_query(skill: dict[str, Any], q: str) -> bool:
    """Case-insensitive substring match across name + th_description + when_to_use."""
    if not q:
        return True
    q_lower = q.lower()
    haystack = " ".join(
        str(skill.get(k, "")) for k in ("name", "th_description", "when_to_use")
    ).lower()
    return q_lower in haystack


def _stats(skills: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate counts for filter chips in the UI."""
    by_domain: dict[str, int] = {}
    by_invocation: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    has_thai = 0
    for s in skills:
        domains = s.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        for d in domains:
            by_domain[d] = by_domain.get(d, 0) + 1
        inv = s.get("invocation") or "manual"
        by_invocation[inv] = by_invocation.get(inv, 0) + 1
        agents = s.get("agents") or []
        if "all" in agents:
            for a in KNOWN_AGENTS:
                if a != "all":
                    by_agent[a] = by_agent.get(a, 0) + 1
        else:
            for a in agents:
                by_agent[a] = by_agent.get(a, 0) + 1
        if s.get("th_description"):
            has_thai += 1
    return {
        "total": len(skills),
        "by_domain": dict(sorted(by_domain.items(), key=lambda kv: -kv[1])),
        "by_invocation": by_invocation,
        "by_agent": dict(sorted(by_agent.items(), key=lambda kv: -kv[1])),
        "has_thai": has_thai,
    }


def list_skills(query_string: str = "") -> dict[str, Any]:
    """GET /api/skills — filtered list view.

    Query params:
      agent=<name>       — only skills visible to that agent (uses canonical_for_agent)
      invocation=auto|manual|both
      domain=<d>         — domain filter (matches any of the skill's domains)
      q=<text>           — substring search across name + th_description + when_to_use
      limit=<n>          — cap results (default 500)
    """
    params = parse_qs(query_string)
    agent = (params.get("agent", ["all"])[0]).lower()
    invocation = params.get("invocation", [None])[0]
    domain = params.get("domain", [None])[0]
    q = params.get("q", [""])[0]
    try:
        limit = int(params.get("limit", ["500"])[0])
    except ValueError:
        limit = 500

    reg = _load_registry()

    # Per-agent visibility: canonical_for_agent already handles the "all" list.
    if agent and agent != "all":
        allowed_names = {s["name"] for s in reg.canonical_for_agent(agent)}
        skills = [s for s in reg.skills if s.get("name") in allowed_names]
    else:
        skills = [s for s in reg.skills if s.get("status") == "canonical"]

    # Apply filters
    if invocation:
        skills = [s for s in skills if (s.get("invocation") or "manual") == invocation]
    if domain:
        skills = [
            s for s in skills
            if domain in (s.get("domain") if isinstance(s.get("domain"), list)
                          else [s.get("domain")] if s.get("domain") else [])
        ]
    skills = [s for s in skills if _matches_query(s, q)]

    # Sort: has Thai first (most useful), then alphabetical
    skills.sort(key=lambda s: (not bool(s.get("th_description")), s.get("name", "")))

    items = [_skill_list_item(s) for s in skills[:limit]]
    return {
        "skills": items,
        "count": len(items),
        "total_matched": len(skills),
        "filters": {"agent": agent, "invocation": invocation, "domain": domain, "q": q},
        "stats": _stats(skills),
        "agents": KNOWN_AGENTS,
        "loaded_at": _cache["loaded"],
    }


def get_skill(name: str) -> dict[str, Any] | None:
    """GET /api/skills/<name> — full detail for one skill."""
    reg = _load_registry()
    skill = reg.get(name)
    if skill is None:
        return None
    # Resolve alias → canonical metadata for display
    return skill


def agent_overview() -> dict[str, Any]:
    """GET /api/skills/agents — per-agent skill counts + which agents exist."""
    reg = _load_registry()
    canonical = [s for s in reg.skills if s.get("status") == "canonical"]
    counts = {}
    for agent in KNOWN_AGENTS:
        if agent == "all":
            counts[agent] = len(canonical)
        else:
            counts[agent] = len(reg.canonical_for_agent(agent))
    return {
        "agents": KNOWN_AGENTS,
        "skill_counts": counts,
        "total_canonical": len(canonical),
    }


__all__ = ["list_skills", "get_skill", "agent_overview", "KNOWN_AGENTS"]
