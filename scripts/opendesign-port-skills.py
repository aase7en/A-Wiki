#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opendesign-port-skills.py — Port A-Wiki skills into Open Design's user skills dir.

== WHAT IT DOES ==
For each skill in TIER1 (and optionally TIER2), this script:
  1. Reads the A-Wiki SKILL.md (resolving symlinks to the real source path).
  2. Splits the file into (frontmatter, body).
  3. Builds a NEW Open Design frontmatter with the correct `od.mode/category/
     surface/scenario` schema (the original A-Wiki frontmatter is discarded —
     OD's normalizeMode/Category/Surface validator expects its own schema).
  4. Writes the merged file to:
       %APPDATA%\\Open Design\\namespaces\\release-stable-win\\data\\skills\\<slug>\\SKILL.md
  5. Copies any sibling asset directories (themes/, scripts/, references/,
     templates/, assets/, canvas-fonts/) verbatim — these are referenced by
     relative path from the skill root, so they must travel alongside.

== IDEMPOTENT ==
Re-running overwrites the previous port (so you can refresh after A-Wiki
updates a skill). It NEVER touches the bundled OD skills (those live under
Programs\\ and are read-only).

== USAGE ==
  python scripts/opendesign-port-skills.py             # port TIER1 (8 skills)
  python scripts/opendesign-port-skills.py --tier 2    # port TIER1 + TIER2 (12)
  python scripts/opendesign-port-skills.py --list      # show plan, write nothing
  python scripts/opendesign-port-skills.py --only frontend-design,theme-factory

== SECURITY ==
This script copies only markdown + static asset directories. It never copies
secrets, never writes to a git-tracked A-Wiki path, and never touches the
user's default ~/.claude profile. The destination is the Open Design AppData
skills directory (private to this machine).

Authored: 2026-08-01 (a-loop Phase 2)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

# Resolve WIKI_ROOT dynamically: prefer the explicit env var, otherwise infer
# from this script's location (scripts/opendesign-port-skills.py lives at the
# repo root's scripts/ dir). Avoids hardcoding a machine-specific drive path.
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_ROOT = _SCRIPT_DIR.parent if (_SCRIPT_DIR.parent / "AGENTS.md").is_file() else Path.cwd()
WIKI_ROOT = Path(os.environ.get("A_WIKI_ROOT", str(_DEFAULT_ROOT)))
ZCODE_SKILLS = WIKI_ROOT / ".zcode" / "skills"
AWIKI_SKILLS = WIKI_ROOT / "skills" / "awiki"

APPDATA = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
# OD_DATA_DIR may override the namespace data dir; default to the observed one.
OD_DATA_DIR = Path(os.environ.get(
    "OD_DATA_DIR",
    APPDATA / "Open Design" / "namespaces" / "release-stable-win" / "data",
))
OD_USER_SKILLS = OD_DATA_DIR / "skills"

# Asset subdirs that travel alongside SKILL.md when present.
ASSET_DIRS = ("themes", "scripts", "references", "templates", "assets",
              "canvas-fonts", "core", "rules", "agents", "examples")

# ─────────────────────────────────────────────────────────────────────────────
# SKILL REGISTRY — A-Wiki skill slug → (source resolver, OD frontmatter spec)
# ─────────────────────────────────────────────────────────────────────────────
#
# `source` is a callable that returns the real source dir (resolve symlinks).
# `od` is the Open Design frontmatter to inject. Keys:
#   mode:     prototype | deck | template | image | video | audio | design-system
#   category: slug for Settings filter row
#   surface:  web | image | video | audio
#   scenario: design | marketing | engineering | product | general
# `triggers`: phrases that activate the skill in OD's chat
# `description_en`: English one-liner for the OD picker (per user request:
#   body stays original, description is EN for picker visibility).
# ─────────────────────────────────────────────────────────────────────────────


def _resolve(*candidates: str) -> Path:
    """Return the first existing real directory among candidates."""
    for c in candidates:
        # Try the .zcode symlink first (canonical entry point).
        p = (ZCODE_SKILLS / c).resolve()
        if p.is_dir() and (p / "SKILL.md").is_file():
            return p
        # Fall back to the awiki/ source for A- suite skills.
        p = (AWIKI_SKILLS / c).resolve()
        if p.is_dir() and (p / "SKILL.md").is_file():
            return p
    raise FileNotFoundError(f"could not resolve skill source for {candidates}")


TIER1 = {
    "frontend-design": {
        "source": lambda: _resolve("frontend-design"),
        "od": {
            "mode": "prototype", "category": "ui-design", "surface": "web",
            "scenario": "design",
        },
        "triggers": [
            "design a landing page", "design a dashboard",
            "design a react component", "design a poster",
            "create distinctive ui", "non-generic interface",
        ],
        "description_en": (
            "Create distinctive, production-grade frontend interfaces "
            "(landing pages, dashboards, components, posters) that avoid "
            "generic AI aesthetics."
        ),
    },
    "theme-factory": {
        "source": lambda: _resolve("theme-factory"),
        "od": {
            "mode": "design-system", "category": "design-systems",
            "surface": "web", "scenario": "design",
        },
        "triggers": [
            "apply a theme", "change theme", "10 themes",
            "theme for slides", "theme for landing page",
        ],
        "description_en": (
            "Apply one of 10 ready-made themes (or a custom one) to slides, "
            "docs, and HTML landing pages."
        ),
    },
    "make-interfaces-feel-better": {
        "source": lambda: _resolve("make-interfaces-feel-better"),
        "od": {
            "mode": "prototype", "category": "ui-design", "surface": "web",
            "scenario": "design",
        },
        "triggers": [
            "polish the interface", "make it feel professional",
            "improve spacing typography shadows", "design polish checklist",
        ],
        "description_en": (
            "Concrete design-engineering polish: spacing, typography, borders, "
            "shadows, motion, hit areas — turn 'generated' into 'professional'."
        ),
    },
    "design-system": {
        "source": lambda: _resolve("design-system"),
        "od": {
            "mode": "design-system", "category": "design-systems",
            "surface": "web", "scenario": "design",
        },
        "triggers": [
            "audit design system", "check visual consistency",
            "generate a design system", "review styling",
        ],
        "description_en": (
            "Generate or audit a design system, check visual consistency "
            "across artifacts, review styling decisions."
        ),
    },
    "frontend-slides": {
        "source": lambda: _resolve("frontend-slides"),
        "od": {
            "mode": "deck", "category": "presentations", "surface": "web",
            "scenario": "design",
        },
        "triggers": [
            "create a presentation", "html slides", "convert pptx to web",
            "animation-rich deck",
        ],
        "description_en": (
            "Create animation-rich HTML presentations and convert PPTX decks "
            "to web-native slides."
        ),
    },
    "web-artifacts-builder": {
        "source": lambda: _resolve("web-artifacts-builder"),
        "od": {
            "mode": "prototype", "category": "ui-design", "surface": "web",
            "scenario": "engineering",
        },
        "triggers": [
            "build a react artifact", "multi-component prototype",
            "shadcn ui artifact", "tailwind prototype",
        ],
        "description_en": (
            "Build elaborate multi-component React/Tailwind/shadcn-ui "
            "artifacts (prototypes, dashboards) as self-contained bundles."
        ),
    },
    "a-think": {
        "source": lambda: _resolve("a-think"),
        "od": {
            "mode": "template", "category": "reasoning", "surface": "web",
            "scenario": "general",
        },
        "triggers": [
            "think before designing", "reason about this",
            "restate the problem", "compare approaches",
            "pre-mortem", "7-step reasoning",
        ],
        "description_en": (
            "7-step reasoning loop (Restate → Done-criteria → Decompose → "
            "2+ approaches → Pre-mortem → Right-size → Prove) to drive "
            "decisions before generating."
        ),
    },
    "spec-driven-development": {
        "source": lambda: _resolve("spec-driven-development"),
        "od": {
            "mode": "template", "category": "reasoning", "surface": "web",
            "scenario": "engineering",
        },
        "triggers": [
            "write a spec first", "clarify requirements",
            "specification before building", "turn prompt into spec",
        ],
        "description_en": (
            "Turn a vague prompt into a structured spec (functional, "
            "non-functional, acceptance criteria) before generating."
        ),
    },
}

TIER2 = {
    "algorithmic-art": {
        "source": lambda: _resolve("algorithmic-art"),
        "od": {
            "mode": "image", "category": "image-generation", "surface": "image",
            "scenario": "design",
        },
        "triggers": [
            "generative art", "p5js art", "seeded randomness art",
            "algorithmic poster",
        ],
        "description_en": (
            "Generative art via p5.js with seeded randomness and interactive "
            "parameter exploration."
        ),
    },
    "motion-foundations": {
        "source": lambda: _resolve("motion-foundations"),
        "od": {
            "mode": "prototype", "category": "ui-design", "surface": "web",
            "scenario": "design",
        },
        "triggers": [
            "motion tokens", "spring presets", "animation foundation",
        ],
        "description_en": (
            "Motion tokens, spring presets, and performance/SSR rules for "
            "motion/react — the foundation layer for polished animation."
        ),
    },
    "motion-patterns": {
        "source": lambda: _resolve("motion-patterns"),
        "od": {
            "mode": "prototype", "category": "ui-design", "surface": "web",
            "scenario": "design",
        },
        "triggers": [
            "animate a modal", "page transition", "stagger animation",
            "toast animation",
        ],
        "description_en": (
            "Production animation patterns (modal, toast, stagger, page "
            "transitions) built on motion-foundations."
        ),
    },
    "canvas-design": {
        "source": lambda: _resolve("canvas-design"),
        "od": {
            "mode": "image", "category": "image-generation", "surface": "image",
            "scenario": "design",
        },
        "triggers": [
            "design a poster", "static visual art", "png poster",
            "pdf poster design",
        ],
        "description_en": (
            "Create static visual art and posters in .png and .pdf using a "
            "curated design philosophy and bundled font library."
        ),
    },
    "marketing-campaign": {
        "source": lambda: _resolve("marketing-campaign"),
        "od": {
            "mode": "prototype", "category": "marketing-creative",
            "surface": "web", "scenario": "marketing",
        },
        "triggers": [
            "marketing campaign", "landing page copy", "email sequence",
            "ad copy", "video script",
        ],
        "description_en": (
            "End-to-end campaign planning: audience, positioning, landing-page "
            "copy, email sequences, ad copy, and video scripts."
        ),
    },
}

ALL_SKILLS = {**TIER1, **TIER2}

# ─────────────────────────────────────────────────────────────────────────────
# FRONTMATTER BUILDER
# ─────────────────────────────────────────────────────────────────────────────


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """
    Split a SKILL.md into (frontmatter_dict_or_None, body).
    Handles both `---\n...\n---\n` and no-frontmatter cases.
    Does NOT parse values into typed objects — we discard the FM anyway.
    """
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    # We don't actually need to parse it; we replace it entirely.
    body_start = end + 4
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    return {"_discarded": True}, text[body_start:]


def build_od_frontmatter(slug: str, spec: dict) -> str:
    """Build the Open Design frontmatter block as a YAML string."""
    od = spec["od"]
    triggers = spec.get("triggers", [])
    desc = spec.get("description_en", slug)
    lines = ["---", f'name: "{slug}"', "description: |"]
    # Indent each line of the description by 2 spaces for YAML block scalar.
    for line in desc.splitlines() or [desc]:
        lines.append(f"  {line}")
    if triggers:
        lines.append("triggers:")
        for t in triggers:
            lines.append(f'  - "{t}"')
    lines.append("od:")
    for key in ("mode", "category", "surface", "scenario"):
        if key in od:
            lines.append(f"  {key}: {od[key]}")
    if "design_system" in od:
        lines.append("  design_system:")
        for k, v in od["design_system"].items():
            lines.append(f"    {k}: {'true' if v else 'false'}")
    if "capabilities_required" in od:
        lines.append("  capabilities_required:")
        for c in od["capabilities_required"]:
            lines.append(f"    - {c}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
# PORT LOGIC
# ─────────────────────────────────────────────────────────────────────────────


def port_skill(slug: str, spec: dict, dry_run: bool = False) -> dict:
    """
    Port a single skill. Returns a result dict:
      {slug, src, dst, status, body_bytes, assets_copied, error?}
    """
    result = {"slug": slug, "status": "error"}
    try:
        src_dir = spec["source"]()
    except FileNotFoundError as exc:
        result["error"] = str(exc)
        return result
    src_skill = src_dir / "SKILL.md"
    if not src_skill.is_file():
        result["error"] = f"no SKILL.md at {src_skill}"
        return result

    body_text = src_skill.read_text(encoding="utf-8")
    _, body = split_frontmatter(body_text)
    new_fm = build_od_frontmatter(slug, spec)
    merged = new_fm + "\n" + body.lstrip("\n")

    dst_dir = OD_USER_SKILLS / slug
    dst_skill = dst_dir / "SKILL.md"
    result["src"] = str(src_dir)
    result["dst"] = str(dst_dir)
    result["body_bytes"] = len(merged.encode("utf-8"))

    if dry_run:
        result["status"] = "dry-run"
        # list assets that WOULD be copied
        would_copy = []
        for sub in ASSET_DIRS:
            if (src_dir / sub).is_dir():
                would_copy.append(sub)
        result["assets_copied"] = would_copy
        return result

    # Write.
    dst_dir.mkdir(parents=True, exist_ok=True)
    # Clear previous asset dirs so a re-port is clean (idempotent overwrite).
    for sub in ASSET_DIRS:
        old = dst_dir / sub
        if old.is_dir():
            shutil.rmtree(old, ignore_errors=True)
    dst_skill.write_text(merged, encoding="utf-8")

    copied = []
    for sub in ASSET_DIRS:
        src_sub = src_dir / sub
        if src_sub.is_dir():
            shutil.copytree(src_sub, dst_dir / sub, dirs_exist_ok=True)
            copied.append(sub)
    result["assets_copied"] = copied
    result["status"] = "ok"
    return result


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Port A-Wiki skills into Open Design's user skills dir.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Destination: %(dest)s\nSource: A-Wiki .zcode/skills + skills/awiki"
            % {"dest": str(OD_USER_SKILLS)}
        ),
    )
    parser.add_argument("--tier", type=int, default=1, choices=(1, 2),
                        help="1 = port 8 Tier-1 skills; 2 = Tier-1 + 5 Tier-2")
    parser.add_argument("--list", action="store_true",
                        help="show the port plan and exit (write nothing)")
    parser.add_argument("--only", metavar="SLUGS",
                        help="comma-separated slugs to port (overrides --tier)")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve + build merged content, but write nothing")
    args = parser.parse_args(argv)

    if args.only:
        slugs = [s.strip() for s in args.only.split(",") if s.strip()]
        for s in slugs:
            if s not in ALL_SKILLS:
                print(f"ERROR: unknown slug {s!r}. Known: {sorted(ALL_SKILLS)}")
                return 2
        plan = {s: ALL_SKILLS[s] for s in slugs}
    elif args.tier == 1:
        plan = dict(TIER1)
    else:
        plan = dict(ALL_SKILLS)

    print(f"Open Design user skills dir: {OD_USER_SKILLS}")
    print(f"Plan: {len(plan)} skill(s) — tier={args.tier}, "
          f"only={args.only or '-'}\n")

    dry = args.list or args.dry_run
    results = []
    for slug, spec in plan.items():
        r = port_skill(slug, spec, dry_run=dry)
        results.append(r)
        status = r["status"]
        if status == "error":
            print(f"  ❌ {slug:32s} ERROR: {r.get('error', '?')}")
        elif status == "dry-run":
            assets = r.get("assets_copied", [])
            asset_str = f" +assets={assets}" if assets else ""
            print(f"  🔵 {slug:32s} would write {r['body_bytes']}B{asset_str}")
        else:
            assets = r.get("assets_copied", [])
            asset_str = f" +assets={assets}" if assets else ""
            print(f"  ✅ {slug:32s} wrote {r['body_bytes']}B{asset_str}")

    if not dry:
        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"\nDone: {ok}/{len(results)} ported. "
              f"Open Open Design → Settings → Skills → Rescan to load them.")

    # Exit non-zero only on hard errors.
    return 0 if all(r["status"] != "error" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
