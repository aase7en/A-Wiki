#!/usr/bin/env python3
"""
synthesize.py — Cross-domain synthesis generator for the A-Wiki knowledge graph.

Reads source entries from wiki/sources/ and generates synthesis documents that
connect concepts across domains, with explicit provenance back to source files.

Usage:
    python3 scripts/synthesize.py                                        # generate all syntheses
    python3 scripts/synthesize.py --domain iot                           # single domain syntheses
    python3 scripts/synthesize.py --cross "iot,env"                      # cross-domain syntheses
    python3 scripts/synthesize.py --list                                  # list existing syntheses
    python3 scripts/synthesize.py --rebuild                              # regenerate and overwrite
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
import textwrap
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
SYNTHESIS_DIR = REPO_ROOT / "wiki" / "synthesis"

# Domain metadata
DOMAIN_INFO: dict[str, dict[str, Any]] = {
    "iot": {"title": "IoT", "color": "#2563eb"},
    "env": {"title": "Environmental Health", "color": "#16a34a"},
    "ai-tools": {"title": "AI Tools", "color": "#9333ea"},
    "pharmacy": {"title": "Pharmacy", "color": "#dc2626"},
    "it": {"title": "IT", "color": "#ca8a04"},
    "general": {"title": "General", "color": "#6b7280"},
}

# Cross-domain bridge definitions: which domains connect naturally
CROSS_DOMAIN_BRIDGES: list[tuple[str, str, str, str]] = [
    # (domain_a, domain_b, topic, description)
    ("iot", "env", "Environmental IoT Sensing",
     "IoT sensors for air, water, and soil quality monitoring — combining LPWAN connectivity with environmental measurement."),
    ("iot", "it", "IoT Network Infrastructure",
     "Network protocols (MQTT, LoRaWAN) and edge computing architectures for reliable IoT deployments."),
    ("env", "ai-tools", "AI-driven Environmental Modeling",
     "Machine learning for air quality forecasting, water quality prediction, and soil moisture estimation."),
    ("pharmacy", "ai-tools", "AI for Drug Safety",
     "LLM and graph-based approaches to drug interaction prediction and clinical decision support."),
    ("iot", "ai-tools", "Intelligent IoT Pipelines",
     "Edge ML inference, RAG for sensor troubleshooting, and vector search over telemetry patterns."),
    ("it", "pharmacy", "Healthcare IT Infrastructure",
     "Network observability and edge computing applied to pharmacy information systems."),
    ("env", "pharmacy", "Environmental Pharmaceutical Risk",
     "Environmental monitoring of pharmaceutical contaminants (antibiotics, hormones) in water systems."),
    ("it", "env", "Environmental Monitoring IT",
     "Network architecture and data pipelines for large-scale environmental sensor networks."),
    ("iot", "pharmacy", "IoT in Pharmacy",
     "Connected medical dispensing, cold chain monitoring, and smart inventory management."),
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def load_parsed_sources() -> dict[str, list[dict[str, Any]]]:
    """Load all source entries from wiki/sources/, keyed by domain."""
    sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not SOURCES_DIR.is_dir():
        return dict(sources)

    for domain_dir in sorted(SOURCES_DIR.iterdir()):
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        for md_file in sorted(domain_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                parsed = parse_source(text, str(md_file.relative_to(REPO_ROOT)))
                if parsed:
                    sources[domain].append(parsed)
            except Exception as e:
                print(f"warn: cannot parse {md_file}: {e}", file=sys.stderr)
    return dict(sources)


def parse_source(text: str, rel_path: str) -> dict[str, Any] | None:
    """Parse a source .md file into structured data."""
    result: dict[str, Any] = {
        "path": rel_path,
        "title": "Untitled",
        "type": "unknown",
        "abstract": "",
        "concepts": [],
        "tags": [],
        "quality": "seed",
        "domain": "general",
    }

    # Title
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        result["title"] = m.group(1).strip()

    # Metadata from blockquote lines
    for line in text.splitlines():
        line_stripped = line.strip()
        kv = re.match(r">\s*\*\*(\w+):\*\*\s*(.+)", line_stripped)
        if kv:
            key = kv.group(1).lower()
            val = kv.group(2).strip()
            if key == "type":
                result["type"] = val
            elif key == "domain":
                result["domain"] = val
            elif key == "quality":
                result["quality"] = val
            elif key == "tags":
                result["tags"] = [t.strip() for t in val.split(",")]

    # Abstract
    abs_match = re.search(r"## Abstract\n\n(.+?)(?:\n\n|\n##|\Z)", text, re.DOTALL)
    if abs_match:
        result["abstract"] = abs_match.group(1).strip().replace("\n", " ")

    # Key Concepts
    concepts = []
    for cm in re.finditer(r"\*\*(.+?)\*\*\s*[—–-]\s*(.+?)(?=\n|$)", text):
        concepts.append({"name": cm.group(1).strip(), "description": cm.group(2).strip()})
    result["concepts"] = concepts

    return result


def find_bridge_sources(
    domain_a: str,
    domain_b: str,
    sources: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Find sources that bridge two domains — by tag overlap or concept match."""
    a_sources = sources.get(domain_a, [])
    b_sources = sources.get(domain_b, [])
    bridges: list[dict[str, Any]] = []

    # Cross-domain sources that reference both domains
    all_sources = list(a_sources) + [s for s in b_sources if s not in a_sources]
    for src in all_sources:
        tags = set(t.lower() for t in src.get("tags", []))
        # Tags that match concepts from the other domain
        other_concepts = {
            s["title"].lower().replace(" ", "-")
            for s in (b_sources if src in a_sources else a_sources)
        }
        if tags & other_concepts:
            bridges.append(src)

    # If no explicit bridges found, pick top sources from each domain
    if not bridges:
        bridges = a_sources[:3] + b_sources[:3]
    return bridges


