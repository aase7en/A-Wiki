#!/usr/bin/env python3
"""
raw-to-synth.py — Batch-generate synthesis page placeholders from un-synthesized sources.

Reads all wiki/sources/<slug>.md files that do NOT have a corresponding synthesis page,
and generates stub synthesis pages in wiki/synthesis/ with template structure.

A synthesis page is considered "exists" if there's a file in wiki/synthesis/ whose
frontmatter `sources` list includes this source's slug.

Usage:
    python3 scripts/wiki/raw-to-synth.py                             # generate remaining stubs
    python3 scripts/wiki/raw-to-synth.py --check                     # dry-run: show what would be created
    python3 scripts/wiki/raw-to-synth.py --domain iot                # filter by domain tag
    python3 scripts/wiki/raw-to-synth.py --overwrite                 # overwrite existing synthesis pages
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
SYNTHESIS_DIR = REPO_ROOT / "wiki" / "synthesis"
ENTITIES_DIR = REPO_ROOT / "wiki" / "entities"
CONCEPTS_DIR = REPO_ROOT / "wiki" / "concepts"

DOMAIN_TAG_MAP = {
    "iot": ["iot", "lora", "esp32", "sensor", "hardware", "wireless", "mqtt"],
    "env": ["env", "environmental", "wastewater", "air-quality", "health"],
    "ai-tools": ["ai", "llm", "agent", "claude", "openai", "machine-learning"],
    "pharmacy": ["pharmacy", "drug", "medicine", "healthcare"],
}


def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract frontmatter fields as a flat dict."""
    fm: dict[str, str] = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('-') and not line.startswith('  '):
                    key, _, val = line.partition(':')
                    fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def get_sources_in_synth() -> set[str]:
    """Return set of source slugs already referenced in synthesis pages."""
    covered: set[str] = set()
    if not SYNTHESIS_DIR.exists():
        return covered
    for synth_file in SYNTHESIS_DIR.glob('*.md'):
        try:
            content = synth_file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        fm = parse_frontmatter(content)
        sources_raw = fm.get('sources', '')
        if sources_raw:
            # Handle YAML list: [slug1, slug2]
            sources_raw = sources_raw.strip('[]')
            for s in sources_raw.split(','):
                s = s.strip().strip('"').strip("'")
                if s:
                    covered.add(s)
    return covered


def detect_domain(tags_str: str) -> str:
    """Detect domain from tags string."""
    tags_lower = tags_str.lower()
    for domain, keywords in DOMAIN_TAG_MAP.items():
        for kw in keywords:
            if kw in tags_lower:
                return domain
    return "cross-domain"


def build_synthesis_stub(source_slug: str, title: str, tags_str: str, synth_slug_hint: str = "") -> str:
    """Generate a synthesis page stub."""
    domain = detect_domain(tags_str)
    
    # Use provided slug hint, or fallback to source slug truncated
    slug = synth_slug_hint if synth_slug_hint else source_slug.replace('_', '-').strip('-')[:50]

    # Build frontmatter
    fm_lines = ['---']
    fm_lines.append(f'type: synthesis')
    fm_lines.append(f'tags: [{domain}]')
    fm_lines.append(f'sources: [{source_slug}]')
    fm_lines.append(f'created: 2026-05-24')
    fm_lines.append(f'updated: 2026-05-24')
    fm_lines.append('---')
    fm_lines.append('')
    fm_lines.append(f'# {title}')
    fm_lines.append('')
    fm_lines.append(f'> **คำถามที่ตอบ**: *(TODO)*')
    fm_lines.append('')
    fm_lines.append('## สรุป')
    fm_lines.append('')
    fm_lines.append('*(TODO)*')
    fm_lines.append('')
    fm_lines.append('## Data Flow / Architecture')
    fm_lines.append('')
    fm_lines.append('```')
    fm_lines.append('(TODO: diagram or flow)')
    fm_lines.append('```')
    fm_lines.append('')
    fm_lines.append('## Components')
    fm_lines.append('')
    fm_lines.append('| Component | Role | Source |')
    fm_lines.append('|-----------|------|--------|')
    fm_lines.append(f'| (TODO) | (TODO) | [[sources/{source_slug}]] |')
    fm_lines.append('')
    fm_lines.append('## Implementation Steps')
    fm_lines.append('')
    fm_lines.append('1. *(TODO)*')
    fm_lines.append('2. *(TODO)*')
    fm_lines.append('3. *(TODO)*')
    fm_lines.append('')
    fm_lines.append('## Cross-References')
    fm_lines.append('')
    fm_lines.append('- Source: [[sources/{source_slug}]]')
    fm_lines.append('- Entities: *(TODO)*')
    fm_lines.append('- Related synthesis: *(TODO)*')
    fm_lines.append('')
    
    return '\n'.join(fm_lines)


