#!/usr/bin/env python3
"""
raw-to-synth.py — Score existing sources (0-10) and auto-generate synthesis stubs for quality ≥ 5.

Scans wiki/sources/ for all .md source files, scores them on a quality rubric,
generates synthesis stubs for high-quality ones, and outputs a quality report table.

Usage:
    python3 scripts/raw-to-synth.py              # Full scan + synthesis generation
    python3 scripts/raw-to-synth.py --source <slug>  # Single source only
    python3 scripts/raw-to-synth.py --dry-run    # Scores only, no writes
    python3 scripts/raw-to-synth.py --json       # JSON output
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
SYNTHESIS_DIR = REPO_ROOT / "wiki" / "synthesis"

# ── Quality Scoring Rubric ──────────────────────────────────────────────

# | Criterion           | Max | Measure                                       |
# |---------------------|-----|-----------------------------------------------|
# | Word count          | 3   | >300=3pt, >100=2pt, >30=1pt                   |
# | Frontmatter complete| 2   | title+tags+date=2pt, partial=1pt              |
# | Section structure   | 2   | ≥3 `##` headers=2pt, 1-2=1pt                 |
# | Content richness    | 2   | code+table+bullets=2pt, one=1pt               |
# | Citation density    | 1   | references/links=1pt                          |
# | total               | 10  |                                               |


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter. Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str | list[str]] = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [s.strip().strip('"').strip("'") for s in val[1:-1].split(",")]
            meta[key] = [s for s in items if s]
        else:
            meta[key] = val.strip('"').strip("'")
    return meta, body


def word_count(text: str) -> int:
    """Count words in body text (excluding frontmatter)."""
    _, body = parse_frontmatter(text)
    # Strip markdown formatting for word count
    clean = re.sub(r"[#*_`\[\]()>|]", " ", body)
    # Remove code blocks
    clean = re.sub(r"```.*?```", "", clean, flags=re.DOTALL)
    words = clean.split()
    return len(words)


def score_word_count(text: str) -> int:
    n = word_count(text)
    if n > 300:
        return 3
    if n > 100:
        return 2
    if n > 30:
        return 1
    return 0


def score_frontmatter(text: str) -> int:
    meta, _ = parse_frontmatter(text)
    has_title = bool(meta.get("title"))
    has_tags = bool(meta.get("tags"))
    has_date = bool(meta.get("date_ingested"))
    score = sum([has_title, has_tags, has_date])
    return score  # 0-3, but cap at 2


def score_sections(body: str) -> int:
    """Count ## headers (level 2 sections)."""
    count = len(re.findall(r"^##\s+\S", body, re.MULTILINE))
    if count >= 3:
        return 2
    if count >= 1:
        return 1
    return 0


def score_richness(text: str) -> int:
    """Check for code blocks, tables, and bullet lists."""
    _, body = parse_frontmatter(text)
    score = 0
    if re.search(r"```", body):
        score += 1
    if re.search(r"\|.*\|.*\|", body):
        score += 1
    if re.search(r"^- ", body, re.MULTILINE):
        score += 1
    return min(score, 2)  # cap at 2


def score_citations(text: str) -> int:
    """Check for external links, wiki links, or references."""
    _, body = parse_frontmatter(text)
    has_ext_links = bool(re.search(r"https?://", body))
    has_wiki_links = bool(re.search(r"\[\[", body))
    has_refs = bool(re.search(r"(?:อ้างอิง|references|sources|แหล่งที่มา)", body, re.IGNORECASE))
    return 1 if (has_ext_links or has_wiki_links or has_refs) else 0


def score_source(text: str) -> dict:
    """Score a source file against the rubric. Returns dict with scores."""
    meta, body = parse_frontmatter(text)
    scores = {
        "word_count": score_word_count(text),
        "frontmatter": score_frontmatter(text),
        "sections": score_sections(body),
        "richness": score_richness(text),
        "citations": score_citations(text),
    }
    total = sum(scores.values())
    total = min(total, 10)  # cap at 10
    if total <= 3:
        tier = "Low"
    elif total <= 6:
        tier = "Medium"
    else:
        tier = "High"
    title = meta.get("title", "")
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    return {
        "total": total,
        "tier": tier,
        "scores": scores,
        "title": title if isinstance(title, str) else str(title),
        "tags": [str(t) for t in tags] if isinstance(tags, list) else [str(tags)],
    }


