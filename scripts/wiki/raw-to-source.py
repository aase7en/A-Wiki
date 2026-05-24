#!/usr/bin/env python3
"""
raw-to-source.py — Convert raw/ markdown files into wiki/sources/ pages.

Reads every .md file in raw/ (symlinked to Google Drive), parses its frontmatter,
generates a deterministic slug from the title, and writes a wiki/sources/<slug>.md
file with:
  - Standardized source frontmatter (type: source, slug, date_ingested, original_file)
  - Preserved raw frontmatter (title, source URL, author, etc.)
  - Cleaned content (emoji image URLs stripped, HTML stripped)

Usage:
    python3 scripts/wiki/raw-to-source.py                    # convert all raw/ files
    python3 scripts/wiki/raw-to-source.py --check            # dry-run: show what would change
    python3 scripts/wiki/raw-to-source.py --force            # overwrite existing source pages

Output:
    - Creates/updates wiki/sources/<slug>.md for each raw file
    - Prints summary: X created, Y skipped, Z errors
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = REPO_ROOT / "raw"
SOURCE_DIR = REPO_ROOT / "wiki" / "sources"

# ─── Slug generation ────────────────────────────────────────────────────────────

def make_slug(title: str) -> str:
    """Generate a deterministic, URL-friendly slug from a title string.
    
    Falls back to a hash-based slug if the title has no ASCII characters.
    
    Rules:
    - Lowercase
    - Remove leading numbers/dots (e.g. "(10)" or "1." or "#1")
    - Replace whitespace with hyphens
    - Remove non-alphanumeric characters (except hyphens)
    - Collapse multiple hyphens into one
    - If result is empty, hash the title with a short prefix
    - Limit to 80 characters
    """
    original = title
    slug = title.lower()
    # Remove leading "(n)" or "#n" patterns
    slug = re.sub(r'^[\s#\(\)\d.]+', '', slug)
    # Replace whitespace with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Collapse multiple hyphens
    slug = re.sub(r'-{2,}', '-', slug)
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    slug = slug[:80].rstrip('-')
    
    # Fallback for non-ASCII titles (e.g. Thai)
    if not slug or len(slug) < 3:
        import hashlib
        h = hashlib.md5(original.encode()).hexdigest()[:8]
        slug = f"source-{h}"
    return slug


# ─── Frontmatter parsing ────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and body from a markdown file.
    
    Returns (frontmatter_dict, body_text). frontmatter_dict keys are lowercased.
    """
    fm: dict[str, str] = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_fm = parts[1]
            body = parts[2].strip()
            for line in raw_fm.strip().split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('-') and not line.startswith('  '):
                    key, _, val = line.partition(':')
                    key = key.strip().lower()
                    val = val.strip()
                    # Remove quotes
                    val = val.strip('"').strip("'")
                    # Parse list values (YAML inline arrays)
                    if val.startswith('[') and val.endswith(']'):
                        items = [
                            item.strip().strip('"').strip("'")
                            for item in val[1:-1].split(',')
                            if item.strip()
                        ]
                        fm[key] = ', '.join(items)
                    else:
                        fm[key] = val

    return fm, body


# ─── Content cleaning ───────────────────────────────────────────────────────────

def clean_body(body: str) -> str:
    """Remove emoji image URLs, HTML, and other noise from body text."""
    # Remove emoji image URLs: ![emoji](https://...)
    body = re.sub(r'!\[[^\]]*\]\(https?://[^\)]+\)', '', body)
    # Remove bare image URLs
    body = re.sub(r'https?://[^\s\)]+\.(?:png|jpg|jpeg|gif|svg|webp)[^\s\)]*', '', body)
    # Remove HTML tags
    body = re.sub(r'<[^>]+>', '', body)
    # Remove empty lines (keep one)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip()


# ─── Source page generator ──────────────────────────────────────────────────────

def build_source_page(fm: dict[str, str], body: str, filename: str) -> tuple[str, str]:
    """Generate source page content.
    
    Returns (slug, page_content).
    """
    title = fm.get('title', filename.replace('.md', '').replace('-', ' '))
    # Prefer explicit slug from raw frontmatter, but only if it has ASCII alpha (skip Thai-only slugs)
    explicit_slug = fm.get('slug', '').strip()
    has_ascii = sum(1 for c in explicit_slug if 'a' <= c <= 'z' or 'A' <= c <= 'Z') >= 2
    if explicit_slug and len(explicit_slug) > 3 and ' ' not in explicit_slug and has_ascii:
        slug = explicit_slug
    else:
        slug = make_slug(title)
    
    # Clean the body
    cleaned_body = clean_body(body)
    
    # Build wiki frontmatter (prefix keys to avoid conflict with raw frontmatter)
    lines = ['---']
    lines.append(f'type: source')
    lines.append(f'title: "{title}"')
    lines.append(f'slug: {slug}')
    lines.append(f'date_ingested: 2026-05-24')
    lines.append(f'original_file: raw/{filename}')
    lines.append('---')
    lines.append('')
    
    # Preserve raw frontmatter inside a yaml code block
    raw_keys = ['title', 'source', 'author', 'published', 'created', 'description', 'tags', 'type', 'slug', 'date_extracted', 'date_collected', 'collected_by', 'status']
    raw_lines = ['---']
    for key in raw_keys:
        if key in fm:
            val = fm[key]
            raw_lines.append(f'{key}: "{val}"')
    raw_lines.append('---')
    
    lines.append('```yaml')
    lines.extend(raw_lines)
    lines.append('```')
    lines.append('')
    
    # Add body
    if cleaned_body:
        lines.append(cleaned_body)
    else:
        lines.append('*(No content)*')
    
    lines.append('')
    return slug, '\n'.join(lines)


# ─── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description='Convert raw/ files to wiki/sources/ pages')
    parser.add_argument('--check', action='store_true', help='Dry-run: show what would change')
    parser.add_argument('--force', action='store_true', help='Overwrite existing source pages')
    args = parser.parse_args()

    if not RAW_DIR.exists():
        print(f'❌ raw/ directory not found: {RAW_DIR}', file=sys.stderr)
        return 1

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    errors = 0
    seen_slugs: set[str] = set()

    md_files = sorted(RAW_DIR.glob('*.md'))
    if not md_files:
        print('⚠️  No .md files found in raw/', file=sys.stderr)
        return 0

    for raw_path in md_files:
        filename = raw_path.name
        try:
            content = raw_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f'❌ Error reading {filename}: {e}', file=sys.stderr)
            errors += 1
            continue

        fm, body = parse_frontmatter(content)
        slug, page_content = build_source_page(fm, body, filename)

        # Deduplicate slugs: append -2, -3, etc. for collisions
        base_slug = slug
        counter = 2
        while slug in seen_slugs:
            slug = f'{base_slug}-{counter}'
            counter += 1
        seen_slugs.add(slug)

        source_path = SOURCE_DIR / f'{slug}.md'
        
        if source_path.exists() and not args.force:
            print(f'  ⏭️  {slug}.md — exists (--force to overwrite)')
            skipped += 1
            continue

        if args.check:
            print(f'  📄 {slug}.md — would create from {filename}')
            created += 1
            continue

        source_path.write_text(page_content, encoding='utf-8')
        print(f'  ✅ {slug}.md — created from {filename}')
        created += 1

    print(f'\n📊 Summary: {created} created, {skipped} skipped, {errors} errors')
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())