def generate_domain_synthesis(
    domain: str,
    sources: list[dict[str, Any]],
) -> str | None:
    """Generate a synthesis document for a single domain."""
    if not sources:
        return None

    today = dt.date.today().isoformat()
    domain_title = DOMAIN_INFO.get(domain, {}).get("title", domain.title())

    # Aggregate concepts
    all_concepts: list[str] = []
    all_tags: set[str] = set()
    for src in sources:
        for c in src.get("concepts", []):
            all_concepts.append(c["name"])
        all_tags.update(src.get("tags", []))

    # Count concept frequency
    concept_freq = defaultdict(int)
    for c in all_concepts:
        concept_freq[c] += 1
    top_concepts = sorted(concept_freq.items(), key=lambda x: -x[1])[:10]

    body = f"""# {domain_title} — Knowledge Synthesis

> **Domain:** {domain}
> **Generated:** {today}
> **Sources:** {len(sources)}
> **Tags:** {', '.join(sorted(all_tags))}

## Overview

This synthesis aggregates {len(sources)} curated source entries in the **{domain_title}** domain.
It connects the key concepts across these sources to provide a unified understanding.

### Key Concepts (by frequency)

| Concept | Frequency |
|---------|-----------|
"""
    for concept, freq in top_concepts:
        body += f"| **{concept}** | {freq} |\n"

    body += f"""
## Source Inventory

| # | Title | Type | Quality | Concepts |
|---|-------|------|---------|----------|
"""
    for i, src in enumerate(sources, 1):
        concepts_str = ", ".join(c["name"] for c in src.get("concepts", [])[:3])
        if len(src.get("concepts", [])) > 3:
            concepts_str += " …"
        body += f"| {i} | [{src['title']}]({src['path']}) | {src['type']} | {src['quality']} | {concepts_str} |\n"

    body += f"""
## Cross-Connections

### Key Relationships

"""
    # Find concept pairs that appear together
    concept_pairs: list[tuple[str, str, int]] = []
    for src in sources:
        names = [c["name"] for c in src.get("concepts", [])]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if names[i] < names[j]:
                    concept_pairs.append((names[i], names[j], 1))
                else:
                    concept_pairs.append((names[j], names[i], 1))

    pair_freq: dict[tuple[str, str], int] = {}
    for a, b, _ in concept_pairs:
        key = (a, b)
        pair_freq[key] = pair_freq.get(key, 0) + 1

    top_pairs = sorted(pair_freq.items(), key=lambda x: -x[1])[:8]
    if top_pairs:
        body += "| Concept A | Concept B | Co-occurrence |\n|-----------|-----------|---------------|\n"
        for (a, b), freq in top_pairs:
            body += f"| {a} | {b} | {freq} sources |\n"
    else:
        body += "_Not enough sources for pair analysis._\n"

    body += f"""
## Research Directions

Based on concept gaps and source quality, consider:

"""
    # Suggest gaps: concepts that appear once
    single_concepts = [c for c, f in concept_freq.items() if f == 1]
    if single_concepts:
        body += f"- **Deepen**: Explore these underdeveloped concepts: {', '.join(single_concepts[:5])}\n"
    body += f"- **Expand**: Add sources tagged: {', '.join(sorted(all_tags)[:5])}\n"

    body += f"""
---
*Auto-generated by `scripts/synthesize.py` — review for accuracy before use.*
"""
    return body


