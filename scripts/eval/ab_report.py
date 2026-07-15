#!/usr/bin/env python3
"""
ab_report.py — Compare A/B experiment phases + recommend a winner (R4).

Consumes the pass_rate aggregates produced by subagent_stats.py (which
tags events with ab_phase) and compares phase A (champion) vs phase B
(challenger). Recommends which model to keep when the experiment
completes (total_phases reached).

Pure comparison logic — no I/O. The CLI wrapper (main()) reads the
observatory stats + experiment config + state, then calls compare_phases
/ recommend and prints a table.

Usage:
  python scripts/eval/ab_report.py --subagent clinical-reasoner
  python scripts/eval/ab_report.py --subagent clinical-reasoner --recommend
  python scripts/eval/ab_report.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

import ab_routing  # noqa: E402  -- sibling module


# ---------------------------------------------------------------------------
# Phase comparison (pure)
# ---------------------------------------------------------------------------
def compare_phases(
    stats_a: dict[str, Any],
    stats_b: dict[str, Any],
    min_samples: int = 10,
    noise_threshold: float = 0.05,
) -> dict[str, Any]:
    """Compare phase A (champion) vs phase B (challenger) pass rates.

    Args:
      stats_a: {count, pass, pass_rate} for phase A.
      stats_b: same for phase B.
      min_samples: minimum count per phase to make a confident call.
      noise_threshold: |delta| below this → 'flat' (no significant difference).

    Returns:
      {
        champion_rate, challenger_rate, delta, winner,
        verdict: 'champion_wins'|'challenger_wins'|'flat'|'insufficient_data',
        reason
      }
    """
    count_a = stats_a.get("count", 0)
    count_b = stats_b.get("count", 0)
    rate_a = stats_a.get("pass_rate", 0.0)
    rate_b = stats_b.get("pass_rate", 0.0)

    if count_a < min_samples or count_b < min_samples:
        return {
            "champion_rate": rate_a, "challenger_rate": rate_b,
            "delta": round(rate_a - rate_b, 3),
            "winner": None,
            "verdict": "insufficient_data",
            "reason": f"Insufficient data: A has {count_a}, B has {count_b} "
                      f"(need {min_samples} each). Wait for more invocations.",
        }

    delta = rate_a - rate_b
    if abs(delta) < noise_threshold:
        return {
            "champion_rate": rate_a, "challenger_rate": rate_b,
            "delta": round(delta, 3),
            "winner": None,
            "verdict": "flat",
            "reason": f"No significant difference (|Δ|={abs(delta):.3f} < "
                      f"noise threshold {noise_threshold}). Keep the champion "
                      f"(lower risk).",
        }

    if delta > 0:
        winner = "A"
        verdict = "champion_wins"
        reason = (f"Champion (A) wins by +{delta:.3f} pass_rate "
                  f"({rate_a:.2f} vs {rate_b:.2f}). Keep the champion model.")
    else:
        winner = "B"
        verdict = "challenger_wins"
        reason = (f"Challenger (B) wins by +{-delta:.3f} pass_rate "
                  f"({rate_b:.2f} vs {rate_a:.2f}). Promote the challenger.")

    return {
        "champion_rate": rate_a, "challenger_rate": rate_b,
        "delta": round(delta, 3),
        "winner": winner, "verdict": verdict, "reason": reason,
    }


# ---------------------------------------------------------------------------
# Recommendation (pure — combines completeness check + comparison)
# ---------------------------------------------------------------------------
def recommend(
    exp: dict[str, Any],
    state: dict[str, Any],
    stats_a: dict[str, Any],
    stats_b: dict[str, Any],
    min_samples: int = 10,
    noise_threshold: float = 0.05,
) -> dict[str, Any]:
    """Full recommendation for a completed experiment.

    Checks completeness first (invocations >= phase_size * total_phases),
    then compares phases. Returns a recommendation dict with:
      verdict, recommended_model (or None), reason, + comparison fields.
    """
    sa = exp["subagent"]
    sa_state = state.get(sa, {})
    invocations = sa_state.get("invocations", 0)

    if not ab_routing.is_complete(exp, invocations):
        ps = exp.get("phase_size", 20)
        tp = exp.get("total_phases", 4)
        target = ps * tp
        return {
            "verdict": "incomplete",
            "recommended_model": None,
            "reason": f"Experiment not yet complete: {invocations}/{target} "
                      f"invocations. Wait for it to finish before recommending.",
            "invocations": invocations, "target": target,
        }

    cmp = compare_phases(stats_a, stats_b, min_samples, noise_threshold)
    recommended = None
    if cmp["verdict"] == "champion_wins":
        recommended = exp["champion"]
    elif cmp["verdict"] == "challenger_wins":
        recommended = exp["challenger"]
    # flat → keep champion (lower risk), insufficient → None

    return {
        **cmp,
        "recommended_model": recommended,
        "invocations": invocations,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def render_report(subagent: str, exp: dict[str, Any], result: dict[str, Any]) -> str:
    """Render a compact comparison table for one experiment."""
    lines = []
    lines.append(f"🧪 A/B Experiment: {subagent}")
    lines.append(f"   champion:   {exp['champion']} (phase A)")
    lines.append(f"   challenger: {exp['challenger']} (phase B)")
    lines.append("")
    if "champion_rate" in result:
        lines.append(f"   {'phase':<8} {'count':>6} {'pass_rate':>10}")
        lines.append(f"   {'A (champ)':<8} {'-':>6} {result.get('champion_rate', 0):>10.3f}")
        lines.append(f"   {'B (chal)':<8} {'-':>6} {result.get('challenger_rate', 0):>10.3f}")
        lines.append(f"   delta: {result.get('delta', 0):+.3f}")
    lines.append("")
    lines.append(f"   verdict: {result.get('verdict', '?')}")
    if result.get("recommended_model"):
        lines.append(f"   ⭐ recommended: {result['recommended_model']}")
    lines.append(f"   {result.get('reason', '')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _fetch_phase_stats(subagent: str) -> tuple[dict, dict]:
    """Fetch phase A + B stats from the observatory for a subagent.

    Returns ({count, pass, pass_rate}, {count, pass, pass_rate}).
    Falls back to empty stats if the dashboard isn't reachable.
    """
    import urllib.request
    try:
        url = "http://localhost:7790/api/subagents/stats?since=0"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"count": 0, "pass": 0, "pass_rate": 0.0}, {"count": 0, "pass": 0, "pass_rate": 0.0}
    sa = data.get("by_subagent", {}).get(subagent, {})
    by_phase = sa.get("by_ab_phase", {})
    a = by_phase.get("A", {"count": 0, "pass": 0, "pass_rate": 0.0})
    b = by_phase.get("B", {"count": 0, "pass": 0, "pass_rate": 0.0})
    return a, b


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--subagent", help="subagent name to report on")
    p.add_argument("--recommend", action="store_true",
                   help="also output a recommendation (requires completed experiment)")
    p.add_argument("--list", action="store_true", help="list all experiments + status")
    p.add_argument("--min-samples", type=int, default=10)
    p.add_argument("--config", default=str(ab_routing.DEFAULT_CONFIG))
    args = p.parse_args()

    experiments = ab_routing.load_experiments(args.config)
    state = ab_routing.load_state()

    if args.list or not args.subagent:
        if not experiments:
            print("No A/B experiments configured.")
            print(f"  Config file: {args.config}")
            return 0
        print(f"A/B Experiments ({len(experiments)}):")
        for exp in experiments:
            sa = exp["subagent"]
            sa_state = state.get(sa, {})
            inv = sa_state.get("invocations", 0)
            phase = sa_state.get("current_phase", "(none)")
            ps = exp.get("phase_size", 20)
            tp = exp.get("total_phases", 4)
            target = ps * tp
            active = "🟢" if exp.get("active") else "⚪"
            print(f"  {active} {sa:<28} {exp['champion']}↔{exp['challenger']}  "
                  f"{inv}/{target} invocations  phase={phase}")
        return 0

    # Report on a specific subagent.
    exp = next((e for e in experiments if e["subagent"] == args.subagent), None)
    if exp is None:
        print(f"❌ No experiment found for subagent '{args.subagent}'", file=sys.stderr)
        print(f"   Configured: {[e['subagent'] for e in experiments]}", file=sys.stderr)
        return 1

    stats_a, stats_b = _fetch_phase_stats(args.subagent)
    if args.recommend:
        result = recommend(exp, state, stats_a, stats_b, args.min_samples)
    else:
        result = compare_phases(stats_a, stats_b, args.min_samples)
    print(render_report(args.subagent, exp, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
