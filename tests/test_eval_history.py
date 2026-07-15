"""Tests for scripts/live-dashboard/eval_history.py — eval history aggregation (R3).

Iron Law #1: failing tests written FIRST. These pin the contract of
collect_history() / to_chart_series() / detect_regression_points() before
the implementation exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import eval_history  # noqa: E402  -- module under test (created by R3)


def _make_result(suite: str, model: str, pass_at_k: float, generated_at: float = 0.0) -> dict:
    """Build a minimal result file payload matching run_subagent_eval schema.

    The actual schema (run_subagent_eval.py line 324) is:
      { <suite_name>: { "suite": <name>, "by_model": {...}, "by_case": {} } }
    Each suite is a TOP-LEVEL key — there is no wrapping "suites" object.
    """
    return {
        suite: {
            "suite": suite,
            "by_model": {
                model: {"pass_at_k": pass_at_k, "total_samples": 10, "passed": int(pass_at_k * 10)},
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
def test_collect_history_empty_dir_returns_empty(tmp_path):
    out = eval_history.collect_history(tmp_path)
    assert out["runs"] == []
    assert out["series"] == []
    assert out["regressions"] == []


def test_collect_history_missing_dir_handled_gracefully(tmp_path):
    """A non-existent path should not raise — return empty."""
    out = eval_history.collect_history(tmp_path / "does-not-exist")
    assert out["runs"] == []


# ---------------------------------------------------------------------------
# 2. Parses timestamped filenames + sorts by date
# ---------------------------------------------------------------------------
def test_collect_history_parses_timestamped_filenames(tmp_path):
    _write_result(tmp_path, "results-20260701-120000.json",
                  _make_result("medical", "deepseek-v4-flash", 0.8, 1751500800.0))
    _write_result(tmp_path, "results-20260708-120000.json",
                  _make_result("medical", "deepseek-v4-flash", 0.9, 1752105600.0))
    out = eval_history.collect_history(tmp_path)
    assert len(out["runs"]) == 2
    # Sorted ascending by date
    assert out["runs"][0]["date_tag"] == "20260701-120000"
    assert out["runs"][1]["date_tag"] == "20260708-120000"


def test_collect_history_sorts_by_date(tmp_path):
    """Files written out of order should still be sorted chronologically."""
    _write_result(tmp_path, "results-20260715-090000.json", _make_result("a", "m", 0.5))
    _write_result(tmp_path, "results-20260701-090000.json", _make_result("a", "m", 0.6))
    _write_result(tmp_path, "results-20260708-090000.json", _make_result("a", "m", 0.7))
    out = eval_history.collect_history(tmp_path)
    dates = [r["date_tag"] for r in out["runs"]]
    assert dates == ["20260701-090000", "20260708-090000", "20260715-090000"]


# ---------------------------------------------------------------------------
# 3. Chart series: one line per (suite, model)
# ---------------------------------------------------------------------------
def test_to_chart_series_one_line_per_suite_model(tmp_path):
    _write_result(tmp_path, "results-20260701-120000.json", {
        "medical": {"suite": "medical", "by_model": {
            "deepseek-v4-flash": {"pass_at_k": 0.7, "total_samples": 10, "passed": 7},
            "glm-5.2": {"pass_at_k": 0.6, "total_samples": 10, "passed": 6},
        }, "by_case": {}},
        "coding": {"suite": "coding", "by_model": {
            "deepseek-v4-flash": {"pass_at_k": 0.8, "total_samples": 10, "passed": 8},
        }, "by_case": {}},
    })
    history = eval_history.collect_history(tmp_path)
    series = eval_history.to_chart_series(history)
    labels = series["labels"]
    assert len(labels) == 1  # one run date
    # 3 lines: medical/deepseek, medical/glm, coding/deepseek
    labels_set = {d["label"] for d in series["datasets"]}
    assert "medical / deepseek-v4-flash" in labels_set
    assert "medical / glm-5.2" in labels_set
    assert "coding / deepseek-v4-flash" in labels_set
    assert len(series["datasets"]) == 3


# ---------------------------------------------------------------------------
# 4. Regression detection: drops over threshold are flagged
# ---------------------------------------------------------------------------
def test_detect_regression_marks_drop_over_threshold(tmp_path):
    """A pass@k drop > threshold (0.10) between consecutive runs is flagged."""
    _write_result(tmp_path, "results-20260701-120000.json",
                  _make_result("medical", "m", 0.90))
    _write_result(tmp_path, "results-20260708-120000.json",
                  _make_result("medical", "m", 0.70))  # drop of 0.20
    history = eval_history.collect_history(tmp_path)
    regs = eval_history.detect_regression_points(history, threshold=0.10)
    assert len(regs) == 1
    r = regs[0]
    assert r["suite"] == "medical"
    assert r["model"] == "m"
    assert r["delta"] == pytest.approx(-0.20, abs=0.01)
    assert r["date_tag"] == "20260708-120000"


def test_detect_regression_ignores_improvement(tmp_path):
    """An improvement (positive delta) is NOT a regression."""
    _write_result(tmp_path, "results-20260701-120000.json",
                  _make_result("medical", "m", 0.50))
    _write_result(tmp_path, "results-20260708-120000.json",
                  _make_result("medical", "m", 0.90))  # gain of 0.40
    history = eval_history.collect_history(tmp_path)
    regs = eval_history.detect_regression_points(history, threshold=0.10)
    assert len(regs) == 0


# ---------------------------------------------------------------------------
# 5. Multiple suites kept separate
# ---------------------------------------------------------------------------
def test_multiple_suits_separate_datasets(tmp_path):
    _write_result(tmp_path, "results-20260701-120000.json", {
        "medical": {"suite": "medical", "by_model": {"m1": {"pass_at_k": 0.7, "total_samples": 10, "passed": 7}}, "by_case": {}},
        "finance": {"suite": "finance", "by_model": {"m1": {"pass_at_k": 0.8, "total_samples": 10, "passed": 8}}, "by_case": {}},
    })
    history = eval_history.collect_history(tmp_path)
    series = eval_history.to_chart_series(history)
    labels = {d["label"] for d in series["datasets"]}
    assert "medical / m1" in labels
    assert "finance / m1" in labels


# ---------------------------------------------------------------------------
# 6. Malformed files skipped gracefully
# ---------------------------------------------------------------------------
def test_malformed_json_skipped(tmp_path):
    """A corrupt results file should be skipped, not crash the collector."""
    _write_result(tmp_path, "results-20260701-120000.json", _make_result("medical", "m", 0.7))
    (tmp_path / "results-20260702-broken.json").write_text("{not valid json", encoding="utf-8")
    out = eval_history.collect_history(tmp_path)
    assert len(out["runs"]) == 1  # only the valid one


# ---------------------------------------------------------------------------
# 7. Flat (no change) → no regression
# ---------------------------------------------------------------------------
def test_flat_history_no_regression(tmp_path):
    _write_result(tmp_path, "results-20260701-120000.json", _make_result("medical", "m", 0.80))
    _write_result(tmp_path, "results-20260708-120000.json", _make_result("medical", "m", 0.80))
    history = eval_history.collect_history(tmp_path)
    regs = eval_history.detect_regression_points(history, threshold=0.10)
    assert len(regs) == 0
