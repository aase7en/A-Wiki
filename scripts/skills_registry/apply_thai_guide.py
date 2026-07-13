#!/usr/bin/env python3
"""Apply Thai guide content (thai_guide.py) to skills-registry.json.

Idempotent: re-running only updates skills listed in THAI_GUIDE and never
removes fields from skills that are not listed.

Usage:
    python scripts/skills_registry/apply_thai_guide.py
    python scripts/skills_registry/apply_thai_guide.py --dry-run
    python scripts/skills_registry/apply_thai_guide.py --validate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import validate_registry  # noqa: E402
from skills_registry.thai_guide import THAI_GUIDE  # noqa: E402

REGISTRY = REPO_ROOT / "skills-registry.json"


def apply(dry_run: bool = False) -> int:
    if not REGISTRY.exists():
        print(f"❌ {REGISTRY} not found", file=sys.stderr)
        return 1

    with open(REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills = data.get("skills", [])
    by_name = {s["name"]: s for s in skills if "name" in s}

    updated = 0
    missing = []
    # Keys that are documentation-only and must NOT be written to the registry.
    NON_REGISTRY_KEYS = {"_note"}
    for name, fields in THAI_GUIDE.items():
        if name not in by_name:
            missing.append(name)
            continue
        skill = by_name[name]
        changed = False
        for key, value in fields.items():
            if key in NON_REGISTRY_KEYS:
                continue
            if skill.get(key) != value:
                skill[key] = value
                changed = True
        if changed:
            updated += 1

    if missing:
        print(f"⚠️  {len(missing)} skill(s) in THAI_GUIDE not found in registry:")
        for m in missing:
            print(f"   - {m}")

    print(f"✅ Updated {updated} skill(s) with Thai guide content")
    print(f"   (THAI_GUIDE has {len(THAI_GUIDE)} entries; {len(missing)} missing)")

    if dry_run:
        print("🔍 Dry-run mode — no changes written.")
        return 0

    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Validate after write
    errors = validate_registry(REGISTRY)
    if errors:
        print(f"❌ Registry invalid after apply ({len(errors)} errors):", file=sys.stderr)
        for e in errors[:10]:
            print(f"   {e}", file=sys.stderr)
        return 2

    print("✅ Registry valid after apply.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Thai guide to skills-registry.json")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    ap.add_argument("--validate", action="store_true", help="Only validate the registry")
    args = ap.parse_args()

    if args.validate:
        errors = validate_registry(REGISTRY)
        if errors:
            print(f"❌ {len(errors)} validation error(s):")
            for e in errors:
                print(f"   {e}")
            return 2
        print("✅ Registry valid.")
        return 0

    return apply(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