def has_ascii_alpha(s: str) -> bool:
    """Check if string contains at least 3 ASCII alphabetic characters."""
    count = sum(1 for c in s if 'a' <= c <= 'z')
    return count >= 3


def make_synthesis_slug(source_slug: str) -> str:
    """Generate synthesis slug from a source slug.
    
    Tries to reduce redundancy while keeping it readable.
    - If source slug has >2 parts, take first 2-3 meaningful segments
    - Strip common suffixes like '-guide', '-documentation', '-with-arduino-ide'
    - Fallback: hash the source slug if no ASCII alpha (e.g. Thai-only slugs)
    """
    # Clean the source slug
    slug = source_slug.lower().strip('-')
    
    # Fallback for non-ASCII (Thai-only) slugs
    if not has_ascii_alpha(slug):
        import hashlib
        h = hashlib.md5(slug.encode()).hexdigest()[:8]
        return f'synth-{h}'
    
    # Strip common trailing noise
    for suffix in ['-guide', '-documentation', '-with-arduino-ide', '-arduino-library',
                   '-esp-idf-programming-guide', '-v44-documentation', '-examples',
                   '-practices', '-introduction', '-tutorial', '-overview']:
        if slug.endswith(suffix):
            slug = slug[:-len(suffix)]
    
    parts = slug.split('-')
    if len(parts) > 4:
        # Take first 3 parts (likely the core subject)
        core = parts[:3]
        # Check if 4th part adds meaningful info (like 'lorawan', 'raspberry')
        meaningful = {'lorawan', 'raspberry', 'lora', 'esp32', 'esp8266', 'arduino',
                      'mqtt', 'node', 'dashboard', 'sensor', 'gateway'}
        for p in parts[3:]:
            if p in meaningful:
                core.append(p)
                break
        slug = '-'.join(core)
    
    # Final cleanup
    slug = slug.strip('-')[:60].rstrip('-')
    return slug if slug else "untitled-synthesis"


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate synthesis page stubs for uncovered sources')
    parser.add_argument('--check', action='store_true', help='Dry-run: show what would be created')
    parser.add_argument('--domain', choices=['iot', 'env', 'ai-tools', 'pharmacy', 'all'],
                        default='all', help='Filter by domain (default: all)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing synthesis pages')
    args = parser.parse_args()

    if not SOURCES_DIR.exists():
        print(f'❌ wiki/sources/ directory not found: {SOURCES_DIR}', file=sys.stderr)
        return 1

    SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)

    # Get sources already covered by synthesis pages
    covered_sources = get_sources_in_synth()
    
    created = 0
    skipped = 0
    errors = 0
    seen_slugs: set[str] = set()

    md_files = sorted(SOURCES_DIR.glob('*.md'))
    
    for source_path in md_files:
        if source_path.name == 'CLAUDE.md':
            continue
            
        try:
            content = source_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f'❌ Error reading {source_path.name}: {e}', file=sys.stderr)
            errors += 1
            continue

        fm = parse_frontmatter(content)
        source_slug = fm.get('slug', source_path.stem)
        title = fm.get('title', source_slug)
        tags = fm.get('tags', '')

        # Check if this source is already covered
        if source_slug in covered_sources and not args.overwrite:
            print(f'  ⏭️  {source_slug} — already covered by synthesis (--overwrite to force)')
            skipped += 1
            continue

        # Domain filter
        if args.domain != 'all':
            detected = detect_domain(tags)
            if detected != args.domain:
                skipped += 1
                continue

        # Build synthesis slug from the source slug directly (deterministic)
        synth_slug = make_synthesis_slug(source_slug)
        
        # Deduplicate synthesis slugs: append -2, -3, etc. for collisions
        base_slug = synth_slug
        counter = 2
        while synth_slug in seen_slugs:
            synth_slug = f'{base_slug}-{counter}'
            counter += 1
        seen_slugs.add(synth_slug)
        
        # Generate stub content with consistent slug
        page_content = build_synthesis_stub(source_slug, title, tags, synth_slug_hint=synth_slug)
        synth_path = SYNTHESIS_DIR / f'{synth_slug}.md'
        
        if args.check:
            print(f'  📄 {synth_slug}.md — would create from source {source_slug} ({title[:40]})')
            created += 1
            continue

        synth_path.write_text(page_content, encoding='utf-8')
        print(f'  ✅ {synth_slug}.md — created from {source_slug}')
        created += 1

    print(f'\n📊 Summary: {created} created, {skipped} skipped, {errors} errors')
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())