def generate_cross_domain_synthesis(
    domain_a: str,
    domain_b: str,
    topic: str,
    description: str,
    sources: dict[str, list[dict[str, Any]]],
) -> str | None:
    """Generate a cross-domain synthesis between two domains."""
    a_sources = sources.get(domain_a, [])
    b_sources = sources.get(domain_b, [])
    if not a_sources or not b_sources:
        return None

    today = dt.date.today().isoformat()
    title_a = DOMAIN_INFO.get(domain_a, {}).get("title", domain_a)
    title_b = DOMAIN_INFO.get(domain_b, {}).get("title", domain_b)
    slug = slugify(f"{topic}")

    body = f"""# {topic}

> **Cross-domain synthesis:** {title_a} ⟷ {title_b}
> **Generated:** {today}
> **Sources:** {len(a_sources)} from {title_a}, {len(b_sources)} from {title_b}

## Synthesis

{description}

### Connections

| From ({title_a}) | ⟷ | From ({title_b}) |
|-----------------|---|------------------|
"""
    # Pair sources by concept similarity
    pairs_created = 0
    for a_src in a_sources[:4]:
        a_concepts = set(c["name"] for c in a_src.get("concepts", []))
        best_match = None
        best_score = 0
        for b_src in b_sources[:6]:
            b_concepts = set(c["name"] for c in b_src.get("concepts", []))
            overlap = len(a_concepts & b_concepts)
            if overlap > best_score:
                best_score = overlap
                best_match = b_src
        if best_match:
            overlap_concepts = a_concepts & set(c["name"] for c in best_match.get("concepts", []))
            overlap_str = ", ".join(overlap_concepts) if overlap_concepts else "*semantic bridge*"
            body += f"| [{a_src['title']}]({a_src['path']}) | {overlap_str} | [{best_match['title']}]({best_match['path']}) |\n"
            pairs_created += 1

    if pairs_created == 0:
        body += "| _(no direct concept overlap found — manually review)_ | | |\n"

    body += f"""
## Cross-Domain Concepts

### From {title_a}

"""
    for src in a_sources[:3]:
        concepts_str = ", ".join(c["name"] for c in src.get("concepts", [])[:4])
        body += f"- **{src['title']}**: {concepts_str}\n"

    body += f"""
### From {title_b}

"""
    for src in b_sources[:3]:
        concepts_str = ", ".join(c["name"] for c in src.get("concepts", [])[:4])
        body += f"- **{src['title']}**: {concepts_str}\n"

    body += f"""
---
*Auto-generated by `scripts/synthesize.py` — review for accuracy and update the description field.*
"""
    return body


def write_synthesis(path: Path, content: str, rebuild: bool = False) -> bool:
    """Write synthesis file, checking for overwrites."""
    if path.exists() and not rebuild:
        print(f"  ⏭  {path.relative_to(REPO_ROOT)} exists (use --rebuild to overwrite)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✅ {path.relative_to(REPO_ROOT)}")
    return True


