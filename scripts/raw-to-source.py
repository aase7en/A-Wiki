#!/usr/bin/env python3
"""
raw-to-source.py — Auto-generate source frontmatter for raw files without a source entry.

Scans raw/ for .md files (excluding raw/README.md) that don't have a
corresponding wiki/sources/<slug>.md, then creates a source file with
auto-detected slug, domain, and tags.

Usage:
    python3 scripts/raw-to-source.py --dry-run   # Show what would be created
    python3 scripts/raw-to-source.py --apply     # Create source files
    python3 scripts/raw-to-source.py --all       # Force re-process all raw files
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "raw"
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"

# Domain keyword → domain tag mapping
DOMAIN_KEYWORDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"pharmacy|drug|medicine|vaccine|rabies|medication|prescription", re.IGNORECASE), "pharmacy"),
    (re.compile(r"esp32|esp32-s3|esp-idf|arduino|loRa|lora|lorawan|mqtt|sensor|iot|mcu|firmware|telemetry", re.IGNORECASE), "iot"),
    (re.compile(r"raspberry|pi5|pi-5|rpi", re.IGNORECASE), "iot"),
    (re.compile(r"grafana|influxdb|telegraf|nodered|node-red|dashboard", re.IGNORECASE), "iot"),
    (re.compile(r"env|waste|water|wastewater|air.quality|pollution|temperature.monitor", re.IGNORECASE), "env"),
    (re.compile(r"ai|llm|agent|gpt|openai|claude|gemini|ollama|langchain|rag|embedding", re.IGNORECASE), "ai-tools"),
    (re.compile(r"machine.learning|tinyml|tflite|tensorflow|pytorch", re.IGNORECASE), "ai-tools"),
]

DEFAULT_TAGS: dict[str, list[str]] = {
    "pharmacy": ["pharmacy"],
    "iot": ["iot"],
    "env": ["env"],
    "ai-tools": ["ai"],
}


def raw_to_slug(filename: str) -> str:
    """Convert raw filename to a URL-safe slug."""
    stem = Path(filename).stem  # strip .md
    # Thai characters and alphanumeric + hyphens only
    slug = stem.lower()
    slug = re.sub(r"[^a-z0-9\u0E00-\u0E7F]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    slug = slug[:60].rstrip("-")
    return slug


def detect_domain(filepath: Path) -> str:
    """Detect domain from parent directory, then filename."""
    # 1. Parent directory inside raw/
    rel = filepath.relative_to(RAW_DIR)
    parts = rel.parts
    if len(parts) > 1:
        # e.g. raw/pharmacy/sp_drugs.json → pharmacy
        dir_name = parts[-2].lower()
        if dir_name in ("pharmacy",):
            return "pharmacy"
        if dir_name in ("ai",):
            return "ai-tools"
        if dir_name in ("iot", "environment", "env", "it"):
            return "iot"
    # 2. Keyword match in filename
    fname = filepath.name
    for pattern, domain in DOMAIN_KEYWORDS:
        if pattern.search(fname):
            return domain
    return ""


def detect_tags(filepath: Path, domain: str) -> list[str]:
    """Auto-detect tags from filename and domain."""
    tags: list[str] = []
    if domain in DEFAULT_TAGS:
        tags.extend(DEFAULT_TAGS[domain])

    fname = filepath.stem.lower()
    # Technical keywords
    tech_map: list[tuple[re.Pattern, str]] = [
        (re.compile(r"esp32"), "esp32"),
        (re.compile(r"esp32-s3|esp32s3"), "esp32-s3"),
        (re.compile(r"arduino"), "arduino"),
        (re.compile(r"lo[řr]a|lorawan"), "lora"),
        (re.compile(r"mqtt"), "mqtt"),
        (re.compile(r"sensor"), "sensor"),
        (re.compile(r"raspberry"), "raspberry-pi"),
        (re.compile(r"grafana"), "grafana"),
        (re.compile(r"dashboard"), "dashboard"),
        (re.compile(r"pharmacy|drug|medicine"), "pharmacy"),
        (re.compile(r"vaccine|rabies"), "vaccine"),
        (re.compile(r"ai|llm|agent"), "ai"),
        (re.compile(r"ollama"), "ollama"),
        (re.compile(r"appsheet"), "appsheet"),
        (re.compile(r"webapp|web-app|web.app"), "webapp"),
        (re.compile(r"thai"), "thai"),
        (re.compile(r"guide|tutorial|course"), "guide"),
    ]
    for pat, tag in tech_map:
        if pat.search(fname) and tag not in tags:
            tags.append(tag)
    # Deduplicate but preserve order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def extract_title_from_body(text: str) -> str:
    """Extract best-guess title from H1 or first meaningful line."""
    for line in text.splitlines():
        line = line.strip()
        # Skip frontmatter
        if line == "---":
            break
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            return s[2:].strip()
    # Fallback: first non-empty, non-frontmatter line
    in_frontmatter = False
    for line in text.splitlines():
        s = line.strip()
        if s == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if s and not s.startswith("#") and not s.startswith("```"):
            return s[:80].rstrip(".")
    return ""


def collect_raw_files() -> list[Path]:
    """Collect all .md files in raw/ (excluding README.md and sub-READMEs)."""
    files: list[Path] = []
    for p in sorted(RAW_DIR.rglob("*.md")):
        if p.name == "README.md":
            continue
        # Skip provenance stubs under raw/legacy/ — these are backfilled
        # original_file pointers for frozen legacy sister-wiki sources, NOT
        # ingestable raw documents. Routing them would duplicate the existing
        # (subdir) source pages with garbage titles.
        if "legacy" in p.relative_to(RAW_DIR).parts:
            continue
        # Skip JSON within raw/
        if p.suffix == ".md":
            files.append(p)
    return files


def source_exists(slug: str) -> bool:
    """Check if a source file already exists for the given slug, anywhere under
    wiki/sources/ — flat (wiki/sources/<slug>.md) OR a domain subdir
    (wiki/sources/<domain>/<slug>.md). Subdir-aware so an existing subdir source
    is never duplicated as a bare-path file."""
    if (SOURCES_DIR / f"{slug}.md").exists():
        return True
    return any(True for _ in SOURCES_DIR.rglob(f"{slug}.md"))


def generate_frontmatter(
    filepath: Path, slug: str, domain: str, tags: list[str]
) -> str:
    """Generate the full source file content."""
    raw_text = filepath.read_text(encoding="utf-8")
    title = extract_title_from_body(raw_text) or filepath.stem
    today = dt.date.today().isoformat()
    rel_path = filepath.relative_to(REPO_ROOT)

    fm_lines = [
        "---",
        f"type: source",
        f"title: \"{title}\"",
        f"slug: {slug}",
        f"date_ingested: {today}",
        f"original_file: {rel_path}",
        f"tags: [{', '.join(tags)}]" if tags else "tags: []",
        "---",
        "",
        raw_text.strip(),
        "",
    ]
    return "\n".join(fm_lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-generate source frontmatter for raw files")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be created (no writes)")
    ap.add_argument("--apply", action="store_true", help="Actually create source files")
    ap.add_argument("--all", action="store_true", help="Force re-process ALL raw files (not just missing)")
    args = ap.parse_args()

    if not args.dry_run and not args.apply and not args.all:
        ap.print_help()
        print("\n⚠  Must specify --dry-run, --apply, or --all", file=sys.stderr)
        return 1

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = collect_raw_files()
    created_count = 0
    skipped_count = 0

    for filepath in raw_files:
        slug = raw_to_slug(filepath.name)
        rel = filepath.relative_to(REPO_ROOT)
        domain = detect_domain(filepath)
        tags = detect_tags(filepath, domain)

        # Check if source exists (skip unless --all)
        existing = source_exists(slug) or source_exists(f"{slug}-0")
        if existing and not args.all:
            skipped_count += 1
            continue

        content = generate_frontmatter(filepath, slug, domain, tags)

        if args.dry_run:
            print(f"  📄 {rel} → wiki/sources/{slug}.md  (domain={domain}, tags={tags})")
            continue

        if args.apply or args.all:
            dest = SOURCES_DIR / f"{slug}.md"
            dest.write_text(content, encoding="utf-8")
            print(f"  ✓ Created: wiki/sources/{slug}.md  (domain={domain})")
            created_count += 1

    if args.dry_run:
        print(f"\n  Summary: {len(raw_files)} raw files scanned, {created_count} would be created, {skipped_count} already exist")
    elif args.apply:
        print(f"\n  Summary: {len(raw_files)} raw files scanned, {created_count} created, {skipped_count} skipped")
    elif args.all:
        print(f"\n  Summary: {len(raw_files)} raw files scanned, {created_count} re-created (--all force)")

    return 0


if __name__ == "__main__":
    sys.exit(main())