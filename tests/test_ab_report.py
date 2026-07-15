"""Tests for scripts/eval/ab_report.py — A/B phase comparison + recommendation (R4)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import ab_report  # noqa: E402  -- module under test (created by R4)


# ---------------------------------------------------------------------------
# 1. compare_phases requires min_samples
# ---------------------------------------------------------------------------
def test_compare_phases_requires_min_samples():
    """Below min_samples → verdict 'insufficient_data'."""
    stats_a = {"count": 5, "pass": 4, "pass_rate": 0.8}
    stats_b = {"count": 3, "pass": 1, "pass_rate": 0.33}
    result = ab_report.compare_phases(stats_a, stats_b, min_samples=10)
    assert result["verdict"] == "insufficient_data"
    assert "need more samples" in result["reason"].lower() or "insufficient" in result["reason"].lower()


# ---------------------------------------------------------------------------
# 2. compare_phases picks the higher pass_rate
# ---------------------------------------------------------------------------
def test_compare_phases_picks_higher_rate():
    stats_a = {"count": 20, "pass": 16, "pass_rate": 0.80}
    stats_b = {"count": 20, "pass": 10, "pass_rate": 0.50}
    result = ab_report.compare_phases(stats_a, stats_b, min_samples=10)
    assert result["verdict"] == "champion_wins"
    assert result["winner"] == "A"
    assert result["delta"] == pytest.approx(0.30, abs=0.01)


def test_compare_phases_challenger_wins():
    stats_a = {"count": 20, "pass": 8, "pass_rate": 0.40}
    stats_b = {"count": 20, "pass": 18, "pass_rate": 0.90}
    result = ab_report.compare_phases(stats_a, stats_b, min_samples=10)
    assert result["verdict"] == "challenger_wins"
    assert result["winner"] == "B"


# ---------------------------------------------------------------------------
# 3. compare_phases flat (within noise threshold)
# ---------------------------------------------------------------------------
def test_compare_phases_flat_within_noise():
    stats_a = {"count": 20, "pass": 15, "pass_rate": 0.75}
    stats_b = {"count": 20, "pass": 14, "pass_rate": 0.70}
    result = ab_report.compare_phases(stats_a, stats_b, min_samples=10, noise_threshold=0.10)
    assert result["verdict"] == "flat"
    assert "no significant difference" in result["reason"].lower() or "within noise" in result["reason"].lower()


# ---------------------------------------------------------------------------
# 4. recommend — only after experiment is complete
# ---------------------------------------------------------------------------
def test_recommend_only_after_total_phases():
    """An incomplete experiment → no recommendation."""
    exp = {"subagent": "x", "champion": "a", "challenger": "b",
           "phase_size": 20, "total_phases": 4}
    state = {"x": {"invocations": 40}}  # 40 < 80 → not complete
    result = ab_report.recommend(exp, state, stats_a={"count": 20, "pass_rate": 0.8},
                                 stats_b={"count": 20, "pass_rate": 0.5})
    assert result["verdict"] == "incomplete"
    assert "not yet complete" in result["reason"].lower() or "incomplete" in result["reason"].lower()


def test_recommend_complete_picks_winner():
    exp = {"subagent": "x", "champion": "a", "challenger": "b",
           "phase_size": 20, "total_phases": 4}
    state = {"x": {"invocations": 80}}  # complete
    result = ab_report.recommend(exp, state, stats_a={"count": 20, "pass_rate": 0.9},
                                 stats_b={"count": 20, "pass_rate": 0.4})
    assert result["verdict"] == "champion_wins"
    assert result["recommended_model"] == "a"
