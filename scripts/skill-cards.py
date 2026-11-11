#!/usr/bin/env python3
"""Compact, read-only skill suggestions from the existing A-Wiki registry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skills_registry import Registry
from skills_registry.skill_cards import build_cards


def main() -> int:
    parser = argparse.ArgumentParser(description="A-Wiki compact skill cards")
    parser.add_argument("--query", help="Task description; omit to view core cards")
    parser.add_argument("--limit", type=int, default=None, help="Max 3 query / 10 core")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()
    registry = Registry.load(Path(__file__).resolve().parents[1] / "skills-registry.json")
    out = build_cards(registry, query=args.query,
                      limit=args.limit if args.limit is not None else
                            (3 if args.query is not None else 8))
    if not args.json:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    if args.json:
        # ASCII JSON survives Windows cp874/cp1252 consoles without data loss.
        print(json.dumps(out, ensure_ascii=True, indent=2))
        return 0
    print(f"Skill decision: {out['decision']} (no full skill bodies read)")
    for item in out["cards"]:
        print(f"- {item['name']}: {item['purpose']}")
        if item["use_when"]:
            print("  Use when: " + ", ".join(item["use_when"]))
        print("  Not when: " + item["do_not_use_when"])
        print(f"  Load later: {item['body_pointer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
