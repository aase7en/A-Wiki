#!/usr/bin/env python3
"""
ingest-source.py — Ingest a source (URL or local file) and create a wiki source entry.

Usage:
    python3 scripts/ingest-source.py --url <url> --domain <domain> [--tags tag1,tag2]
    python3 scripts/ingest-source.py --file <path> --domain <domain> [--tags tag1,tag2]
    python3 scripts/ingest-source.py --list                               # list all sources
    python3 scripts/ingest-source.py --list --domain iot                   # filter by domain

Output: wiki/sources/<domain>/<slug>.md
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import textwrap
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"

# Domains we recognise
VALID_DOMAINS = ("iot", "env", "ai-tools", "pharmacy", "it", "general")

# File extensions handled directly by read_text
PLAIN_TEXT_EXTS = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".xml", ".ini", ".cfg", ".conf", ".log", ".tsv"}
# Binary/office formats convertible via MarkItDown
BINARY_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".epub", ".html", ".htm"}

DOMAIN_TITLES = {
    "iot": "IoT",
    "env": "Environmental Health",
    "ai-tools": "AI Tools",
    "pharmacy": "Pharmacy",
    "it": "IT",
    "general": "General",
}


def slugify(text: str) -> str:
    """Convert text to a safe filesystem slug."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def frontmatter(**kwargs) -> str:
    """Generate YAML-ish frontmatter for a source file."""
    lines = ["---"]
    for k, v in kwargs.items():
        if isinstance(v, list):
            items = ", ".join(f'"{x}"' for x in v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def extract_text_from_url(url: str) -> str | None:
    """Try to fetch and extract text from a URL.

    Uses curl as a lightweight fallback. Returns plain-text content or None.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass
    return None


def extract_text_from_file(path: str) -> str | None:
    """Read a local file. Handles .md, .txt, .json."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def infer_title_from_content(text: str) -> str:
    """Try to extract a reasonable title from the content."""
    # First line that looks like an H1 or bold title
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            return m.group(1).strip()
        m = re.match(r"^\*\*(.+?)\*\*$", line)
        if m:
            return m.group(1).strip()
    # First meaningful line
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!", "-", "*", ">", "|", "`")):
            return line[:80]
    return "Untitled Source"


def generate_abstract(text: str, max_len: int = 200) -> str:
    """Generate a one-paragraph abstract from content."""
    # Strip code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    # Strip markdown headers, links, bold, etc.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#*>_~]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_len:
        return text

    # Try to break at sentence boundary
    cut = text.rfind(". ", 0, max_len)
    if cut > max_len // 2:
        return text[: cut + 1]
    # Fallback: word boundary
    cut = text.rfind(" ", 0, max_len)
    if cut > 0:
        return text[:cut] + "…"
    return text[:max_len] + "…"


def extract_key_concepts(text: str, max_concepts: int = 8) -> list[str]:
    """Extract likely key concepts from content using simple heuristics.

    Picks capitalized multi-word phrases that appear multiple times.
    """
    # Clean code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Find repeated capitalized phrases (2-4 words)
    phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text)
    freq: dict[str, int] = {}
    for p in phrases:
        freq[p] = freq.get(p, 0) + 1
    # Filter by frequency >= 2, sort by freq desc
    ranked = sorted(
        [(k, v) for k, v in freq.items() if v >= 2],
        key=lambda x: -x[1],
    )
    return [p for p, _ in ranked[:max_concepts]]


def extract_links(text: str, source_url: str | None = None) -> list[str]:
    """Extract URLs from markdown links and bare URLs."""
    links: list[str] = []
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        url = m.group(2).strip()
        if url.startswith("http"):
            links.append(url)
    for m in re.finditer(r"(https?://[^\s)<\"']+)", text):
        url = m.group(1).rstrip(".,;:)!?")
        if url not in links:
            links.append(url)
    return links


def create_source_entry(
    title: str,
    domain: str,
    source_type: str,
    abstract: str,
    ref: str,
    tags: list[str],
    key_concepts: list[str] | None = None,
    related_links: list[str] | None = None,
    quality: str = "seed",
) -> str:
    """Generate the full source markdown file content."""
    today = dt.date.today().isoformat()
    concepts = key_concepts or []
    links = related_links or []

    body = f"""# {title}

> **Type:** {source_type}
> **Domain:** {DOMAIN_TITLES.get(domain, domain)}
> **Ref:** {ref}
> **Ingested:** {today}
> **Quality:** {quality}
> **Tags:** {', '.join(tags) if tags else '(none)'}

## Abstract

{abstract}

## Key Concepts

"""
    if concepts:
        for c in concepts:
            body += f"- **{c}**\n"
    else:
        body += "_(auto-extract failed — review manually)_\n"

    if links:
        body += "\n## Related Links\n\n"
        for link in links:
            body += f"- {link}\n"

    body += textwrap.dedent("""\

    ---
    *Auto-created by `scripts/ingest-source.py` — review abstract and concepts for accuracy.*
    """)
    return body


def ingest_source(
    title: str | None,
    domain: str,
    source_type: str,
    ref: str,
    tags: list[str],
    raw_text: str | None,
    quality: str = "seed",
) -> Path | None:
    """Ingest a source: generate file and write to disk."""
    if domain not in VALID_DOMAINS:
        print(f"error: invalid domain '{domain}'. Valid: {', '.join(VALID_DOMAINS)}", file=sys.stderr)
        return None

    if not raw_text:
        print("error: no content to ingest", file=sys.stderr)
        return None

    actual_title = title or infer_title_from_content(raw_text)
    slug = slugify(actual_title)
    abstract = generate_abstract(raw_text)
    concepts = extract_key_concepts(raw_text)
    links = extract_links(raw_text, ref)

    content = create_source_entry(
        title=actual_title,
        domain=domain,
        source_type=source_type,
        abstract=abstract,
        ref=ref,
        tags=tags,
        key_concepts=concepts,
        related_links=links,
        quality=quality,
    )

    # Ensure directory exists
    out_dir = SOURCES_DIR / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"

    # Avoid overwriting existing sources unless forced
    if out_path.exists():
        print(f"warn: {out_path} already exists — add a 'title' arg or move it manually", file=sys.stderr)
        return None

    out_path.write_text(content, encoding="utf-8")
    print(f"✅ Created source: {out_path}")
    return out_path


def list_sources(domain: str | None = None) -> None:
    """List all ingested sources with metadata."""
    if not SOURCES_DIR.is_dir():
        print("No sources directory found.")
        return

    domains = [domain] if domain else sorted(
        d.name for d in SOURCES_DIR.iterdir() if d.is_dir() and d.name in VALID_DOMAINS
    )

    total = 0
    for dom in domains:
        dom_dir = SOURCES_DIR / dom
        if not dom_dir.is_dir():
            continue
        files = sorted(dom_dir.glob("*.md"))
        if not files:
            continue
        print(f"\n--- {DOMAIN_TITLES.get(dom, dom)} ---")
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
                title = "?"
                abstract = ""
                quality = ""
                tags = ""
                ingested = ""
                for line in text.splitlines():
                    m = re.match(r"^#\s+(.+)$", line)
                    if m:
                        title = m.group(1).strip()
                    m = re.match(r"^>\s*\*\*Quality:\*\*\s*(.+)$", line)
                    if m:
                        quality = m.group(1).strip()
                    m = re.match(r"^>\s*\*\*Tags:\*\*\s*(.+)$", line)
                    if m:
                        tags_val = m.group(1).strip()
                        if tags_val != "(none)":
                            tags = tags_val
                    m = re.match(r"^>\s*\*\*Ingested:\*\*\s*(.+)$", line)
                    if m:
                        ingested = m.group(1).strip()
                abs_match = re.search(r"## Abstract\n\n(.+?)(?:\n\n|\n##|\Z)", text, re.DOTALL)
                if abs_match:
                    abstract = abs_match.group(1).strip().replace("\n", " ")[:80]
                print(f"  {f.stem:35s} | {title:40s} | {quality:8s} | {ingested}")
                total += 1
            except Exception as e:
                print(f"  {f.stem:35s} | ERROR: {e}")

    print(f"\nTotal sources: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a source into the wiki")
    parser.add_argument("--url", help="Source URL to ingest")
    parser.add_argument("--file", help="Local file path to ingest")
    parser.add_argument("--title", help="Override title for the source entry")
    parser.add_argument(
        "--domain", choices=VALID_DOMAINS, default="general",
        help="Knowledge domain (default: general)",
    )
    parser.add_argument(
        "--type", dest="source_type", default="article",
        choices=["article", "documentation", "paper", "video", "tutorial", "reference", "other"],
        help="Type of source (default: article)",
    )
    parser.add_argument(
        "--tags", type=lambda s: [t.strip() for t in s.split(",") if t.strip()],
        default=[],
        help="Comma-separated tags",
    )
    parser.add_argument(
        "--quality", choices=["seed", "draft", "reviewed", "curated"], default="seed",
        help="Quality level (default: seed)",
    )
    parser.add_argument("--list", action="store_true", help="List all ingested sources")
    parser.add_argument("--list-domain", dest="list_domain", help="List sources by domain")

    args = parser.parse_args()

    if args.list or args.list_domain:
        list_sources(args.list_domain)
        return

    if not args.url and not args.file:
        parser.print_help()
        sys.exit(1)

    # Fetch content
    if args.url:
        print(f"🌐 Fetching: {args.url}...", file=sys.stderr)
        raw_text = extract_text_from_url(args.url)
        ref = args.url
        source_type = args.source_type or "article"
    elif args.file:
        print(f"📄 Reading: {args.file}...", file=sys.stderr)
        raw_text = extract_text_from_file(args.file)
        ref = str(Path(args.file).resolve())
        source_type = args.source_type or "other"

    if not raw_text:
        print("error: could not fetch/read content", file=sys.stderr)
        sys.exit(1)

    ingest_source(
        title=args.title,
        domain=args.domain,
        source_type=source_type,
        ref=ref,
        tags=args.tags or [],
        raw_text=raw_text,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()