def generate_synthesis(source_path: Path, score_result: dict) -> str:
    """Generate a synthesis stub for a high-quality source."""
    source_text = source_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(source_text)
    slug = source_path.stem
    title = meta.get("title", slug)
    source_rel = source_path.relative_to(REPO_ROOT)
    today = dt.date.today().isoformat()

    # Extract first 3 lines of body (after H1) as summary
    summary_lines: list[str] = []
    in_body = False
    for line in body.splitlines():
        s = line.strip()
        if not in_body and s.startswith("# "):
            in_body = True
            continue
        if not in_body:
            continue
        if not s:
            continue
        if s.startswith("##"):
            continue
        if s.startswith("```"):
            continue
        summary_lines.append(s)
        if len(summary_lines) >= 3:
            break
    summary = " ".join(summary_lines)[:200] if summary_lines else "(awaiting human summary)"

    # Extract key points from first few ## sections
    key_points: list[str] = []
    section_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = section_pattern.findall(body)
    for m in matches[:5]:
        key_points.append(f"- **{m.strip()}** — (extract from source)")

    domain = ""
    if meta.get("tags"):
        domain_keywords = ["iot", "ai", "pharmacy", "env"]
        for kw in domain_keywords:
            if any(kw in str(t) for t in (meta["tags"] if isinstance(meta["tags"], list) else [meta["tags"]])):
                domain = kw
                break

    synt_slug = f"synth-{slug}"

    lines = [
        "---",
        f"type: synthesis",
        f"title: \"{title} — Synthesis\"",
        f"slug: {synt_slug}",
        f"date_synthesized: {today}",
        f"sources: [{source_rel}]",
        f"quality_score: {score_result['total']}/10",
        f"domain: {domain}" if domain else "domain: ''",
        "---",
        "",
        f"# {title} — Synthesis",
        f"> Quality Score: {score_result['total']}/10 — {score_result['tier']}",
        "",
        "## Summary",
        summary,
        "",
        "## Key Points",
    ]
    if key_points:
        lines.extend(key_points)
    else:
        lines.append("_(Extract from source sections)_")
    lines.extend([
        "",
        "## Relevance",
        "_To be filled in by human review._",
        "",
    ])
    return "\n".join(lines)


def format_quality_table(results: dict[str, dict]) -> str:
    """Format scoring results as an ASCII table."""
    rows = sorted(results.items(), key=lambda x: x[1]["total"], reverse=True)
    header = "| Source | Score | Tier |"
    sep =    "|--------|-------|------|"
    lines: list[str] = []
    total_sum = 0
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for slug, r in rows:
        total_sum += r["total"]
        counts[r["tier"]] += 1
        title = (r["title"][:40] + "…") if len(r["title"]) > 40 else r["title"]
        lines.append(f"| {slug} | {r['total']:2d} | {r['tier']} |")
    avg = total_sum / len(rows) if rows else 0
    footer = f"\n| **Average**: {avg:.1f}/10 | | |"
    footer += f"\n| **High**: {counts['High']}  **Med**: {counts['Medium']}  **Low**: {counts['Low']} | | |"
    return "\n".join([header, sep] + lines + [footer])


def main() -> int:
    ap = argparse.ArgumentParser(description="Score sources and generate synthesis stubs")
    ap.add_argument("--source", type=str, help="Process a single source slug only")
    ap.add_argument("--dry-run", action="store_true", help="Scores only, no synthesis writes")
    ap.add_argument("--json", action="store_true", help="Output as JSON instead of table")
    args = ap.parse_args()

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)

    # Collect source files
    if args.source:
        source_path = SOURCES_DIR / f"{args.source}.md"
        if not source_path.exists():
            print(f"❌ Source not found: {args.source}", file=sys.stderr)
            return 1
        source_files = [source_path]
    else:
        source_files = sorted(SOURCES_DIR.glob("*.md"))

    results: dict[str, dict] = {}
    created = 0
    skipped = 0

    for sp in source_files:
        if sp.name == "CLAUDE.md":
            continue
        slug = sp.stem

        try:
            text = sp.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠  Cannot read {sp.name}: {e}", file=sys.stderr)
            skipped += 1
            continue

        score_result = score_source(text)
        results[slug] = score_result

        # Generate synthesis for High + Medium (score >= 5), unless dry-run or single-source
        if score_result["total"] >= 5 and not args.dry_run and not args.source:
            synt_path = SYNTHESIS_DIR / f"synth-{slug}.md"
            if synt_path.exists():
                skipped += 1
                continue
            content = generate_synthesis(sp, score_result)
            synt_path.write_text(content, encoding="utf-8")
            print(f"  ✓ Synthesis: wiki/synthesis/synth-{slug}.md (score={score_result['total']})")
            created += 1

    # Output
    if args.json:
        output = {
            "generated_at": dt.datetime.now().isoformat(),
            "total": len(results),
            "average": sum(r["total"] for r in results.values()) / len(results) if results else 0,
            "sources": {
                slug: {
                    "total": r["total"],
                    "tier": r["tier"],
                    "scores": r["scores"],
                }
                for slug, r in results.items()
            },
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("\n  Quality Report — wiki/sources/")
        print(format_quality_table(results))

    if args.source and not args.dry_run:
        slug = args.source
        r = results.get(slug)
        if r:
            print(f"\n  {slug}: score={r['total']}/10, tier={r['tier']}")
            print(f"  Breakdown: {r['scores']}")

    if not args.dry_run and not args.source:
        print(f"\n  Summary: {len(results)} sources scored, {created} syntheses created, {skipped} skipped/existing")

    return 0


if __name__ == "__main__":
    sys.exit(main())