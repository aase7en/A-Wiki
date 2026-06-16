#!/usr/bin/env python3
"""
choose-model.py — Terminal model chooser (CLI fallback for the HTML chooser).

Reads the scouted catalog (.tmp/model-catalog.json, from
`model-scout-current.py --catalog`) and lets you list models grouped by
provider, then pin a primary + secondary into the roster.

Usage:
  choose-model.py --list                         # show catalog grouped by ค่าย
  choose-model.py --primary z-ai/glm-4.6 \
                  --secondary google/gemini-2.5-flash:free \
                  [--race "a b c"] [--out .tmp/model-selection.json] [--apply]

`--apply` runs apply-model-selection.py to pin the choice into model-roster.conf.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / ".tmp" / "model-catalog.json"
DEFAULT_SELECTION = REPO_ROOT / ".tmp" / "model-selection.json"
APPLY_SCRIPT = REPO_ROOT / "scripts" / "apply-model-selection.py"


def _fmt_price(p) -> str:
    if p in (None, ""):
        return "—"
    try:
        v = float(p)
    except (TypeError, ValueError):
        return "—"
    return "free" if v == 0 else f"${v * 1e6:.2f}/M"


def print_catalog(catalog: dict) -> None:
    by_provider = catalog.get("by_provider", {})
    if not by_provider:
        print("(empty catalog — run: python3 scripts/model-scout-current.py --catalog)")
        return
    for provider in sorted(by_provider):
        bucket = by_provider[provider]
        print(f"\n=== {provider} ===")
        for role in ("primary", "secondary"):
            for m in bucket.get(role, []):
                print(
                    f"  [{role:<9}] {m['model_id']:<42} "
                    f"{m.get('tier_hint',''):<3} in {_fmt_price(m.get('prompt_price'))}"
                    f"  out {_fmt_price(m.get('completion_price'))}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal model chooser")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--list", action="store_true", help="print catalog and exit")
    parser.add_argument("--primary", help="model id to pin as primary (capable)")
    parser.add_argument("--secondary", help="model id to pin as secondary (cheap)")
    parser.add_argument("--race", help="space-separated model ids for race lanes")
    parser.add_argument("--out", default=str(DEFAULT_SELECTION))
    parser.add_argument("--apply", action="store_true", help="pin into model-roster.conf")
    args = parser.parse_args(argv)

    catalog_path = Path(args.catalog)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}

    if args.list or not (args.primary or args.secondary):
        print_catalog(catalog)
        if args.list:
            return 0
        if not (args.primary or args.secondary):
            print("\nPick with: --primary <id> --secondary <id> [--apply]")
            return 0

    selection = {
        "primary": args.primary,
        "secondary": args.secondary,
        "race": args.race.split() if args.race else [],
        "generated_from": "choose-model.py",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"selection written: {out}")

    if args.apply:
        result = subprocess.run(
            [sys.executable, str(APPLY_SCRIPT), "--in", str(out)],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        sys.stdout.write(result.stdout)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
