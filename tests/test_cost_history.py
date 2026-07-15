"""Tests for scripts/live-dashboard/cost_history.py — cost-aware aggregation (S6).

Iron Law #1: failing tests written FIRST. These pin the contract of
collect_cost_history() / to_cost_chart_series() / model_cost_summary()
before the implementation exists.

S6 ใช้ COST_MATRIX (จาก cost-router.py) + token counts (จาก S6.0)
เพื่อ estimate USD per run per model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import cost_history  # noqa: E402  -- module under test (created by S6)


def _make_result_with_tokens(suite: str, model: str, tokens_in: int, tokens_out: int) -> dict:
    """สร้าง result file payload ที่มี tokens (S6.0 schema).

    Schema: {<suite>: {by_model: {<model>: {tokens_in, tokens_out, ...}}}}
    """
    return {
        suite: {
            "suite": suite,
            "by_model": {
                model: {
                    "pass_at_k": 0.8,
                    "total_samples": 10,
                    "passed": 8,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                }
            },
            "by_case": {},
        }
    }


def _write_result(dir_path: Path, filename: str, payload: dict) -> Path:
    p = dir_path / filename
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. Empty / missing dir → empty history
# ---------------------------------------------------------------------------
def test_collect_cost_history_empty_dir(tmp_path):
    out = cost_history.collect_cost_history(tmp_path)
    assert out["runs"] == []
    assert out["total_usd"] == 0.0


def test_collect_cost_history_missing_dir_handled(tmp_path):
    """Non-existent path ไม่ crash — return empty."""
    out = cost_history.collect_cost_history(tmp_path / "nope")
    assert out["runs"] == []


# ---------------------------------------------------------------------------
# 2. Aggregates tokens per model → USD via COST_MATRIX
# ---------------------------------------------------------------------------
def test_collect_cost_history_aggregates_tokens_per_model(tmp_path):
    """Result file ที่มี tokens → history run ที่มี USD estimate per (suite, model)."""
    # deepseek-v4-flash = 1000 in + 500 out tokens
    _write_result(tmp_path, "results-20260701-120000.json",
                  _make_result_with_tokens("medical", "deepseek-v4-flash", 1000, 500))
    out = cost_history.collect_cost_history(tmp_path)
    assert len(out["runs"]) == 1
    run = out["runs"][0]
    assert "medical" in run["suites"]
    assert "deepseek-v4-flash" in run["suites"]["medical"]
    cost_info = run["suites"]["medical"]["deepseek-v4-flash"]
    assert "usd" in cost_info
    assert cost_info["usd"] > 0  # DeepSeek มี price > 0
    assert cost_info["tokens_in"] == 1000
    assert cost_info["tokens_out"] == 500


# ---------------------------------------------------------------------------
# 3. estimate_cost uses COST_MATRIX (known model → known price)
# ---------------------------------------------------------------------------
def test_estimate_cost_uses_cost_matrix():
    """deepseek-v4-flash: input=$0.15/1M, output=$0.60/1M.
    1M tokens in + 1M out → 0.15 + 0.60 = $0.75
    """
    cost = cost_history.estimate_model_cost("deepseek/deepseek-v4-flash", 1_000_000, 1_000_000)
    assert cost == pytest.approx(0.75, abs=0.01)


def test_estimate_cost_free_model_zero():
    """Free model (price 0) → USD = 0."""
    # glm-4.7-flash = free (input/output = 0.00)
    cost = cost_history.estimate_model_cost("zai/glm-4.7-flash", 1_000_000, 1_000_000)
    assert cost == 0.0


# ---------------------------------------------------------------------------
# 4. Unknown model → $0 (not crash)
# ---------------------------------------------------------------------------
def test_unknown_model_zero_cost():
    cost = cost_history.estimate_model_cost("unknown/mystery-model", 1000, 500)
    assert cost == 0.0  # unknown → $0, ไม่ crash


# ---------------------------------------------------------------------------
# 5. Chart series: one line per (suite, model)
# ---------------------------------------------------------------------------
def test_to_cost_chart_series_one_line_per_suite_model(tmp_path):
    _write_result(tmp_path, "results-20260701-120000.json", {
        "medical": {"suite": "medical", "by_model": {
            "deepseek-v4-flash": {"tokens_in": 1000, "tokens_out": 500, "pass_at_k": 0.8, "total_samples": 10, "passed": 8},
            "glm-5.2": {"tokens_in": 800, "tokens_out": 400, "pass_at_k": 0.7, "total_samples": 10, "passed": 7},
        }, "by_case": {}},
        "coding": {"suite": "coding", "by_model": {
            "deepseek-v4-flash": {"tokens_in": 2000, "tokens_out": 1000, "pass_at_k": 0.9, "total_samples": 10, "passed": 9},
        }, "by_case": {}},
    })
    history = cost_history.collect_cost_history(tmp_path)
    series = cost_history.to_cost_chart_series(history)
    labels = {d["label"] for d in series["datasets"]}
    assert "medical / deepseek-v4-flash" in labels
    assert "medical / glm-5.2" in labels
    assert "coding / deepseek-v4-flash" in labels


# ---------------------------------------------------------------------------
# 6. model_cost_summary ranks most expensive
# ---------------------------------------------------------------------------
def test_model_cost_summary_ranks_most_expensive(tmp_path):
    """2 runs; deepseek-v4-flash ใช้ tokens เยอะกว่า glm-5.2 → total USD สูงกว่า."""
    for date in ["20260701-120000", "20260708-120000"]:
        _write_result(tmp_path, f"results-{date}.json", {
            "medical": {"suite": "medical", "by_model": {
                "deepseek-v4-flash": {"tokens_in": 5000, "tokens_out": 2000, "pass_at_k": 0.8, "total_samples": 10, "passed": 8},
                "glm-5.2": {"tokens_in": 1000, "tokens_out": 500, "pass_at_k": 0.7, "total_samples": 10, "passed": 7},
            }, "by_case": {}},
        })
    history = cost_history.collect_cost_history(tmp_path)
    summary = cost_history.model_cost_summary(history)
    # แปลงเป็น dict เพื่อเช็ค
    by_model = {s["model"]: s["total_usd"] for s in summary}
    assert "deepseek-v4-flash" in by_model
    assert "glm-5.2" in by_model
    assert by_model["deepseek-v4-flash"] > by_model["glm-5.2"]


# ---------------------------------------------------------------------------
# 7. Missing tokens field → $0 (legacy results compatibility)
# ---------------------------------------------------------------------------
def test_missing_tokens_field_handled(tmp_path):
    """Legacy result files (ก่อน S6.0) ไม่มี tokens → USD = 0, ไม่ crash."""
    _write_result(tmp_path, "results-20260601-120000.json", {
        "medical": {"suite": "medical", "by_model": {
            "deepseek-v4-flash": {"pass_at_k": 0.8, "total_samples": 10, "passed": 8},  # ไม่มี tokens
        }, "by_case": {}},
    })
    out = cost_history.collect_cost_history(tmp_path)
    assert len(out["runs"]) == 1
    run = out["runs"][0]
    cost_info = run["suites"]["medical"]["deepseek-v4-flash"]
    assert cost_info["usd"] == 0.0  # missing tokens → $0
    assert cost_info["tokens_in"] == 0
