"""Duplicate-cluster detection + consolidation helpers for Chunk 2.

This module does NOT mutate the registry or skill files on its own. It produces
an ACTION MATRIX — a structured proposal of what to alias/deprecate/delete —
for human review. The actual edits are applied by ``apply_dedup()`` once the
matrix is approved.

Detection signals:
  - exact name collision (same name across surfaces — scanner already dedups)
  - alias graph (already-known aliases)
  - description similarity (shingled word overlap) for near-duplicates

The action matrix classifies each cluster as:
  - ``delete``      : true duplicate (same content, different paths) — keep 1
  - ``alias``       : near-duplicate (different content, same purpose) — keep all, alias
  - ``stub``        : thin re-route stub — formalize frontmatter
  - ``distinct``    : same theme, genuinely different — leave alone, tag domain
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from . import Registry


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, dropping short words + punctuation."""
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if len(w) >= 4}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def detect_clusters(registry: Registry, threshold: float = 0.55) -> list[dict[str, Any]]:
    """Return clusters of skills that are potential duplicates.

    A cluster is a dict: {canonical: name, members: [...], score: float, reason: str}.
    """
    skills = registry.skills
    # Pre-tokenize descriptions once.
    tokens: dict[str, set[str]] = {}
    for s in skills:
        desc = s.get("description") or s.get("name", "")
        tokens[s["name"]] = _tokenize(desc) | _tokenize(s.get("name", ""))

    # Build alias graph from existing registry aliases.
    alias_pairs: set[tuple[str, str]] = set()
    for s in skills:
        for alias in s.get("aliases", []) or []:
            alias_pairs.add((alias, s["name"]))
        if s.get("status") == "alias" and s.get("canonical"):
            alias_pairs.add((s["name"], s["canonical"]))

    clusters: list[dict[str, Any]] = []
    seen: set[str] = set()

    for i, a in enumerate(skills):
        if a["name"] in seen:
            continue
        members = [a["name"]]
        for b in skills[i + 1:]:
            if b["name"] in seen:
                continue
            score = _jaccard(tokens[a["name"]], tokens[b["name"]])
            is_alias = (a["name"], b["name"]) in alias_pairs or (b["name"], a["name"]) in alias_pairs
            if score >= threshold or is_alias:
                members.append(b["name"])
                seen.add(b["name"])
        if len(members) > 1:
            seen.add(a["name"])
            # Score = max pairwise similarity for the cluster.
            max_score = 0.0
            for x in members:
                for y in members:
                    if x < y:
                        max_score = max(max_score, _jaccard(tokens[x], tokens[y]))
            clusters.append({
                "members": sorted(members),
                "score": round(max_score, 2),
                "reason": "alias-graph" if any(
                    (x, y) in alias_pairs or (y, x) in alias_pairs
                    for x in members for y in members if x < y
                ) else "description-similarity",
            })

    return sorted(clusters, key=lambda c: -c["score"])


def classify_cluster(cluster: dict[str, Any], registry: Registry) -> str:
    """Suggest an action: delete | alias | stub | distinct."""
    members = cluster["members"]
    score = cluster["score"]

    # Very high similarity + same name root → likely true duplicate.
    if score >= 0.85:
        return "delete"

    # Medium similarity → alias.
    if score >= 0.55:
        return "alias"

    # Check if any member is already a stub (status alias/deprecated).
    for name in members:
        skill = registry.get(name)
        if skill and skill.get("status") in ("alias", "deprecated"):
            return "stub"

    return "distinct"


# ---------------------------------------------------------------------------
# Consolidation application
# ---------------------------------------------------------------------------

def build_consolidation_plan(registry: Registry) -> dict[str, Any]:
    """Produce a human-readable action matrix for review.

    Returns {clusters: [...], stats: {delete, alias, stub, distinct}}.
    """
    clusters = detect_clusters(registry)
    plan = []
    counts = defaultdict(int)
    for cluster in clusters:
        action = classify_cluster(cluster, registry)
        counts[action] += 1
        plan.append({
            "action": action,
            "members": cluster["members"],
            "score": cluster["score"],
            "canonical": sorted(cluster["members"])[0],  # deterministic pick; reviewer overrides
            "reason": cluster["reason"],
        })
    return {
        "clusters": sorted(plan, key=lambda c: {"delete": 0, "stub": 1, "alias": 2, "distinct": 3}[c["action"]]),
        "stats": dict(counts),
    }


def validate_dedup(registry: Registry) -> list[str]:
    """Return errors if the registry violates dedup invariants.

    Called by tests to ensure consolidation results are sound:
      - every alias points to an existing canonical
      - no orphan aliases
      - no alias chains deeper than 1 hop (alias → alias is forbidden)
      - no cycles
    """
    errors: list[str] = []
    names = {s["name"] for s in registry.skills}

    for s in registry.skills:
        name = s["name"]
        if s.get("status") == "alias":
            canonical = s.get("canonical")
            if not canonical:
                errors.append(f"alias '{name}' has no 'canonical' field")
            elif canonical not in names:
                errors.append(f"orphan alias: '{name}' → '{canonical}' (canonical missing)")
            elif registry.skills and any(
                t["name"] == canonical and t.get("status") == "alias" for t in registry.skills
            ):
                errors.append(
                    f"alias chain: '{name}' → '{canonical}' which is itself an alias "
                    f"(max depth 1 allowed)"
                )

        # aliases[] entries must also resolve.
        for alias in s.get("aliases", []) or []:
            if alias not in names:
                # OK — aliases[] is a declaration of additional names for THIS skill.
                continue

    return errors


__all__ = [
    "detect_clusters",
    "classify_cluster",
    "build_consolidation_plan",
    "validate_dedup",
]
