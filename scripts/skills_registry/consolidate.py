"""Apply the audited consolidation plan to skills-registry.json.

This is the Chunk 2 mutation tool. It takes the human-verified action matrix
(from the deep audit + dedup.detect_clusters) and applies it to the registry:
  - marks aliases (status + canonical)
  - marks deprecated stubs (status + migrated_to)
  - removes deleted entries (true duplicates) after recording them as aliases

The action matrix is encoded as a Python data structure here (not parsed from
JSON) so it is version-controlled, reviewable in the diff, and auditable.

Idempotent: running twice produces the same registry.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Human-verified action matrix (from 3-agent deep audit, Chunk 2 of plan)
# Each entry: {name, action, canonical, note}
# ---------------------------------------------------------------------------

CONSOLIDATION_ACTIONS: list[dict[str, str]] = [
    # --- TRUE DUPLICATE: skill-creator ×3 ---
    # Anthropic version (485 lines, eval-driven) is canonical. The claude-code +
    # delegation copies are identical Manus-flavored 236-line forks. The scanner
    # already dedups by name and kept the anthropic-skills path (source priority).
    # We record the mirror paths so generators know where the duplicates live,
    # and note them as superseded. We do NOT delete files (Iron Law safety).
    {"name": "skill-creator", "action": "mark-canonical-with-mirrors", "mirror_paths": [
        "skills/claude-code/skill-creator",
        "skills/delegation/skill-creator",
    ], "note": "3 copies exist; anthropic-skills version is canonical, claude-code + delegation are Manus-fork mirrors"},

    # --- THIN STUB re-routes (already stubs — formalize) ---
    {"name": "hipaa-compliance", "action": "alias", "canonical": "healthcare-phi-compliance", "note": "declared thin entrypoint in audit"},
    {"name": "token-budget-advisor", "action": "alias", "canonical": "context-budget", "note": "defers heuristics to context-budget"},
    {"name": "root-cause-first", "action": "deprecated", "canonical": "debug-mantra", "note": "superseded by debug-mantra (deprecated stub in skills/deprecated/)"},

    # --- NEAR-DUP alias: verification cluster (keep content, alias surface) ---
    {"name": "laravel-verification", "action": "alias", "canonical": "django-verification", "note": "near-dup: identical 5-phase shape, different framework"},
    {"name": "quarkus-verification", "action": "alias", "canonical": "django-verification", "note": "near-dup: identical 5-phase shape, different framework"},
    {"name": "springboot-verification", "action": "alias", "canonical": "django-verification", "note": "near-dup: identical 5-phase shape, different framework"},
]


def apply_consolidation(registry_path: Path) -> dict[str, Any]:
    """Apply CONSOLIDATION_ACTIONS to the registry. Returns a summary.

    Idempotent: safe to run multiple times.
    """
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills_by_name: dict[str, dict[str, Any]] = {s["name"]: s for s in data["skills"]}
    summary = {"applied": [], "skipped": [], "renamed": []}

    for action in CONSOLIDATION_ACTIONS:
        name = action["name"]
        act = action["action"]

        if act == "mark-canonical-with-mirrors":
            # A canonical skill that has duplicate copies elsewhere. Record the
            # mirror paths without deleting them (Iron Law safety). This skill
            # stays canonical; the mirrors are noted for later cleanup.
            if name not in skills_by_name:
                summary["skipped"].append(f"{name} not in registry")
                continue
            skill = skills_by_name[name]
            mirrors = action.get("mirror_paths", [])
            existing = skill.get("mirror_paths", [])
            merged = sorted(set(existing) | set(mirrors))
            if merged == existing:
                summary["skipped"].append(f"{name} mirrors already recorded")
                continue
            skill["mirror_paths"] = merged
            summary["applied"].append(f"{name}: recorded {len(mirrors)} mirror path(s)")
            continue

        if name not in skills_by_name:
            summary["skipped"].append(f"{name} not in registry")
            continue

        skill = skills_by_name[name]

        if act == "alias":
            canonical = action["canonical"]
            if skill.get("status") == "alias" and skill.get("canonical") == canonical:
                summary["skipped"].append(f"{name} already aliased → {canonical}")
                continue
            skill["status"] = "alias"
            skill["canonical"] = canonical
            # Ensure the canonical exists; if not, warn but still apply (reviewer will fix).
            if canonical not in skills_by_name:
                summary["applied"].append(f"⚠️  {name} → alias of {canonical} (canonical MISSING)")
            else:
                summary["applied"].append(f"{name} → alias of {canonical}")

        elif act == "deprecated":
            canonical = action["canonical"]
            skill["status"] = "deprecated"
            skill["migrated_to"] = canonical
            summary["applied"].append(f"{name} → deprecated (migrated_to: {canonical})")

    # Rebuild skills list (sorted) and write back.
    data["skills"] = sorted(skills_by_name.values(), key=lambda s: s["name"])

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return summary


if __name__ == "__main__":
    import subprocess
    import sys
    registry_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "skills-registry.json"
    result = apply_consolidation(registry_path)
    print(f"Applied: {len(result['applied'])}")
    for line in result["applied"]:
        print(f"  ✓ {line}")
    if result["renamed"]:
        print(f"Renamed: {len(result['renamed'])}")
        for line in result["renamed"]:
            print(f"  ✓ {line}")
    if result["skipped"]:
        print(f"Skipped: {len(result['skipped'])}")
        for line in result["skipped"]:
            print(f"  → {line}")

    # CLICK-PATH-003 fix: chain surface regen so generated/ stays in sync.
    # consolidate.py mutates the registry; without this, generated surfaces go stale
    # and CI --check fails on the next push.
    if result["applied"] or result["renamed"]:
        print("\n--- Regenerating surfaces (registry changed) ---")
        regen = REPO_ROOT / "scripts" / "regen-skill-surfaces.py"
        proc = subprocess.run(
            [sys.executable, str(regen)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            print("✅ Surfaces regenerated from updated registry.")
        else:
            print(f"⚠️  regen failed (exit {proc.returncode}):\n{proc.stderr}", file=sys.stderr)
            print("   Run manually: python scripts/regen-skill-surfaces.py", file=sys.stderr)
