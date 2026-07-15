"""Tests for the Observatory alerting module (alerts.py).

Alerts fire when a subagent's pass_rate drops below a threshold while having
enough samples (>= min_count) to be statistically meaningful. Pure logic —
no I/O, no clock, no network — so trivially deterministic.

Default thresholds (mirrors DEFAULT_THRESHOLDS in alerts.py):
  - warning:  pass_rate < 0.85 AND count >= 5
  - critical: pass_rate < 0.70 AND count >= 5
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import alerts  # noqa: E402


def _stat(count, pass_n, fail_n, pass_rate=None):
    """Build a minimal by_subagent entry that alerts.evaluate_alerts consumes."""
    if pass_rate is None:
        pass_rate = round(pass_n / count, 3) if count else 0.0
    return {"count": count, "pass": pass_n, "fail": fail_n, "pass_rate": pass_rate,
            "latency_p50_ms": 0, "latency_p95_ms": 0,
            "tokens_in": 0, "tokens_out": 0, "models": {}, "best_model": None}


def _stats(by_subagent):
    return {"total_invocations": sum(s["count"] for s in by_subagent.values()),
            "window_seconds": 86400, "generated_at": 0.0,
            "by_subagent": dict(by_subagent), "by_bucket": {}}


# ---------------------------------------------------------------------------
# Empty / healthy stats → no alerts
# ---------------------------------------------------------------------------

def test_no_alerts_when_empty():
    """No subagents → no alerts (nothing to alert on)."""
    stats = {"total_invocations": 0, "by_subagent": {}, "by_bucket": {}}
    assert alerts.evaluate_alerts(stats) == []


def test_no_alerts_when_all_healthy():
    """Healthy pass_rate (>= 0.85) with enough samples → no alerts."""
    stats = _stats({"medical-lit-reviewer": _stat(10, 10, 0, pass_rate=1.0)})
    assert alerts.evaluate_alerts(stats) == []


# ---------------------------------------------------------------------------
# Threshold tiers
# ---------------------------------------------------------------------------

def test_critical_when_pass_rate_low():
    """pass_rate < 0.70 with count >= 5 → critical alert."""
    stats = _stats({"finance-analyst": _stat(10, 4, 6, pass_rate=0.40)})
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 1
    assert out[0]["severity"] == "critical"
    assert out[0]["subagent"] == "finance-analyst"
    assert out[0]["pass_rate"] == 0.40
    assert out[0]["count"] == 10


def test_warning_tier_between_thresholds():
    """0.70 <= pass_rate < 0.85 with count >= 5 → warning (not critical)."""
    stats = _stats({"code-architect": _stat(10, 8, 2, pass_rate=0.80)})
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 1
    assert out[0]["severity"] == "warning"
    assert out[0]["subagent"] == "code-architect"


def test_warning_boundary_is_exclusive():
    """pass_rate == 0.85 exactly → NOT a warning (threshold is < 0.85)."""
    stats = _stats({"x": _stat(10, 9, 1, pass_rate=0.85)})
    assert alerts.evaluate_alerts(stats) == []


def test_critical_boundary_is_exclusive():
    """pass_rate == 0.70 exactly → warning (critical threshold is < 0.70)."""
    stats = _stats({"x": _stat(10, 7, 3, pass_rate=0.70)})
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 1
    assert out[0]["severity"] == "warning"


# ---------------------------------------------------------------------------
# Min-sample guard (suppress noise from tiny samples)
# ---------------------------------------------------------------------------

def test_ignores_few_samples():
    """count < 5 (min_count) → no alert even with 0% pass_rate (avoid noise)."""
    # 4 calls, all fail
    stats = _stats({"x": _stat(4, 0, 4, pass_rate=0.0)})
    assert alerts.evaluate_alerts(stats) == []


def test_min_count_boundary_inclusive():
    """count == 5 (exactly min_count) → alert CAN fire (>= is inclusive)."""
    stats = _stats({"x": _stat(5, 0, 5, pass_rate=0.0)})
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 1
    assert out[0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# Multiple subagents → multiple alerts, sorted by severity then count
# ---------------------------------------------------------------------------

def test_multiple_alerts_sorted():
    """Two failing subagents → two alerts; critical before warning."""
    stats = _stats({
        "alpha": _stat(10, 8, 2, pass_rate=0.80),   # warning
        "beta":  _stat(10, 2, 8, pass_rate=0.20),   # critical
    })
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 2
    # critical first
    assert out[0]["severity"] == "critical"
    assert out[0]["subagent"] == "beta"
    assert out[1]["severity"] == "warning"
    assert out[1]["subagent"] == "alpha"


# ---------------------------------------------------------------------------
# Custom thresholds override defaults
# ---------------------------------------------------------------------------

def test_custom_thresholds():
    """Caller can tighten/loosen thresholds via the thresholds arg."""
    stats = _stats({"x": _stat(10, 9, 1, pass_rate=0.90)})
    # Default: 0.90 is healthy. But raise warning to 0.95 → now it's a warning.
    out = alerts.evaluate_alerts(stats, thresholds={"warning": 0.95, "critical": 0.80})
    assert len(out) == 1
    assert out[0]["severity"] == "warning"


def test_custom_min_count():
    """Caller can raise min_count to suppress alert until more samples."""
    stats = _stats({"x": _stat(10, 0, 10, pass_rate=0.0)})
    # With min_count=20 → 10 samples is not enough → no alert.
    out = alerts.evaluate_alerts(stats, thresholds={"min_count": 20})
    assert out == []


# ---------------------------------------------------------------------------
# Alert message + action hint (for dashboard banner display)
# ---------------------------------------------------------------------------

def test_message_includes_action():
    """Each alert's msg+action suggests the next step (eval or reroute)."""
    stats = _stats({"x": _stat(10, 2, 8, pass_rate=0.20)})
    out = alerts.evaluate_alerts(stats)
    assert len(out) == 1
    a = out[0]
    assert "x" in a["msg"]
    # action should point at the eval or adaptive-routing CLI
    assert "eval" in a["action"].lower() or "reroute" in a["action"].lower() \
        or "adaptive" in a["action"].lower()


def test_alert_has_required_keys():
    """Every alert dict must carry the keys the dashboard UI expects."""
    stats = _stats({"x": _stat(10, 0, 10, pass_rate=0.0)})
    out = alerts.evaluate_alerts(stats)
    a = out[0]
    for k in ("severity", "subagent", "pass_rate", "count", "fail", "msg", "action"):
        assert k in a, f"missing key {k!r}"


# ---------------------------------------------------------------------------
# Summary helper (used by the dashboard banner count badge)
# ---------------------------------------------------------------------------

def test_summary_counts_by_severity():
    """summarize() returns {total, critical, warning} counts for the badge."""
    stats = _stats({
        "a": _stat(10, 8, 2, pass_rate=0.80),   # warning
        "b": _stat(10, 2, 8, pass_rate=0.20),   # critical
        "c": _stat(10, 1, 9, pass_rate=0.10),   # critical
        "d": _stat(10, 9, 1, pass_rate=0.90),   # healthy
    })
    summary = alerts.summarize(stats)
    assert summary["total"] == 3
    assert summary["critical"] == 2
    assert summary["warning"] == 1


def test_summary_empty_when_healthy():
    summary = alerts.summarize({"by_subagent": {}})
    assert summary == {"total": 0, "critical": 0, "warning": 0}
