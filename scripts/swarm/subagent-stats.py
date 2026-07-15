#!/usr/bin/env python3
"""
subagent-stats.py — CLI for the Subagent Observatory.

Prints per-subagent statistics (count, pass_rate, latency p50/p95, best model)
aggregated from .tmp/live-events.jsonl. This is the terminal alternative to
the "🔬 Subagents" dashboard tab.

Usage:
  python scripts/swarm/subagent-stats.py               # all-time stats
  python scripts/swarm/subagent-stats.py --since 24h   # last 24h only
  python scripts/swarm/subagent-stats.py --since 3600  # last 3600s
  python scripts/swarm/subagent-stats.py --json        # raw JSON output

Data source: events emitted by scripts/hooks/log_subagent_result.py
(PostToolUse on the Agent tool).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import subagent_stats as st  # noqa: E402


def _parse_since(value: str) -> int:
    """Parse --since into seconds: '24h' → 86400, '30m' → 1800, '3600' → 3600."""
    v = value.strip().lower()
    if not v:
        return 0
    mult = 1
    if v.endswith("h"):
        mult = 3600
        v = v[:-1]
    elif v.endswith("m"):
        mult = 60
        v = v[:-1]
    elif v.endswith("s"):
        v = v[:-1]
    try:
        return int(float(v) * mult)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid --since value: {value!r}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--since", type=_parse_since, default=0,
                   help="time window (e.g. 24h, 30m, 3600); default = all time")
    p.add_argument("--json", action="store_true", help="emit raw JSON instead of a table")
    p.add_argument("--log", default=str(st.DEFAULT_LOG),
                   help=f"path to live-events.jsonl (default: {st.DEFAULT_LOG})")
    args = p.parse_args()

    stats = st.aggregate(log_file=args.log, window_seconds=args.since)
    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(st.render_summary(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