def list_syntheses() -> None:
    """List existing synthesis documents."""
    if not SYNTHESIS_DIR.is_dir():
        print("No synthesis directory found.")
        return
    files = sorted(SYNTHESIS_DIR.glob("*.md"))
    if not files:
        print("No synthesis documents found.")
        return
    print(f"Found {len(files)} synthesis documents:\n")
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            title = "?"
            domain = ""
            sources_count = ""
            for line in text.splitlines():
                m = re.match(r"^#\s+(.+)$", line)
                if m:
                    title = m.group(1).strip()
                m = re.match(r"^>\s*\*\*Domain:\*\*\s*(.+)$", line)
                if m:
                    domain = m.group(1).strip()
                m = re.match(r"^>\s*\*\*Sources:\*\*\s*(.+)$", line)
                if m:
                    sources_count = f" [{m.group(1).strip()}]"
            print(f"  {f.stem:40s} | {title:50s} | {domain:20s}{sources_count}")
        except Exception as e:
            print(f"  {f.stem:40s} | ERROR: {e}")


def generate_all_syntheses(domain: str | None, cross: str | None, rebuild: bool) -> None:
    """Main synthesis generation entry point."""
    sources = load_parsed_sources()
    total_domains = 0
    total_cross = 0

    if cross:
        # Cross-domain synthesis
        domains = [d.strip() for d in cross.split(",")]
        if len(domains) != 2:
            print("error: --cross requires exactly 2 comma-separated domains", file=sys.stderr)
            sys.exit(1)
        da, db = domains
        if da not in sources or db not in sources:
            print(f"warn: one or both domains have no sources ({da}, {db})", file=sys.stderr)
            # Try to find a bridge definition
        topic = f"{DOMAIN_INFO.get(da, {}).get('title', da)} ⟷ {DOMAIN_INFO.get(db, {}).get('title', db)}"
        description = f"Cross-domain synthesis connecting {DOMAIN_INFO.get(da, {}).get('title', da)} and {DOMAIN_INFO.get(db, {}).get('title', db)}."
        for a, b, t, d in CROSS_DOMAIN_BRIDGES:
            if {a, b} == {da, db}:
                topic = t
                description = d
                break
        content = generate_cross_domain_synthesis(da, db, topic, description, sources)
        if content:
            slug = slugify(topic)
            path = SYNTHESIS_DIR / f"{slug}.md"
            if write_synthesis(path, content, rebuild):
                total_cross += 1
    elif domain:
        # Single domain synthesis
        if domain not in sources:
            print(f"warn: no sources found for domain '{domain}'", file=sys.stderr)
            return
        content = generate_domain_synthesis(domain, sources[domain])
        if content:
            path = SYNTHESIS_DIR / f"synthesis-{domain}.md"
            if write_synthesis(path, content, rebuild):
                total_domains += 1
    else:
        # Generate all domain syntheses + cross-domain syntheses
        for d in sorted(sources.keys()):
            content = generate_domain_synthesis(d, sources[d])
            if content:
                path = SYNTHESIS_DIR / f"synthesis-{d}.md"
                if write_synthesis(path, content, rebuild):
                    total_domains += 1

        # Cross-domain bridges
        for da, db, topic, description in CROSS_DOMAIN_BRIDGES:
            if da in sources and db in sources:
                content = generate_cross_domain_synthesis(da, db, topic, description, sources)
                if content:
                    slug = slugify(topic)
                    path = SYNTHESIS_DIR / f"{slug}.md"
                    if write_synthesis(path, content, rebuild):
                        total_cross += 1

    print(f"\nGenerated: {total_domains} domain syntheses + {total_cross} cross-domain syntheses")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cross-domain synthesis documents")
    parser.add_argument("--domain", help="Generate synthesis for a single domain")
    parser.add_argument("--cross", help="Generate cross-domain synthesis (comma-sep, e.g. 'iot,env')")
    parser.add_argument("--rebuild", action="store_true", help="Overwrite existing syntheses")
    parser.add_argument("--list", action="store_true", help="List existing syntheses")
    args = parser.parse_args()

    if args.list:
        list_syntheses()
        return

    generate_all_syntheses(args.domain, args.cross, args.rebuild)


if __name__ == "__main__":
    main()