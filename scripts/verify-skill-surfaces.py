#!/usr/bin/env python3
"""
verify-skill-surfaces.py — cross-agent skill visibility smoke test
===================================================================

Asserts that every canonical skill in skills-registry.json is discoverable by
every agent surface the registry serves. This catches drift between the
single source of truth (registry) and the generated per-agent views.

Usage
-----
::

    python scripts/verify-skill-surfaces.py            # report + exit 0/1
    python scripts/verify-skill-surfaces.py --json     # machine-readable

Exit codes
----------
- 0 = all canonical skills visible across all surfaces, no drift
- 1 = visibility gaps or drift detected

See: docs/architecture/skill-architecture-plan.md (Chunk 5)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Degrade unencodable characters instead of crashing on non-UTF-8 consoles
# (Thai Windows = cp874) — same pattern as scripts/check-privacy.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry, validate_registry  # noqa: E402
from skills_registry import drift as drift_mod  # noqa: E402
from skills_registry.generators import (  # noqa: E402
    gen_agents_md,
    gen_antigravity,
    gen_cline,
    gen_codex,
    gen_gemini,
    gen_hermes,
    gen_kilo,
    gen_openclaw,
    gen_windsurf,
    gen_zcode,
    gen_zcode_agents,
)

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
SURFACES_DIR = REPO_ROOT / "scripts" / "skills_registry" / "generated"

# Surfaces the verifier owns: {filename: generator}.
# Every generator whose output lands in SURFACES_DIR belongs here. gen_skill_index
# is deliberately absent — it writes to wiki/SKILL-INDEX.md, not SURFACES_DIR, and
# the drift check below assumes a single directory. regen --check covers that one.
SURFACES = {
    gen_kilo.filename: gen_kilo,
    gen_gemini.filename: gen_gemini,
    gen_cline.filename: gen_cline,
    gen_antigravity.filename: gen_antigravity,
    gen_hermes.filename: gen_hermes,
    gen_agents_md.filename: gen_agents_md,
    gen_codex.filename: gen_codex,
    gen_windsurf.filename: gen_windsurf,
    gen_openclaw.filename: gen_openclaw,
    gen_zcode.filename: gen_zcode,
    gen_zcode_agents.filename: gen_zcode_agents,
}

# Agent-scoped skills (agents list WITHOUT "all") are invisible to the shared
# index by design — they must instead be visible in their own agent's surface.
# {agent tag: generators that agent actually consumes}
AGENT_SURFACES = {
    "zcode": (gen_zcode, gen_zcode_agents),
    "hermes": (gen_hermes,),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    report: dict = {"ok": True, "errors": [], "stats": {}}

    # 1. Registry validity
    errors = validate_registry(REGISTRY_PATH)
    if errors:
        report["ok"] = False
        report["errors"].extend(f"registry: {e}" for e in errors)
        return _emit(report, a.json)

    reg = Registry.load(REGISTRY_PATH)
    canonical = reg.canonical_names()
    report["stats"]["total_skills"] = len(reg.skills)
    report["stats"]["canonical_skills"] = len(canonical)
    report["stats"]["aliases"] = len([s for s in reg.skills if s.get("status") == "alias"])
    report["stats"]["deprecated"] = len([s for s in reg.skills if s.get("status") == "deprecated"])

    # 2. Drift check
    generated = {fn: gen.render(reg) for fn, gen in SURFACES.items()}
    drift_errors = drift_mod.detect(REGISTRY_PATH, SURFACES_DIR, generated)
    if drift_errors:
        report["ok"] = False
        report["errors"].extend(f"drift: {e}" for e in drift_errors)

    # 3. Shared visibility: every skill scoped to "all" must reach the shared index.
    #
    # This compares like with like. gen_agents_md renders canonical_for_agent("all"),
    # so testing it against canonical_names() (which includes agent-scoped skills)
    # reports skills that are absent BY DESIGN — e.g. the 31 zcode-only subagents.
    # Those are covered by check 3b instead.
    index = gen_agents_md.render(reg)
    shared = [s["name"] for s in reg.canonical_for_agent("all")]
    missing_from_index = [n for n in shared if f"`{n}`" not in index]
    if missing_from_index:
        report["ok"] = False
        report["errors"].append(
            f"{len(missing_from_index)} shared skill(s) missing from skills-index: "
            f"{missing_from_index[:5]}"
        )
    report["stats"]["shared_skills"] = len(shared)
    report["stats"]["visible_in_index"] = len(shared) - len(missing_from_index)

    # 3b. Agent-scoped visibility: a skill excluded from the shared index must be
    # visible in the surface of at least one agent it IS scoped to. Otherwise it is
    # registered but unreachable by every agent — a silent orphan.
    scoped = [s for s in reg.skills if s.get("status") == "canonical" and s["name"] not in set(shared)]
    rendered: dict[str, str] = {}
    orphan_scoped: list[str] = []
    for s in scoped:
        agents = s.get("agents") or []
        found = False
        for agent in agents:
            for gen in AGENT_SURFACES.get(agent, ()):
                key = gen.filename
                if key not in rendered:
                    rendered[key] = gen.render(reg)
                if s["name"] in rendered[key]:
                    found = True
                    break
            if found:
                break
        if not found:
            orphan_scoped.append(f"{s['name']} (agents={agents})")
    if orphan_scoped:
        report["ok"] = False
        report["errors"].append(
            f"{len(orphan_scoped)} agent-scoped skill(s) not visible in any agent surface: "
            f"{orphan_scoped[:5]}"
        )
    report["stats"]["agent_scoped_skills"] = len(scoped)
    report["stats"]["visible_in_agent_surface"] = len(scoped) - len(orphan_scoped)

    # 4. Alias integrity
    orphan_aliases = []
    for s in reg.skills:
        if s.get("status") == "alias":
            target = s.get("canonical")
            resolved = reg.get(target) if target else None
            if not resolved or resolved.get("status") == "alias":
                orphan_aliases.append(s["name"])
    if orphan_aliases:
        report["ok"] = False
        report["errors"].append(f"orphan aliases: {orphan_aliases[:5]}")

    return _emit(report, a.json)


def _emit(report: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        stats = report["stats"]
        if report["ok"]:
            print(f"✅ Cross-agent skill visibility OK")
            print(f"   {stats.get('canonical_skills', 0)} canonical skills across {len(SURFACES)} surface(s)")
            print(f"     ├─ {stats.get('visible_in_index', 0)}/{stats.get('shared_skills', 0)} shared (agents=all) visible in skills-index")
            print(f"     └─ {stats.get('visible_in_agent_surface', 0)}/{stats.get('agent_scoped_skills', 0)} agent-scoped visible in their own agent surface")
            print(f"   {stats.get('aliases', 0)} aliases, {stats.get('deprecated', 0)} deprecated")
            print(f"   no drift, no orphan aliases")
        else:
            print(f"🚨 Cross-agent visibility FAILED:", file=sys.stderr)
            for e in report["errors"]:
                print(f"   - {e}", file=sys.stderr)
            print(f"   fix: python scripts/regen-skill-surfaces.py", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
