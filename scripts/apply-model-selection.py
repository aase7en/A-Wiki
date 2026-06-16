#!/usr/bin/env python3
"""
apply-model-selection.py — Pin a user's model choice into model-roster.conf.

Reads a selection (from the `models` render-html chooser round-trip, or
choose-model.py) and pins it into wiki/context/model-roster.conf using a
cost-first mapping:

  secondary (cheap/fast/free) → TIER1_PRIMARY     (search / lookup / summarize)
  primary   (flagship/capable)→ TIER2_PRIMARY     (reason / compare)
                              → TIER3_PRIMARY     (scan / long-context)
  secondary                   → TIER2_FALLBACK1   (cheap fallback for reasoning)
  race[]                      → RACE_MODELS        (parallel lanes)

Selection JSON shape:
  {"primary": "z-ai/glm-4.6", "secondary": "google/gemini-2.5-flash:free",
   "race": ["z-ai/glm-4.6", "google/gemini-2.5-flash:free"]}

Usage:
  apply-model-selection.py [--in .tmp/model-selection.json] [--roster <conf>]
                           [--dry-run] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = REPO_ROOT / ".tmp" / "model-selection.json"
DEFAULT_ROSTER = REPO_ROOT / "wiki" / "context" / "model-roster.conf"


def plan_changes(selection: dict) -> dict[str, str]:
    """Map a selection dict to roster variable assignments (cost-first)."""
    changes: dict[str, str] = {}
    secondary = selection.get("secondary")
    primary = selection.get("primary")
    race = selection.get("race") or []

    if secondary:
        changes["TIER1_PRIMARY"] = secondary
        changes["TIER2_FALLBACK1"] = secondary
    if primary:
        changes["TIER2_PRIMARY"] = primary
        changes["TIER3_PRIMARY"] = primary
    if not race:
        race = [m for m in (primary, secondary) if m]
    if race:
        changes["RACE_MODELS"] = " ".join(race)
    return changes


def apply_changes(text: str, changes: dict[str, str]) -> str:
    """Replace `VAR="..."` lines in roster text, appending any that are absent."""
    lines = text.splitlines()
    seen: set[str] = set()
    for i, line in enumerate(lines):
        m = re.match(r"^(\w+)=", line)
        if m and m.group(1) in changes:
            var = m.group(1)
            lines[i] = f'{var}="{changes[var]}"'
            seen.add(var)
    appended = [f'{v}="{val}"' for v, val in changes.items() if v not in seen]
    if appended:
        lines.append("")
        lines.append("# Pinned by model chooser (apply-model-selection.py)")
        lines.extend(appended)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pin model selection into roster")
    parser.add_argument("--in", dest="infile", default=str(DEFAULT_SELECTION))
    parser.add_argument("--roster", default=str(DEFAULT_ROSTER))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    selection = json.loads(Path(args.infile).read_text(encoding="utf-8"))
    roster_path = Path(args.roster)
    text = roster_path.read_text(encoding="utf-8") if roster_path.exists() else ""
    changes = plan_changes(selection)
    new_text = apply_changes(text, changes)

    if not args.dry_run:
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(new_text, encoding="utf-8")

    if args.json:
        print(json.dumps({"roster_path": str(roster_path), "changed": changes, "dry_run": args.dry_run},
                         ensure_ascii=False))
    else:
        verb = "would change" if args.dry_run else "pinned"
        for var, val in changes.items():
            print(f"{verb} {var}={val}")
        if not changes:
            print("no changes (empty selection)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
