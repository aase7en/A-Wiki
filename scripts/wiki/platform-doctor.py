#!/usr/bin/env python3
"""platform-doctor.py — CLI for the platform-ingest health-check.

Usage:
  python scripts/wiki/platform-doctor.py            # default: probe all 4 backends
  python scripts/wiki/platform-doctor.py --json     # JSON output for agents
  python scripts/wiki/platform-doctor.py --list     # list backends (no probing)
  python scripts/wiki/platform-doctor.py reddit     # probe just one channel

Exits 0 on success, 1 if any backend is 'error' (network failure etc).
'warn' status does NOT fail — it just means metadata-only or partial.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))


def _channel_names() -> list[str]:
    from platforms import BACKENDS
    return list(BACKENDS.keys())


def _probe(names: list[str] | None) -> dict:
    from platforms import BACKENDS
    from platforms.doctor import check_all
    channels = [BACKENDS[n] for n in names] if names else list(BACKENDS.values())
    return check_all(channels)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health-check platform ingestion backends.",
    )
    parser.add_argument(
        "channels",
        nargs="*",
        help="Optional channel names to probe (default: all). "
             "Choices: " + ", ".join(["reddit", "youtube", "bilibili", "jina"]),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON (compact, for agent consumption).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List known backends without probing.",
    )
    args = parser.parse_args()

    if args.list:
        names = _channel_names()
        if args.json:
            print(json.dumps({"backends": names}, ensure_ascii=False))
        else:
            print(f"{len(names)} backends registered:")
            for n in names:
                print(f"  {n}")
        return 0

    # Validate requested channel names
    known = set(_channel_names())
    unknown = [c for c in args.channels if c not in known]
    if unknown:
        print(f"unknown channel(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"known: {', '.join(sorted(known))}", file=sys.stderr)
        return 1

    report = _probe(args.channels or None)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        from platforms.doctor import render_text
        print(render_text(report))

    # Exit code: 1 if ANY error, 0 otherwise (warn is OK — partial coverage)
    has_error = any(e.get("status") == "error" for e in report.values())
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
