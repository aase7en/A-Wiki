"""Tests for the design_quality_gate MCP tool registration + dispatch.

Verifies the tool is registered in neural_spine_mcp.TOOLS, has the correct
schema, and dispatches to a_design_gate.evaluate() correctly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import neural_spine_mcp as ns  # noqa: E402


# ── registration ──────────────────────────────────────────────────────────

class TestRegistration:

    def test_tool_is_registered(self):
        assert "design_quality_gate" in ns.TOOLS

    def test_tool_has_required_fields(self):
        tool = ns.TOOLS["design_quality_gate"]
        for key in ("fn", "description", "inputSchema"):
            assert key in tool, f"missing {key}"

    def test_fn_is_callable(self):
        assert callable(ns.TOOLS["design_quality_gate"]["fn"])

    def test_design_tokens_required_in_schema(self):
        schema = ns.TOOLS["design_quality_gate"]["inputSchema"]
        assert "design_tokens" in schema.get("required", [])

    def test_ship_threshold_optional_with_default(self):
        """ship_threshold is optional (default 80 applied by handler)."""
        schema = ns.TOOLS["design_quality_gate"]["inputSchema"]
        assert "ship_threshold" not in schema.get("required", [])
        props = schema.get("properties", {})
        assert props.get("ship_threshold", {}).get("default") == 80

    def test_description_mentions_8_categories(self):
        """Description should advertise the 8-category rubric so callers know."""
        desc = ns.TOOLS["design_quality_gate"]["description"]
        for keyword in ("Hierarchy", "Typography", "Color", "Composition",
                        "Motion", "Accessibility", "Distinctiveness", "Craft"):
            assert keyword in desc, f"description missing category: {keyword}"


# ── dispatch ─────────────────────────────────────────────────────────────

PERFECT_TOKENS = {
    "focal_point": "hero", "visual_weights": [3, 2, 1], "uses_size_hierarchy": True,
    "type_scale_ratio": "3:2", "body_line_height": 1.5, "body_font": "Plus Jakarta Sans",
    "serif_default": False,
    "palette": {"fg": "#2A2A2A", "bg": "#FAFAFA", "card": "#FFF",
                "border": "#E5E5E5", "accent": "#0F766E", "destructive": "#B91C1C"},
    "grid_system": "12-col", "grammar": "operations-console", "density": "dense",
    "whitespace_intentional": True, "duration_tokens": True, "prefers_reduced_motion": True,
    "exit_duration_ms": 150, "enter_duration_ms": 250,
    "accessibility": {"touch_target_pt": 48, "focus_visible": True,
                      "aria_semantic": True, "color_not_only_state": True},
    "distinctiveness": {"icon_chip_cliche": False, "all_even_grid": False,
                        "ghost_numbering": False, "stock_hero_visual": False},
    "craft": {"number_ratio_2to1": True, "refined_black": True,
              "low_opacity_shadow": True, "single_accent": True,
              "eyebrow_restraint": True},
}


class TestDispatch:

    def test_dispatch_perfect_tokens_passes(self):
        fn = ns.TOOLS["design_quality_gate"]["fn"]
        result = fn({"design_tokens": PERFECT_TOKENS})
        assert result["total"] >= 80
        assert result["blocked"] is False

    def test_dispatch_empty_tokens_blocked(self):
        fn = ns.TOOLS["design_quality_gate"]["fn"]
        result = fn({"design_tokens": {}})
        assert result["blocked"] is True
        assert result["total"] < 80

    def test_dispatch_returns_per_category(self):
        fn = ns.TOOLS["design_quality_gate"]["fn"]
        result = fn({"design_tokens": {}})
        for cat in ("hierarchy", "typography", "color", "composition",
                    "motion", "accessibility", "distinctiveness", "craft"):
            assert cat in result["per_category"]
            assert "score" in result["per_category"][cat]
            assert "max" in result["per_category"][cat]
            assert "fails" in result["per_category"][cat]

    def test_dispatch_custom_threshold_applied(self):
        """ship_threshold override should change blocked flag."""
        fn = ns.TOOLS["design_quality_gate"]["fn"]
        # Perfect scores 100 → threshold 96 still passes
        result = fn({"design_tokens": PERFECT_TOKENS, "ship_threshold": 96})
        assert result["ship_threshold"] == 96
        assert result["blocked"] is False
        # Threshold 101 → impossible to pass
        result_impossible = fn({"design_tokens": PERFECT_TOKENS, "ship_threshold": 101})
        assert result_impossible["blocked"] is True

    def test_dispatch_missing_design_tokens_does_not_crash(self):
        """If caller omits design_tokens, default to empty (fail-soft)."""
        fn = ns.TOOLS["design_quality_gate"]["fn"]
        result = fn({})
        assert "total" in result
        assert result["blocked"] is True


# ── regression: TOOLS dict integrity ─────────────────────────────────────

class TestToolsDictIntegrity:

    def test_other_tools_still_present(self):
        """Adding design_quality_gate must not have removed other tools."""
        for must in ("memory_recall", "memory_remember", "bb_post", "bb_read",
                     "task_add", "task_claim", "task_release", "skill_route",
                     "focus_set", "focus_advance", "claim_acquire", "claim_release"):
            assert must in ns.TOOLS, f"registration broke: {must} missing"

    def test_all_tools_have_callable_fn(self):
        for name, tool in ns.TOOLS.items():
            assert callable(tool.get("fn")), f"{name} has no callable fn"
