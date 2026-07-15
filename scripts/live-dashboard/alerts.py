"""Observatory alerting — flag subagents whose pass_rate has dropped.

Consumes the stats dict produced by scripts/live-dashboard/subagent_stats.py
and returns a list of alerts (warning / critical) for the dashboard banner.
Pure function of the stats dict + optional thresholds — no I/O, no clock —
so it is trivially testable without a running server.

Default thresholds (tuned to avoid noise):
  - min_count: 5     → ignore subagents with fewer than 5 invocations
                       (too few samples to draw a conclusion)
  - warning:   0.85  → flag when pass_rate drops below 85%
  - critical:  0.70  → escalate to critical when pass_rate drops below 70%

Used by:
  - server.py /api/subagents/alerts (24h-window banner)
  - tests/test_alerts.py
"""
from __future__ import annotations

from typing import Any

DEFAULT_THRESHOLDS = {
    "min_count": 5,    # ignore subagents with fewer samples (statistical noise)
    "warning": 0.85,   # pass_rate < 0.85 → warning
    "critical": 0.70,  # pass_rate < 0.70 → critical
}

# Severity ranking for sorting (critical first).
_SEVERITY_ORDER = {"critical": 0, "warning": 1}


def evaluate_alerts(
    stats: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return a list of alert dicts for subagents failing the pass_rate gate.

    Args:
      stats: the dict returned by subagent_stats.aggregate(). Must contain
             by_subagent: {name: {count, pass, fail, pass_rate, ...}}.
      thresholds: optional override of DEFAULT_THRESHOLDS keys
                  (min_count, warning, critical). Partial overrides merge
                  over the defaults.

    Returns:
      List of alert dicts, sorted critical-first then by count desc:
        [{
          "severity": "critical"|"warning",
          "subagent": "<name>",
          "pass_rate": float,
          "count": int,
          "fail": int,
          "msg": "<human-readable summary>",
          "action": "<CLI suggestion>",
        }, ...]
    """
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    min_count = int(th["min_count"])
    warn_thr = float(th["warning"])
    crit_thr = float(th["critical"])

    out: list[dict[str, Any]] = []
    by_subagent = stats.get("by_subagent", {}) or {}
    for name, sa in by_subagent.items():
        count = int(sa.get("count", 0))
        if count < min_count:
            continue  # too few samples — would be noise
        pass_rate = float(sa.get("pass_rate", 0.0))
        if pass_rate >= warn_thr:
            continue  # healthy

        if pass_rate < crit_thr:
            severity = "critical"
            action = ("consider `python scripts/eval/apply_adaptive_routing.py` "
                      "or reroute to a different model")
        else:
            severity = "warning"
            action = ("consider `python scripts/eval/run_subagent_eval.py "
                      "--domain <suite>` to validate model choice")

        fail = int(sa.get("fail", count - int(sa.get("pass", 0))))
        out.append({
            "severity": severity,
            "subagent": name,
            "pass_rate": pass_rate,
            "count": count,
            "fail": fail,
            "msg": (f"{name}: pass_rate={pass_rate*100:.0f}% "
                    f"({fail}/{count} failed in window)"),
            "action": action,
        })

    # Sort: critical first, then warning; within a tier, more failures first.
    out.sort(key=lambda a: (_SEVERITY_ORDER.get(a["severity"], 9), -a["fail"]))
    return out


def summarize(stats: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, int]:
    """Return {total, critical, warning} counts for the dashboard badge.

    Used by the banner to show "🚨 2 critical · ⚠️ 1 warning" without the
    caller having to re-run evaluate_alerts and count.
    """
    alerts = evaluate_alerts(stats, thresholds=thresholds)
    critical = sum(1 for a in alerts if a["severity"] == "critical")
    warning = sum(1 for a in alerts if a["severity"] == "warning")
    return {"total": len(alerts), "critical": critical, "warning": warning}


__all__ = ["evaluate_alerts", "summarize", "DEFAULT_THRESHOLDS"]
