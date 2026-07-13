#!/usr/bin/env python3
"""Apply Thai guide content (thai_guide.py) to skills-registry.json.

Idempotent: re-running only updates skills listed in THAI_GUIDE and never
removes fields from skills that are not listed.

Two sources of Thai content:
  (a) Hand-written   — thai_guide.py THAI_GUIDE dict (default source)
  (b) LLM-generated  — skills-registry.json.proposed (from batch_thai.py)

Usage:
    # (a) Apply hand-written content from thai_guide.py
    python scripts/skills_registry/apply_thai_guide.py
    python scripts/skills_registry/apply_thai_guide.py --dry-run
    python scripts/skills_registry/apply_thai_guide.py --validate

    # (b) Apply LLM-generated content from .proposed (Senior Critic review)
    python scripts/skills_registry/apply_thai_guide.py --from-proposed
    python scripts/skills_registry/apply_thai_guide.py --from-proposed --review
    python scripts/skills_registry/apply_thai_guide.py --from-proposed --dry-run
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
PROPOSED = REPO_ROOT / "skills-registry.json.proposed"

# Keys that are documentation-only and must NOT be written to the registry.
NON_REGISTRY_KEYS = {"_note"}


def apply(dry_run: bool = False) -> int:
    """Apply hand-written THAI_GUIDE content to the registry."""
    if not REGISTRY.exists():
        print(f"❌ {REGISTRY} not found", file=sys.stderr)
        return 1

    with open(REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills = data.get("skills", [])
    by_name = {s["name"]: s for s in skills if "name" in s}

    updated = 0
    missing = []
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


def apply_proposed(dry_run: bool = False, review: bool = False) -> int:
    """Merge skills-registry.json.proposed into the registry.

    Iron Law #3 (Senior Critic): when --review is set, every entry is shown
    to the user with its proposed values; they choose (y/skip/edit/quit).
    Without --review, all entries are applied (still gated by quality_gate
    having run during batch_thai.py).
    """
    if not PROPOSED.exists():
        print(f"❌ {PROPOSED} not found. Run batch_thai.py first.", file=sys.stderr)
        return 1

    with open(REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(PROPOSED, "r", encoding="utf-8") as f:
        proposed = json.load(f)

    skills = data.get("skills", [])
    by_name = {s["name"]: s for s in skills if "name" in s}

    applied = 0
    skipped = 0
    missing = []
    approved: dict[str, dict] = {}  # entries the user approved (for --review mode)

    for name, fields in proposed.items():
        if name not in by_name:
            missing.append(name)
            continue
        skill = by_name[name]

        if review:
            print(f"\n─ {name} ─────────────────────────")
            for key, val in fields.items():
                cur = skill.get(key)
                if cur == val:
                    print(f"  {key}: (unchanged)")
                else:
                    print(f"  {key}:")
                    if cur:
                        print(f"    now: {json.dumps(cur, ensure_ascii=False)[:120]}")
                    print(f"    new: {json.dumps(val, ensure_ascii=False)[:120]}")
            try:
                choice = input("  [y]es / [s]kip / [a]ll-rest / [q]uit: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\naborted")
                return 1
            if choice in {"q", "quit"}:
                print("quitting (no further prompts)")
                break
            if choice in {"a", "all", "all-rest"}:
                review = False  # disable per-entry prompt for the rest
                choice = "y"
            if choice not in {"y", "yes"}:
                skipped += 1
                continue

        changed = False
        for key, value in fields.items():
            if key in NON_REGISTRY_KEYS:
                continue
            if skill.get(key) != value:
                skill[key] = value
                changed = True
        if changed:
            applied += 1
            approved[name] = fields

    if missing:
        print(f"\n⚠️  {len(missing)} proposed entry(s) not found in registry:")
        for m in missing:
            print(f"   - {m}")

    print(f"\n✅ Applied {applied} | skipped {skipped} | {len(missing)} missing")

    if dry_run:
        print("🔍 Dry-run mode — no changes written.")
        return 0

    if applied == 0:
        print("ℹ️  Nothing to apply.")
        return 0

    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    errors = validate_registry(REGISTRY)
    if errors:
        print(f"❌ Registry invalid after apply ({len(errors)} errors):", file=sys.stderr)
        for e in errors[:10]:
            print(f"   {e}", file=sys.stderr)
        return 2

    print("✅ Registry valid after apply.")

    # In review mode, write back only the approved entries to .proposed so a
    # subsequent non-review run is a no-op for the approved ones.
    if review and approved:
        with open(PROPOSED, "w", encoding="utf-8") as f:
            json.dump(approved, f, ensure_ascii=False, indent=2)
        print(f"📝 Updated {PROPOSED.name} to {len(approved)} approved entries")
    elif not review:
        # Non-review apply = trust the whole .proposed; clear it after apply.
        PROPOSED.unlink()
        print(f"🧹 Cleared {PROPOSED.name} (all entries applied)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Thai guide to skills-registry.json")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    ap.add_argument("--validate", action="store_true", help="Only validate the registry")
    ap.add_argument("--from-proposed", action="store_true",
                    help="Merge from skills-registry.json.proposed (LLM output) instead of thai_guide.py")
    ap.add_argument("--review", action="store_true",
                    help="With --from-proposed: prompt per-entry (y/skip/all-rest/quit). Iron Law #3 gate.")
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

    if args.from_proposed:
        return apply_proposed(dry_run=args.dry_run, review=args.review)

    return apply(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
