"""Skill tier consolidation — plan §3/§6.3 (auto-skill consolidation).

User vision: "แยกหมวดหมู่ให้ skill ถูกใช้ด้วยผู้ใช้น้อยที่สุด" —
the AUTO tier must be the default (agent pulls skills via routing tiers
1-3); MANUAL is reserved for the user's own domain-specific work
(hospital/government/private-business documents).

Invariants:
1. MANUAL budget: at most 18 canonical skills may keep invocation=manual —
   exactly the user-specific work list. Everything else is invocation=auto.
2. Catalog pruning: no canonical skill may live under skills/_upstream/
   or skills/ecosystem/ unless it is referenced (backticked) by a kept
   skill directory — unreferenced catalog copies are deprecated (grep-able,
   never deleted).
3. Deprecated entries always carry migrated_to + note (schema contract).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((REPO_ROOT / "skills-registry.json").read_text(encoding="utf-8"))
SKILLS = REGISTRY["skills"]

# งานเฉพาะตัว user (plan §3): เอกสาร รพ./ราชการ/ธุรกิจส่วนตัว
USER_SPECIFIC_MANUAL = {
    "a-doc", "a-med-order", "a-rabies-report", "a-escalate",
    "word-generator", "assessment-generator", "pharmacy-order-lookup",
    "thai-government-form", "thai-invoice", "thai-resume",
    "thai-festival-card", "monte-carlo-quant-analysis",
}

KEEP_DIRS = (
    "skills/awiki/", "skills/engineering-lifecycle/", "skills/claude-code/",
    "skills/claude-thai/", "skills/wiki/", "skills/delegation/",
    "skills/engineering/", "skills/mattpocock/", "skills/anthropic-skills/",
    "skills/gamedev-skills/",
)


def _bound_names() -> set[str]:
    names = {s["name"] for s in SKILLS}
    bound: set[str] = set()
    for d in KEEP_DIRS:
        for f in (REPO_ROOT / d).rglob("SKILL.md"):
            if not f.is_file():
                continue
            txt = f.read_text(encoding="utf-8", errors="ignore")
            bound |= set(re.findall(r"`([a-z][a-z0-9-]{2,})`", txt))
    return bound & names


def _canonical():
    return [s for s in SKILLS if s.get("status") == "canonical"]


def test_manual_tier_is_user_specific_and_small():
    manual = sorted(s["name"] for s in _canonical()
                    if s.get("invocation") == "manual")
    assert len(manual) <= 18, f"manual tier ballooned to {len(manual)}: {manual}"
    stray = [n for n in manual if n not in USER_SPECIFIC_MANUAL]
    assert not stray, f"non-user-specific skills still manual: {stray}"


def test_auto_tier_is_the_default():
    auto = [s for s in _canonical() if s.get("invocation") in (None, "both")]
    assert not auto, (
        f"{len(auto)} canonical skills have no explicit tier "
        f"(auto|manual): {[s['name'] for s in auto][:8]}")


def test_catalog_entries_must_be_bound_or_deprecated():
    bound = _bound_names()
    unbound = [s["name"] for s in _canonical()
               if str(s.get("path", "")).startswith(
                   ("skills/_upstream/", "skills/ecosystem/"))
               and s["name"] not in bound]
    assert not unbound, (
        f"unreferenced catalog copies still canonical: {unbound[:12]}")


def test_deprecated_entries_carry_migration_contract():
    for s in SKILLS:
        if s.get("status") == "deprecated":
            assert s.get("migrated_to"), f"{s['name']} deprecated without migrated_to"
            assert str(s.get("note", "")).strip(), f"{s['name']} deprecated without note"
