#!/usr/bin/env python3
"""
regen-skill-surfaces.py — regenerate per-agent skill surfaces from the registry
=============================================================================

Single command that keeps every agent's view of A-Wiki skills in sync with the
single source of truth (``skills-registry.json``).

Usage
-----
::

    # Normal: regenerate all surfaces from the registry, write to disk.
    python scripts/regen-skill-surfaces.py

    # CI mode: refuse to exit 0 if any generated surface has drifted.
    python scripts/regen-skill-surfaces.py --check

    # First-time bootstrap: scan all skill surfaces and emit a DRAFT registry
    # for human review (does NOT overwrite an existing registry).
    python scripts/regen-skill-surfaces.py --bootstrap --out skills-registry.draft.json

    # Validate the registry without writing anything.
    python scripts/regen-skill-surfaces.py --validate

Exit codes
----------
- 0 = success / no drift
- 1 = validation or drift failure (CI gate)
- 2 = unexpected error

See: docs/protocols/skill-frontmatter-schema.md
     A-Wiki Universal Skill Architecture (Chunk 1)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Emoji in status prints crash on non-UTF-8 consoles (Thai Windows = cp874),
# turning a clean --check into exit 1 — the pre-commit hook then misreads the
# crash as registry drift. Degrade unencodable characters instead of dying.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import (  # noqa: E402
    DriftError,
    Registry,
    validate_registry,
)
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
    gen_skill_index,
    gen_windsurf,
    gen_zcode,
    gen_zcode_agents,
)
from skills_registry.scan import build_draft_registry  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
SURFACES_DIR = REPO_ROOT / "scripts" / "skills_registry" / "generated"

# Registry of generators: {output_filename: generator_module}.
# To add a NEW agent surface in the future, add one entry here.
GENERATORS = {
    gen_kilo.filename: gen_kilo,
    gen_gemini.filename: gen_gemini,
    gen_cline.filename: gen_cline,
    gen_antigravity.filename: gen_antigravity,
    gen_hermes.filename: gen_hermes,
    gen_agents_md.filename: gen_agents_md,
    # USA-1 chunk C1 — four missing agent surfaces (was 6/9, now 10/9 + future).
    gen_codex.filename: gen_codex,
    gen_windsurf.filename: gen_windsurf,
    gen_openclaw.filename: gen_openclaw,
    gen_zcode.filename: gen_zcode,
    # SA2 — ZCode *agents* manifest (subagent definitions, not skills).
    gen_zcode_agents.filename: gen_zcode_agents,
    # USA-1 chunk C8 — central skill brain (USA-1 §6). Written to wiki/, not
    # generated/, because it is the agent-readable brain consumed at session start.
    gen_skill_index.filename: gen_skill_index,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_registry(path: Path) -> Registry:
    errors = validate_registry(path)
    if errors:
        print("🚨 skills-registry.json is invalid:", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
        raise SystemExit(1)
    return Registry.load(path)


def _output_path(filename: str) -> Path:
    """Resolve where a generated surface should be written.

    Most surfaces live under SURFACES_DIR (generated/, gitignored machine files).
    The central skill brain (SKILL-INDEX.md, USA-1 §6) lives under wiki/ because
    it is the agent-readable brain consumed at session start, not a machine blob.
    """
    if filename == "SKILL-INDEX.md":
        return REPO_ROOT / "wiki" / filename
    return SURFACES_DIR / filename


def cmd_regenerate(args: argparse.Namespace) -> int:
    """Regenerate all surfaces from the registry (default action)."""
    reg = _load_registry(REGISTRY_PATH)
    SURFACES_DIR.mkdir(parents=True, exist_ok=True)
    (REPO_ROOT / "wiki").mkdir(parents=True, exist_ok=True)

    # Touch a .gitkeep so the dir is tracked even before first generation.
    (SURFACES_DIR / ".gitkeep").touch()

    print(f"✅ Regenerating {len(GENERATORS)} surface(s) from skills-registry.json")
    print(f"   ({len(reg.skills)} skills, {len(reg.canonical_names())} canonical)")
    for filename, gen in GENERATORS.items():
        content = gen.render(reg)
        out = _output_path(filename)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        rel = out.relative_to(REPO_ROOT)
        print(f"   ✓ {rel} ({len(content)} bytes)")
    print(f"✅ Surfaces regenerated.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """CI mode: exit 1 if any generated surface has drifted from the registry.

    Surfaces may live in different dirs (most in generated/, the skill brain
    SKILL-INDEX.md in wiki/ per USA-1 §6), so we resolve each output path via
    _output_path rather than assuming a single surfaces_dir.
    """
    reg = _load_registry(REGISTRY_PATH)
    generated = {filename: gen.render(reg) for filename, gen in GENERATORS.items()}

    # First, the standard generated/-dir surfaces via the drift module.
    gen_dir_surfaces = {
        fn: content for fn, content in generated.items()
        if _output_path(fn).parent == SURFACES_DIR
    }
    try:
        drift_mod.detect_and_raise(REGISTRY_PATH, SURFACES_DIR, gen_dir_surfaces)
    except DriftError as exc:
        print(f"🚨 Drift detected: {exc}", file=sys.stderr)
        print("   Run `python scripts/regen-skill-surfaces.py` to fix.", file=sys.stderr)
        return 1

    # Then, out-of-dir surfaces (currently just the wiki/SKILL-INDEX.md brain).
    for filename, expected in generated.items():
        out = _output_path(filename)
        if out.parent == SURFACES_DIR:
            continue  # already checked above
        if not out.exists():
            print(f"🚨 Drift detected: {filename} missing at {out}", file=sys.stderr)
            print("   Run `python scripts/regen-skill-surfaces.py` to fix.", file=sys.stderr)
            return 1
        actual = out.read_text(encoding="utf-8")
        # Use the same timestamp normaliser as the drift module.
        if drift_mod._normalize(actual) != drift_mod._normalize(expected):
            print(f"🚨 Drift detected: {filename} content does not match registry output", file=sys.stderr)
            print("   Run `python scripts/regen-skill-surfaces.py` to fix.", file=sys.stderr)
            return 1

    print(f"✅ No drift — {len(generated)} surface(s) match the registry.")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """Scan all skill surfaces and emit a DRAFT registry for review."""
    out_path = Path(args.out) if args.out else REPO_ROOT / "skills-registry.draft.json"
    if out_path.exists() and not args.force:
        print(f"🚨 {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    draft = build_draft_registry(REPO_ROOT, generated_at="DRAFT-NEEDS-HUMAN-REVIEW")
    out_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")

    n = len(draft["skills"])
    by_domain: dict[str, int] = {}
    for s in draft["skills"]:
        for d in s["domain"]:
            by_domain[d] = by_domain.get(d, 0) + 1

    print(f"✅ Draft registry written to {out_path}")
    print(f"   {n} skills discovered across all surfaces")
    print("   Domain distribution:")
    for d in sorted(by_domain, key=lambda k: -by_domain[k]):
        print(f"     {d:20s} {by_domain[d]}")
    print()
    print("   ⚠️  This is a DRAFT. Review domain/lifecycle assignments before")
    print("       promoting to skills-registry.json. Heuristics are best-effort.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate the registry without writing anything."""
    errors = validate_registry(REGISTRY_PATH)
    if errors:
        print("🚨 skills-registry.json is invalid:", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
        return 1
    print("✅ skills-registry.json is valid.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[1] if __doc__ else "Regenerate skill surfaces.",
    )
    ap.add_argument(
        "--check", action="store_true",
        help="CI mode: exit 1 if generated surfaces have drifted from the registry.",
    )
    ap.add_argument(
        "--bootstrap", action="store_true",
        help="Scan all skill surfaces and emit a DRAFT registry for review.",
    )
    ap.add_argument(
        "--validate", action="store_true",
        help="Validate the registry without writing anything.",
    )
    ap.add_argument("--out", help="Output path for --bootstrap (default: skills-registry.draft.json).")
    ap.add_argument("--force", action="store_true", help="Overwrite existing draft in --bootstrap mode.")
    a = ap.parse_args()

    if a.bootstrap:
        return cmd_bootstrap(a)
    if a.validate:
        return cmd_validate(a)
    if a.check:
        return cmd_check(a)
    return cmd_regenerate(a)


if __name__ == "__main__":
    raise SystemExit(main())
