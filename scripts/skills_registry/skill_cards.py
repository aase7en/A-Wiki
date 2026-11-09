"""Compact read-only cards over the canonical skill registry and route().

This module deliberately does not duplicate matching, register hooks, execute skills,
or load SKILL.md bodies. It is an optional small discovery view (WO-AWIKI-76-01).
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from . import routing


DEFAULT_CORE = (
    "a-router", "a-fasttask", "a-debug", "a-plan",
    "a-council", "token-optimization", "grill-with-docs", "a-research",
)


def _purpose(description: Any, fallback: str, max_chars: int = 220) -> str:
    clean = re.sub(r"\s+", " ", str(description or fallback)).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip(" ,.;:") + "…"


def _card(skill: dict[str, Any], *, match: str, score: int,
          auto_load_candidate: bool) -> dict[str, Any]:
    raw = skill.get("triggers") or []
    triggers = [t.strip() for t in raw if isinstance(t, str) and t.strip()][:3]
    negative = skill.get("do_not_use_when")
    if not isinstance(negative, str) or not negative.strip():
        negative = "NOT_SPECIFIED_IN_REGISTRY"
    return {
        "name": skill["name"],
        "status": "canonical",
        "purpose": _purpose(skill.get("description"), skill["name"]),
        "use_when": triggers,
        "do_not_use_when": negative,
        "risk_policy": "NOT_VERIFIED",
        "invocation_hint": skill.get("invocation_hint") or "/" + skill["name"],
        "body_pointer": skill.get("path") or "",
        "match": match,
        "score": score,
        "auto_load_candidate": auto_load_candidate,
    }


def build_cards(registry: Any, query: str | None = None, *, limit: int = 3,
                core_names: Sequence[str] = DEFAULT_CORE) -> dict[str, Any]:
    """Provide <=3 ranked query cards, or <=10 non-executing core cards.

    Caller must still apply actual harness capability, risk and owner approval.
    auto_load_candidate is a *read-the-skill-body* hint, never execution permission.
    """
    is_query = query is not None
    capped = max(1, min(int(limit), 3 if is_query else 10))
    skills = {s["name"]: s for s in (getattr(registry, "skills", []) or [])
              if isinstance(s, dict) and s.get("status") == "canonical"
              and isinstance(s.get("name"), str)}
    cards = []
    if not is_query:
        for name in core_names:
            if name in skills:
                cards.append(_card(skills[name], match="CORE_CATALOG", score=0,
                                   auto_load_candidate=False))
            if len(cards) >= capped:
                break
        decision = "DISCOVER_ONLY"
    else:
        hits = routing.route(registry, str(query), limit=capped)
        for name, route_score in hits:
            skill = skills.get(name)
            if skill is None:
                continue
            trigger_score = routing.match_score(skill.get("triggers") or [], str(query))
            explicit = trigger_score >= routing.DEFAULT_THRESHOLD
            can_load = explicit and skill.get("invocation") == "auto"
            cards.append(_card(skill,
                               match="EXPLICIT_TRIGGER" if explicit else
                                     ("SPINE_FALLBACK" if route_score == 0 else
                                      "DESCRIPTION_FALLBACK"),
                               score=route_score, auto_load_candidate=can_load))
        decision = ("AUTO_LOAD_CANDIDATE" if cards and cards[0]["auto_load_candidate"]
                    else "SUGGEST_ONLY" if cards else "NO_AUTO_SELECT")
    return {
        "source": "skills-registry.json via canonical routing.route",
        "decision": decision,
        "full_skill_bodies_loaded": 0,
        "cards": cards,
    }
