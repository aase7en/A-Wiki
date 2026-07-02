#!/usr/bin/env python3
"""
tag_hermes.py — add ``"hermes"`` to the ``agents`` list of skills Hermes (Pi5)
should see.
==============================================================================

This is a **heuristic tagger**, not an authority.  The single source of truth
is ``skills-registry.json``; this script just proposes + applies the default
Hermes tagging policy so the set stays small (~40-50) instead of the full 331
skills that free-tier Pi5 models can't preload.

Heuristic (from ``docs/architecture/hermes-cross-agent-handoff.md`` §A2)
----------------------------------------------------------------------
A canonical skill is tagged for Hermes iff ANY of:

1. ``lifecycle_phase`` is set and not ``none``
   (the 13 lifecycle skills — DEFINE→SHIP pipeline).
2. ``domain`` intersects the Telegram-relevant set
   ``{wiki, pharmacy, thai}`` (the ~20 skills exposed via Telegram bot).
3. ``name`` is in the explicit meta-skill allowlist below
   (router + ops skills Hermes should always know about).

It is IDEMPOTENT: re-running on an already-tagged registry is a no-op (it
never duplicates ``"hermes"`` and never removes a tag a human added).

Usage
-----
::

    # Show what WOULD change (default — safe, no writes).
    python scripts/skills_registry/tag_hermes.py

    # Apply the changes to skills-registry.json in place.
    python scripts/skills_registry/tag_hermes.py --apply

    # Apply, then regenerate all surfaces so hermes.skills.json reflects it.
    python scripts/skills_registry/tag_hermes.py --apply --regen

Exit codes
----------
- 0 = success (or no changes needed)
- 1 = registry invalid (refuse to touch a broken file)

See: docs/architecture/hermes-cross-agent-handoff.md (Chunk A2)
     docs/architecture/skill-architecture-plan.md (the 5-layer contract)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import validate_registry  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"

# Domains exposed to Hermes because they're reachable via the Telegram bot
# (Pi5 runs the gateway 24/7).  See handoff §A2 + lifecycle-config.json.
TELEGRAM_DOMAINS: frozenset[str] = frozenset({"wiki", "pharmacy", "thai"})

# Explicit allowlist of meta/ops skills Hermes should always know about,
# independent of lifecycle/domain heuristics.  Handoff §A2.
META_ALLOWLIST: frozenset[str] = frozenset({
    "awiki-lifecycle-router",
    "a-wiki-telegram",
    "wiki-search-local",
    "ingest-source",
    "lint-wiki",
    "delegate-subagent",
    "debug-mantra",
    "scrutinize",
    "post-mortem",
})


def _should_tag(skill: dict) -> tuple[bool, str | None]:
    """Return (tag?, reason) for one skill dict, per the heuristic above.

    Only canonical skills are eligible: aliases/deprecated re-route to a
    canonical that already carries its own agents decision.
    """
    if skill.get("status") != "canonical":
        return False, None

    name = skill.get("name", "")

    phase = skill.get("lifecycle_phase")
    if phase and phase != "none":
        return True, f"lifecycle_phase={phase!r}"

    domains = set(skill.get("domain") or [])
    hit = domains & TELEGRAM_DOMAINS
    if hit:
        return True, f"telegram domain={sorted(hit)!r}"

    if name in META_ALLOWLIST:
        return True, "meta-skill allowlist"

    return False, None


def _ensure_hermes(agents: list[str]) -> list[str]:
    """Idempotently insert 'hermes' into an agents list (no dup)."""
    return agents if "hermes" in agents else [*agents, "hermes"]


def plan_changes(data: dict) -> list[dict]:
    """Return the list of {name, before, after, reason} for skills to change.

    Idempotent: a skill already carrying 'hermes' yields no change.
    """
    changes: list[dict] = []
    for skill in data.get("skills", []):
        should, reason = _should_tag(skill)
        if not should:
            continue
        before = list(skill.get("agents") or [])
        after = _ensure_hermes(before)
        if before == after:
            continue  # already tagged (by a human earlier, or a prior run)
        changes.append({
            "name": skill.get("name", "<unnamed>"),
            "before": before,
            "after": after,
            "reason": reason,
        })
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[1] if __doc__ else "Tag skills for Hermes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Apply the changes to skills-registry.json (default: dry-run).",
    )
    ap.add_argument(
        "--regen", action="store_true",
        help="After --apply, run scripts/regen-skill-surfaces.py to refresh surfaces.",
    )
    a = ap.parse_args()

    errors = validate_registry(REGISTRY_PATH)
    if errors:
        print("🚨 skills-registry.json is invalid — refusing to tag:", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
        return 1

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    changes = plan_changes(data)

    if not changes:
        n_tagged = sum(
            1 for s in data["skills"]
            if "hermes" in (s.get("agents") or [])
        )
        print(f"✅ No changes needed — {n_tagged} skill(s) already tagged for Hermes.")
        return 0

    print(f"Hermes tagging plan: {len(changes)} skill(s) to tag\n")
    for c in changes:
        print(f"  + {c['name']:35s}  ({c['reason']})")
        print(f"      {c['before']}  →  {c['after']}")

    if not a.apply:
        print(f"\n[dry-run] {len(changes)} change(s) pending. Re-run with --apply to write.")
        return 0

    # Apply in place.
    applied = 0
    by_name = {s.get("name"): s for s in data["skills"]}
    for c in changes:
        skill = by_name[c["name"]]
        skill["agents"] = _ensure_hermes(list(skill.get("agents") or []))
        applied += 1

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\n✅ Applied {applied} tag(s) to {REGISTRY_PATH.relative_to(REPO_ROOT)}")

    if a.regen:
        import subprocess
        print("   Regenerating surfaces…")
        rc = subprocess.call(
            [sys.executable, str(REPO_ROOT / "scripts" / "regen-skill-surfaces.py")]
        )
        if rc != 0:
            print(f"   ⚠️  regen exited {rc}", file=sys.stderr)
            return rc
    else:
        print("   Run `python scripts/regen-skill-surfaces.py` to refresh surfaces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
