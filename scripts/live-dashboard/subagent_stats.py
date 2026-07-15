"""Subagent Observatory — aggregation over .tmp/live-events.jsonl.

Reads `subagent_invoke` events emitted by the PostToolUse hook
(scripts/hooks/log_subagent_result.py) and produces per-subagent +
per-bucket statistics: count, pass/fail, pass_rate, latency p50/p95,
token totals, and a model leaderboard (best model by pass_rate).

Used by:
  - the "🔬 Subagents" dashboard tab (via server.py /api/subagents/stats)
  - the CLI: python scripts/swarm/subagent-stats.py [--since 24h]

The aggregation is a pure function of a log file path + window, so it is
trivially testable without a running server.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LOG = REPO_ROOT / ".tmp" / "live-events.jsonl"


def _percentile(sorted_vals: list[int], p: float) -> int:
    """Linear-interp percentile of a SORTED list. Returns 0 if empty."""
    if not sorted_vals:
        return 0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return int(round(sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)))


def _empty_subagent_stat() -> dict[str, Any]:
    return {
        "count": 0, "pass": 0, "fail": 0, "pass_rate": 0.0,
        "latency_p50_ms": 0, "latency_p95_ms": 0,
        "tokens_in": 0, "tokens_out": 0,
        "models": {}, "best_model": None,
    }


def aggregate(
    log_file: Path | str = DEFAULT_LOG,
    window_seconds: int = 0,
    now: float | None = None,
) -> dict[str, Any]:
    """Aggregate subagent_invoke events into per-subagent + per-bucket stats.

    Args:
      log_file: path to the live-events.jsonl log.
      window_seconds: if > 0, only count events newer than (now - window).
                      0 = all events (no time filter).
      now: override "current time" for deterministic tests.

    Returns:
      {
        total_invocations, window_seconds, generated_at,
        by_subagent: {name: {count, pass, fail, pass_rate,
                             latency_p50_ms, latency_p95_ms,
                             tokens_in, tokens_out, models, best_model}},
        by_bucket:   {bucket: {count, pass, fail, pass_rate}},
      }
    """
    log_path = Path(log_file)
    now_ts = now if now is not None else time.time()
    cutoff = now_ts - window_seconds if window_seconds > 0 else 0.0

    by_subagent: dict[str, dict[str, Any]] = {}
    by_bucket: dict[str, dict[str, Any]] = {}
    total = 0

    if not log_path.exists():
        return _empty_result(window_seconds, now_ts)

    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("type") != "subagent_invoke":
                    continue
                ts = ev.get("ts", 0)
                if cutoff and ts < cutoff:
                    continue
                total += 1

                name = ev.get("subagent_type", "?")
                result = ev.get("result", "pass")
                is_pass = result == "pass"
                model = ev.get("model") or "unknown"
                bucket = ev.get("bucket") or "unknown"
                latency = int(ev.get("latency_ms") or 0)
                tokens_in = int(ev.get("tokens_in") or 0)
                tokens_out = int(ev.get("tokens_out") or 0)

                sa = by_subagent.setdefault(name, _empty_subagent_stat())
                sa["count"] += 1
                if is_pass:
                    sa["pass"] += 1
                else:
                    sa["fail"] += 1
                sa["tokens_in"] += tokens_in
                sa["tokens_out"] += tokens_out
                # stash latencies + model counts for a second pass
                sa.setdefault("_latencies", []).append(latency)
                sa["models"][model] = sa["models"].get(model, 0) + 1
                # per-model pass tracking
                sa.setdefault("_model_pass", {})
                sa["_model_pass"][model] = sa["_model_pass"].get(model, 0) + (1 if is_pass else 0)
                sa.setdefault("_model_total", {})
                sa["_model_total"][model] = sa["_model_total"].get(model, 0) + 1
                # R4: per-ab-phase pass tracking (only if event is tagged)
                ab_phase = ev.get("ab_phase")
                if ab_phase:
                    sa.setdefault("_ab_phase_pass", {})
                    sa.setdefault("_ab_phase_total", {})
                    sa["_ab_phase_pass"][ab_phase] = sa["_ab_phase_pass"].get(ab_phase, 0) + (1 if is_pass else 0)
                    sa["_ab_phase_total"][ab_phase] = sa["_ab_phase_total"].get(ab_phase, 0) + 1

                bk = by_bucket.setdefault(bucket, {"count": 0, "pass": 0, "fail": 0, "pass_rate": 0.0})
                bk["count"] += 1
                if is_pass:
                    bk["pass"] += 1
                else:
                    bk["fail"] += 1
    except Exception:
        pass

    # Second pass: finalize percentiles, pass_rate, best_model; strip scratch keys.
    for sa in by_subagent.values():
        lats = sorted(sa.pop("_latencies", []))
        sa["latency_p50_ms"] = _percentile(lats, 0.50)
        sa["latency_p95_ms"] = _percentile(lats, 0.95)
        sa["pass_rate"] = round(sa["pass"] / sa["count"], 3) if sa["count"] else 0.0
        # best model = highest pass_rate (ties → most invocations)
        model_pass = sa.pop("_model_pass", {})
        model_total = sa.pop("_model_total", {})
        best = None
        best_rate = -1.0
        for m, total_m in model_total.items():
            rate = model_pass.get(m, 0) / total_m if total_m else 0.0
            if rate > best_rate or (rate == best_rate and total_m > model_total.get(best or "", 0)):
                best_rate = rate
                best = m
        sa["best_model"] = best
        sa["models"] = dict(sorted(sa["models"].items(), key=lambda kv: -kv[1]))
        # R4: finalize by_ab_phase (only present if events were tagged)
        ab_pass = sa.pop("_ab_phase_pass", {})
        ab_total = sa.pop("_ab_phase_total", {})
        if ab_total:
            sa["by_ab_phase"] = {}
            for phase, tot in ab_total.items():
                pa = ab_pass.get(phase, 0)
                sa["by_ab_phase"][phase] = {
                    "count": tot,
                    "pass": pa,
                    "pass_rate": round(pa / tot, 3) if tot else 0.0,
                }

    for bk in by_bucket.values():
        bk["pass_rate"] = round(bk["pass"] / bk["count"], 3) if bk["count"] else 0.0

    return {
        "total_invocations": total,
        "window_seconds": window_seconds,
        "generated_at": round(now_ts, 3),
        "by_subagent": by_subagent,
        "by_bucket": dict(sorted(by_bucket.items(), key=lambda kv: -kv[1]["count"])),
    }


def _empty_result(window_seconds: int, now_ts: float) -> dict[str, Any]:
    return {
        "total_invocations": 0,
        "window_seconds": window_seconds,
        "generated_at": round(now_ts, 3),
        "by_subagent": {},
        "by_bucket": {},
    }


def render_summary(stats: dict[str, Any]) -> str:
    """Render a compact, human-readable summary table (for CLI output)."""
    lines = []
    total = stats["total_invocations"]
    lines.append(f"🔬 Subagent Observatory — {total} invocation(s)")
    if stats.get("window_seconds"):
        lines.append(f"   window: last {stats['window_seconds']}s")
    lines.append("")
    if not stats["by_subagent"]:
        lines.append("   (no subagent_invoke events yet — invoke a subagent to populate)")
        return "\n".join(lines)
    header = f"{'subagent':<30} {'count':>5} {'pass%':>6} {'p50ms':>7} {'p95ms':>7} {'best_model'}"
    lines.append(header)
    lines.append("-" * len(header))
    for name, sa in sorted(stats["by_subagent"].items(), key=lambda kv: -kv[1]["count"]):
        lines.append(
            f"{name:<30} {sa['count']:>5} {sa['pass_rate']*100:>5.0f}% "
            f"{sa['latency_p50_ms']:>7} {sa['latency_p95_ms']:>7} {sa.get('best_model') or '-'}"
        )
    if stats["by_bucket"]:
        lines.append("")
        lines.append("By rate-limit bucket:")
        for b, bk in stats["by_bucket"].items():
            lines.append(f"  {b:<20} {bk['count']:>4}  pass={bk['pass_rate']*100:.0f}%")
    return "\n".join(lines)


__all__ = ["aggregate", "render_summary", "DEFAULT_LOG"]
