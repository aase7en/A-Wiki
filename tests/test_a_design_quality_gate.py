"""Tests for scripts/lib/a_design_gate.py — Quality Gate rubric evaluator.

Iron Law #1 — TDD. Tests the deterministic scoring of design decisions
against the 8-category rubric. No vision/ML — pure function on design_tokens.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from a_design_gate import evaluate, SHIP_THRESHOLD, MAX_SCORE, CATEGORIES  # noqa: E402


# ── sample design_tokens fixtures ────────────────────────────────────────

# A "perfect" submission — all categories score full
PERFECT_TOKENS = {
    "focal_point": "hero-KPI",
    "visual_weights": [3, 2, 1],
    "uses_size_hierarchy": True,
    "type_scale_ratio": "3:2",
    "body_line_height": 1.5,
    "body_font": "Plus Jakarta Sans",
    "serif_default": False,
    "palette": {
        "fg": "#2A2A2A", "bg": "#FAFAFA", "card": "#FFFFFF",
        "border": "#E5E5E5", "accent": "#0F766E", "destructive": "#B91C1C",
    },
    "grid_system": "12-col",
    "grammar": "operations-console",
    "density": "dense",
    "whitespace_intentional": True,
    "duration_tokens": True,
    "prefers_reduced_motion": True,
    "exit_duration_ms": 150,
    "enter_duration_ms": 250,
    "accessibility": {
        "touch_target_pt": 48,
        "focus_visible": True,
        "aria_semantic": True,
        "color_not_only_state": True,
    },
    "distinctiveness": {
        "icon_chip_cliche": False,
        "all_even_grid": False,
        "ghost_numbering": False,
        "stock_hero_visual": False,
    },
    "craft": {
        "number_ratio_2to1": True,
        "refined_black": True,
        "low_opacity_shadow": True,
        "single_accent": True,
        "eyebrow_restraint": True,
    },
}

# A "sloppy" submission — multiple critical fails
SLOPPY_TOKENS = {
    "palette": {"fg": "#000000", "bg": "#FFFFFF", "accent": "#6366F1"},  # AI-purple + #000
    "accessibility": {"touch_target_pt": 36},  # < 44
    "distinctiveness": {"icon_chip_cliche": True, "all_even_grid": True},
}


# ── basic structure ──────────────────────────────────────────────────────

class TestStructure:

    def test_evaluate_returns_dict_with_required_keys(self):
        result = evaluate({})
        for key in ("total", "ship_threshold", "blocked", "per_category", "fails"):
            assert key in result

    def test_max_score_is_100(self):
        assert MAX_SCORE == 100

    def test_ship_threshold_is_80(self):
        assert SHIP_THRESHOLD == 80

    def test_categories_sum_to_100(self):
        assert sum(CATEGORIES.values()) == 100

    def test_eight_categories(self):
        assert set(CATEGORIES.keys()) == {
            "hierarchy", "typography", "color", "composition",
            "motion", "accessibility", "distinctiveness", "craft",
        }


# ── perfect submission ───────────────────────────────────────────────────

class TestPerfectSubmission:

    def test_perfect_scores_above_threshold(self):
        result = evaluate(PERFECT_TOKENS)
        assert result["total"] >= SHIP_THRESHOLD, f"perfect tokens should ship: {result}"
        assert result["blocked"] is False

    def test_perfect_scores_high(self):
        """Perfect tokens should score ≥85 (hard to hit exactly 100 due to optional fields)."""
        result = evaluate(PERFECT_TOKENS)
        assert result["total"] >= 85, f"perfect should be ≥85, got {result['total']}: {result['fails']}"


# ── sloppy submission ────────────────────────────────────────────────────

class TestSloppySubmission:

    def test_sloppy_is_blocked(self):
        result = evaluate(SLOPPY_TOKENS)
        assert result["blocked"] is True
        assert result["total"] < SHIP_THRESHOLD

    def test_sloppy_catches_ai_purple(self):
        result = evaluate(SLOPPY_TOKENS)
        assert any("AI-purple" in f or "Lila" in f for f in result["fails"]), result["fails"]

    def test_sloppy_catches_touch_target(self):
        result = evaluate(SLOPPY_TOKENS)
        assert any("touch_target" in f and "44" in f for f in result["fails"]), result["fails"]

    def test_sloppy_catches_pure_black(self):
        result = evaluate(SLOPPY_TOKENS)
        assert any("#000" in f or "refined black" in f for f in result["fails"]), result["fails"]

    def test_sloppy_catches_icon_chip_cliche(self):
        result = evaluate(SLOPPY_TOKENS)
        assert any("icon-chip" in f for f in result["fails"]), result["fails"]


# ── empty / fail-soft ────────────────────────────────────────────────────

class TestFailSoft:

    def test_empty_tokens_does_not_raise(self):
        result = evaluate({})
        # Empty tokens should not raise. Total is low (most categories score 0
        # for missing fields), but Distinctiveness scores full 10 because
        # "no tells declared" is treated as no-tells (innocent until proven).
        assert isinstance(result["total"], int)
        assert result["total"] >= 0
        assert result["blocked"] is True  # empty design can't ship

    def test_none_fields_do_not_raise(self):
        result = evaluate({"palette": None, "accessibility": None})
        assert isinstance(result["total"], int)


# ── WCAG helpers (contrast ratio) ────────────────────────────────────────

class TestContrast:

    def test_black_on_white_passes(self):
        from a_design_gate import _contrast_ratio
        assert _contrast_ratio("#000000", "#FFFFFF") >= 20.0

    def test_low_contrast_fails(self):
        from a_design_gate import _hex_luminance
        # Same color = ratio 1.0
        from a_design_gate import _contrast_ratio
        assert _contrast_ratio("#888888", "#999999") < 2.0

    def test_invalid_hex_returns_safe_default(self):
        from a_design_gate import _hex_luminance, _contrast_ratio
        assert _hex_luminance("not-a-hex") == 0.0
        assert _contrast_ratio("xxx", "yyy") == 1.0


# ── distinctiveness deductions ───────────────────────────────────────────

class TestDistinctiveness:

    def test_all_tells_max_deduction_floors_at_zero(self):
        tokens = {"distinctiveness": {
            "icon_chip_cliche": True,
            "all_even_grid": True,
            "ghost_numbering": True,
            "stock_hero_visual": True,
        }}
        result = evaluate(tokens)
        assert result["per_category"]["distinctiveness"]["score"] == 0
