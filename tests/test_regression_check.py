"""Tests for scripts/eval/regression_check.py — pass@k regression detection.

P3 closes the "detect regression" link in the feedback loop. The CI workflow
runs eval weekly, compares new pass@k against the previous results file,
and flags any (suite, model) pair whose pass@k dropped by more than the
threshold. Pure functions — no I/O, no clock — so trivially deterministic.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import regression_check as rc  # noqa: E402


def _results(by_model_pass_at_k):
    """Build a minimal results dict shaped like run_subagent_eval output:
    {suite: {by_model: {model: {pass_at_k, total_samples, passed}}}}"""
    out = {}
    for suite, models in by_model_pass_at_k.items():
        out[suite] = {"by_model": {
            m: {"pass_at_k": rate, "total_samples": 10, "passed": int(rate * 10)}
            for m, rate in models.items()
        }, "by_case": {}}
    return out


# ---------------------------------------------------------------------------
# detect_regression — compares baseline vs new pass@k
# ---------------------------------------------------------------------------

def test_no_regressions_when_flat():
    """Identical pass@k → all flat, zero regressions."""
    baseline = _results({"medical": {"deepseek-v4-flash": 0.8, "glm-5.2": 0.7}})
    new = _results({"medical": {"deepseek-v4-flash": 0.8, "glm-5.2": 0.7}})
    out = rc.detect_regression(baseline, new, threshold=0.10)
    assert all(r["severity"] == "flat" for r in out)
    assert not any(r["severity"] == "regression" for r in out)


def test_flags_drop_over_threshold():
    """pass@k drop > threshold → regression flagged."""
    baseline = _results({"medical": {"deepseek-v4-flash": 0.9}})
    new = _results({"medical": {"deepseek-v4-flash": 0.7}})  # drop 0.20 > 0.10
    out = rc.detect_regression(baseline, new, threshold=0.10)
    regressions = [r for r in out if r["severity"] == "regression"]
    assert len(regressions) == 1
    r = regressions[0]
    assert r["suite"] == "medical"
    assert r["model"] == "deepseek-v4-flash"
    assert r["baseline_pass_at_k"] == 0.9
    assert r["new_pass_at_k"] == 0.7
    assert r["delta"] == -0.2


def test_drop_at_threshold_not_flagged():
    """Drop EXACTLY equal to threshold → NOT flagged (exclusive boundary).
    threshold=0.10, drop=0.10 → severity=flat (not regression)."""
    baseline = _results({"x": {"m": 0.9}})
    new = _results({"x": {"m": 0.8}})  # drop exactly 0.10
    out = rc.detect_regression(baseline, new, threshold=0.10)
    assert all(r["severity"] == "flat" for r in out)


def test_improvement_flagged_separately():
    """pass@k INCREASE → improvement (not regression, not flat)."""
    baseline = _results({"x": {"m": 0.5}})
    new = _results({"x": {"m": 0.8}})  # +0.30
    out = rc.detect_regression(baseline, new, threshold=0.10)
    improvements = [r for r in out if r["severity"] == "improvement"]
    assert len(improvements) == 1
    assert improvements[0]["delta"] == 0.3


def test_missing_baseline_all_flat():
    """Suite/model present in new but absent from baseline → flat (no baseline
    to compare against; we cannot call it a regression)."""
    baseline = {}  # no baseline
    new = _results({"medical": {"m": 0.5}})
    out = rc.detect_regression(baseline, new, threshold=0.10)
    # No baseline → treated as flat (first run has nothing to regress from).
    assert all(r["severity"] == "flat" for r in out)
    assert len(out) == 1  # the new entry is reported as flat with baseline=0


def test_missing_in_new_treated_as_removed():
    """Suite/model in baseline but absent from new → reported as 'removed'
    (dropped from results entirely; worth investigating)."""
    baseline = _results({"x": {"m": 0.9}})
    new = {}  # empty new results
    out = rc.detect_regression(baseline, new, threshold=0.10)
    removed = [r for r in out if r["severity"] == "removed"]
    assert len(removed) == 1
    assert removed[0]["suite"] == "x"
    assert removed[0]["model"] == "m"


def test_multiple_suites_models():
    """Multiple suites × models → one entry per (suite, model) pair."""
    baseline = _results({
        "medical": {"a": 0.9, "b": 0.5},
        "finance": {"a": 0.8},
    })
    new = _results({
        "medical": {"a": 0.7, "b": 0.7},  # a: regression, b: improvement
        "finance": {"a": 0.8},            # flat
    })
    out = rc.detect_regression(baseline, new, threshold=0.10)
    assert len(out) == 3
    by_pair = {(r["suite"], r["model"]): r for r in out}
    assert by_pair[("medical", "a")]["severity"] == "regression"
    assert by_pair[("medical", "b")]["severity"] == "improvement"
    assert by_pair[("finance", "a")]["severity"] == "flat"


# ---------------------------------------------------------------------------
# render_regression_report — markdown for GitHub issue body
# ---------------------------------------------------------------------------

def test_render_report_lists_regressions():
    """Report must list every regression with suite/model/delta."""
    baseline = _results({"medical": {"m": 0.9}})
    new = _results({"medical": {"m": 0.6}})
    out = rc.detect_regression(baseline, new, threshold=0.10)
    report = rc.render_regression_report(out)
    assert "medical" in report
    assert "m" in report
    assert "regression" in report.lower()


def test_render_report_empty_when_no_regressions():
    """No regressions → short 'all green' message."""
    baseline = _results({"x": {"m": 0.9}})
    new = _results({"x": {"m": 0.9}})
    out = rc.detect_regression(baseline, new, threshold=0.10)
    report = rc.render_regression_report(out)
    assert "no regression" in report.lower() or "all green" in report.lower() \
        or "stable" in report.lower()


def test_render_report_includes_summary_counts():
    """Report header should summarize counts (regression/improvement/flat)."""
    baseline = _results({"x": {"a": 0.9, "b": 0.5}})
    new = _results({"x": {"a": 0.7, "b": 0.7}})
    out = rc.detect_regression(baseline, new, threshold=0.10)
    report = rc.render_regression_report(out)
    # Should mention the counts somewhere in the header
    assert "1" in report  # 1 regression
