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


class TestNegativeTriggerVeto:
    """WO-AWIKI-SKILLECO-16 — negative_triggers veto routing.

    Issue #76: the router must be able to express "NOT for this input"
    (e.g. caveman never auto-compresses security evidence) in routing data.
    """

    def test_negative_trigger_vetoes_positive_hit(self):
        reg = _reg(
            {"name": "compact-style",
             "description": "compact output style for low-risk prose",
             "domain": "style", "triggers": ["summarize"],
             "negative_triggers": ["security evidence"], "invocation_hint": "/x"},
        )
        hits = routing.route(reg, "summarize the security evidence log")
        assert "compact-style" not in [h[0] for h in hits], (
            "negative trigger must veto the skill even with a positive hit")

    def test_negative_trigger_vetoes_description_fallback(self):
        reg = _reg(
            {"name": "compact-style",
             "description": "excel invoice generator security evidence tool",
             "domain": "style", "triggers": [],
             "negative_triggers": ["security evidence"], "invocation_hint": "/x"},
        )
        hits = routing.route(reg, "generate security evidence excel invoice")
        assert "compact-style" not in [h[0] for h in hits], (
            "veto must also block the description-fallback tier")

    def test_absent_negative_triggers_routes_normally(self):
        reg = _reg({"name": "plain", "description": "compact prose",
                    "domain": "style", "triggers": ["summarize"],
                    "invocation_hint": "/x"})
        assert routing.route(reg, "summarize this")[0][0] == "plain"

    def test_negative_without_positive_is_noop(self):
        reg = _reg({"name": "never-matches",
                    "description": "unrelated thing",
                    "domain": "d", "triggers": [],
                    "negative_triggers": ["security"], "invocation_hint": "/x"})
        hits = routing.route(reg, "totally unrelated words here")
        assert "never-matches" not in [h[0] for h in hits], (
            "vetoed skill must never surface, even via the a-flow spine default")


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
