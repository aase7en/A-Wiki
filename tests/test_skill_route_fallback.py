"""Slice 2 — tiered skill discovery (TDD red-first).

Pain: routing covers only 17/243 skills (triggers); the other 226 are
findable ONLY by reading the 81KB SKILL-INDEX. Contract after this slice:
route() falls back to scoring over description+domain when triggers give
[] — agents CHOOSE skills lazily instead of loading the big index.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skills_registry.routing as routing  # noqa: E402


from types import SimpleNamespace


def _reg(*skills):
    return SimpleNamespace(skills=[dict(s, status="canonical") for s in skills])


class TestDescriptionFallback:
    def test_trigger_miss_falls_back_to_description(self):
        """A skill with NO triggers whose description matches the intent
        must be found — today route() returns [] and the agent is told to
        use a-think instead."""
        reg = _reg(
            {"name": "no-trigger-skill",
             "description": "Excel workbook generator for Thai invoices",
             "domain": "office", "triggers": [], "invocation_hint": "/excel"},
            {"name": "unrelated",
             "description": "Blender motion state inspection",
             "domain": "gamedev", "triggers": [], "invocation_hint": "/blender"},
        )
        hits = routing.route(reg, "generate thai invoice excel")
        assert hits, "description fallback must fire when triggers miss"
        assert hits[0][0] == "no-trigger-skill"

    def test_fallback_respects_threshold_no_garbage(self):
        reg = _reg({"name": "unrelated",
                    "description": "Blender motion inspection",
                    "domain": "gamedev", "triggers": []})
        hits = routing.route(reg, "kubernetes cluster upgrade")
        # 2026-08-22 tier-3: unmatched OBJECTIVES land on the default spine
        # by design — noise would be random skills scoring above it.
        assert hits == [("a-flow", 0)], (
            f"irrelevant query must yield only the default spine, got: {hits}")

    def test_trigger_hits_still_win_over_description(self):
        reg = _reg(
            {"name": "triggered", "description": "misc",
             "domain": "x", "triggers": ["deploy"], "invocation_hint": "/d"},
            {"name": "described",
             "description": "deploy deployment shipping release",
             "domain": "x", "triggers": [], "invocation_hint": "/s"},
        )
        hits = routing.route(reg, "deploy")
        assert hits[0][0] == "triggered", "explicit trigger outranks description"

    def test_real_registry_finds_beyond_a_suite(self):
        """On the real 243-skill registry, an intent that no A-suite trigger
        covers must surface a canonical skill via description (proves the
        226-skill blind spot is gone)."""
        from skills_registry import Registry
        reg = Registry.load(REPO_ROOT / "skills-registry.json")
        hits = routing.route(reg, "create powerpoint presentation from markdown")
        assert hits, "deck-generation intent must find a skill without the big index"
        assert any("slide" in h[0] or "pptx" in h[0] or "deck" in h[0]
                   for h in hits), [h[0] for h in hits]
