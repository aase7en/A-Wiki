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
import hashlib
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

# Import shared domain constants from lib (F8 dedup — was inline tuple/dict)
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.wiki_domains import VALID_DOMAINS, DOMAIN_TITLES  # noqa: E402

# File extensions handled directly by read_text
PLAIN_TEXT_EXTS = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".xml", ".ini", ".cfg", ".conf", ".log", ".tsv"}
# Binary/office formats convertible via MarkItDown
BINARY_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".epub", ".html", ".htm"}


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

    Priority:
    1. curl-impersonate binary (TLS fingerprint: chrome) — bypasses Cloudflare/Akamai
    2. curl -sL (existing fallback)

    On 403/429: prints suggestion to use scrape-advanced.py.
    Returns plain-text content or None.
    """
    import subprocess

    # Try curl-impersonate binary first
    for bin_name in ("curl-impersonate-chrome", "curl-impersonate"):
        bin_path = shutil.which(bin_name)
        if bin_path:
            try:
                result = subprocess.run(
                    [bin_path, "-sL", "--max-time", "15", url],
                    capture_output=True, text=True, timeout=20,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
                if "403" in result.stderr or "429" in result.stderr:
                    print(
                        f"hint: target may be blocking — try: python3 scripts/wiki/scrape-advanced.py --url {url}",
                        file=sys.stderr,
                    )
                    return None
            except Exception:
                continue

    # Fallback to curl -sL
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass

    print(
        f"hint: both curl methods failed — try: python3 scripts/wiki/scrape-advanced.py --url {url}",
        file=sys.stderr,
    )
    return None


class BinaryUnavailableError(RuntimeError):
    """WO-AWIKI-TITLE-06 (Jev refuse_hard 0.68): a binary/office file could
    not be converted (MarkItDown absent or conversion failed). Raised BEFORE
    any filesystem write so mojibake never enters the wiki or raw/."""


def prettify_stem(stem: str) -> str:
    """WO-AWIKI-TITLE-06 (Jev filename_stem 1.00): title fallback for
    non-converted fallback text — separators to spaces, title case."""
    return re.sub(r"[-_]+", " ", stem).strip().title()


def extract_text_from_file(path: str, slug: str | None = None, write_raw: bool = True) -> tuple[str | None, bool]:
    """Read a local file. Handles .md, .txt, .json + binary/office via MarkItDown.

    For binary/office formats (.pdf, .docx, .xlsx, .pptx, .epub, .html):
    converts to Markdown via MarkItDown and saves to ``raw/<slug>.md``
    so the provenance hook passes.

    Returns ``(text, title_safe)``. ``title_safe`` is False only when the
    text came from the unknown-extension fallback read — callers must use
    the filename stem as title, never infer from that content. Binary
    conversion failures raise :class:`BinaryUnavailableError` (Jev
    refuse_hard 0.68 — garbage bodies must not enter the wiki).
    """
    p = Path(path)
    if not p.exists():
        return None

    ext = p.suffix.lower()

    # Plain text formats — direct read
    if ext in PLAIN_TEXT_EXTS:
        try:
            return p.read_text(encoding="utf-8"), True
        except Exception:
            return None, True

    # Binary/office formats — use MarkItDown
    if ext in BINARY_EXTS:
        try:
            from markitdown import MarkItDown  # type: ignore[import-untyped]
        except ImportError as e:
            # WO-AWIKI-TITLE-06 (Jev refuse_hard 0.68): refuse BEFORE any
            # write — the fallback read would be mojibake garbage.
            raise BinaryUnavailableError(
                f"MarkItDown not installed — install: pip install markitdown "
                f"(refusing binary ingest of {path})") from e
        try:
            md = MarkItDown()
            result = md.convert(str(p))
            if result and result.text_content:
                text = result.text_content
                if slug and write_raw:
                    # R82-1: dry-run must never write raw provenance — main()
                    # passes write_raw=False under --dry-run.
                    raw_path = REPO_ROOT / "raw" / f"{slug}.md"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_text(text, encoding="utf-8")
                    print(f"📝 MarkItDown → {raw_path}", file=sys.stderr)
                return text, True
            # converter produced nothing — same garbage risk as failure
            raise BinaryUnavailableError(
                f"MarkItDown produced no content for {path} "
                f"(refusing binary ingest)")
        except BinaryUnavailableError:
            raise
        except Exception as e:
            raise BinaryUnavailableError(
                f"MarkItDown conversion failed for {path}: {e} "
                f"(refusing binary ingest)") from e

    # Fallback: unknown extension — readable text, but NOT title-safe
    # (WO-AWIKI-TITLE-06, Jev filename_stem 1.00: caller titles from stem).
    try:
        return p.read_text(encoding="utf-8", errors="replace"), False
    except Exception:
        return None, False


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


def _content_hash(text: str) -> str:
    """SHA-256 of raw source content (WO-AWIKI-INGEST-03 dedup key)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _note_declares_hash(path: Path, digest: str) -> bool:
    """True when path's YAML frontmatter declares exactly this content_sha256.

    R82-3: match only a real frontmatter line between the --- delimiters, with
    the exact value — never body text, prefixes, or suffixed values.
    R82-4: read to the closing delimiter, not a fixed 2000-char cutoff, so
    hashes emitted after long metadata are still seen. Whole-file read is
    accepted (sources are small Markdown notes); file symlinks are followed,
    directory symlinks are not enumerated by rglob.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return False
    needle = f"content_sha256: {digest}"
    matched = False
    closed = False
    for line in lines[1:]:
        if not line[:1].isspace() and line.rstrip() == "---":
            closed = True  # closing delimiter — accept only if matched before it
            break
        # top-level keys only: an indented needle inside a YAML block scalar
        # (e.g. under description: |) must never match (Terra re-review N1/N2).
        if not line[:1].isspace() and line.rstrip() == needle:
            matched = True
    return matched and closed


def _find_hash_duplicate(digest: str, sources_dir) -> Path | None:
    """Return an existing note whose frontmatter declares the same hash.

    Notes written before this feature carry no content_sha256 line and
    therefore never match (grandfather).
    """
    if not sources_dir.is_dir():
        return None
    for path in sorted(sources_dir.rglob("*.md")):
        if _note_declares_hash(path, digest):
            return path
    return None


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
    original_file: str | None = None,
    content_sha256: str | None = None,
    source_url: str | None = None,
    duplicate_of: str | None = None,
) -> str:
    """Generate the full source markdown file content with YAML frontmatter."""
    today = dt.date.today().isoformat()
    concepts = key_concepts or []
    links = related_links or []
    slug = slugify(title)

    extra = {}
    if content_sha256:
        extra["content_sha256"] = content_sha256
    if source_url:
        extra["source_url"] = source_url
    if duplicate_of:
        extra["duplicate_of"] = duplicate_of
    front = frontmatter(
        type="source",
        title=title,
        slug=slug,
        date_ingested=today,
        original_file=original_file or "",
        tags=tags,
        quality=quality,
        **extra,
    )

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
    return front + "\n" + body


def ingest_source(
    title: str | None,
    domain: str,
    source_type: str,
    ref: str,
    tags: list[str],
    raw_text: str | None,
    quality: str = "seed",
    original_file: str | None = None,
    dry_run: bool = False,
    allow_duplicate: bool = False,
) -> Path | None:
    """Ingest a source: generate file and write to disk.

    Duplicate content (same content_sha256 in any existing note) is refused
    with a pointer to the existing note unless allow_duplicate is set
    (Jev 2026-11-12: state did not settle cross-domain policy 0.41/0.37,
    noul 0.48 — code takes the fail-safe branch). dry_run performs every
    check but writes nothing.
    """
    if domain not in VALID_DOMAINS:
        print(f"error: invalid domain '{domain}'. Valid: {', '.join(VALID_DOMAINS)}", file=sys.stderr)
        return None

    if not raw_text:
        print("error: no content to ingest", file=sys.stderr)
        return None

    digest = _content_hash(raw_text)
    duplicate = _find_hash_duplicate(digest, SOURCES_DIR)
    if duplicate is not None and not allow_duplicate:
        print(
            f"warn: duplicate content (sha256 {digest[:12]}...) already ingested at "
            f"{duplicate} — pass --allow-duplicate to file it anyway",
            file=sys.stderr,
        )
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
        original_file=original_file,
        content_sha256=digest,
        source_url=ref if ref.startswith("http") else None,
        duplicate_of=(
            duplicate.relative_to(SOURCES_DIR).as_posix()
            if (duplicate is not None and allow_duplicate)
            else None
        ),  # R82-2: portable repo-relative pointer, never machine-absolute
    )

    out_dir = SOURCES_DIR / domain
    out_path = out_dir / f"{slug}.md"

    # Avoid overwriting existing sources unless forced
    if out_path.exists():
        print(f"warn: {out_path} already exists — add a 'title' arg or move it manually", file=sys.stderr)
        return None

    if dry_run:
        # R82-1: dry-run creates nothing — no mkdir, no write.
        print(f"[dry-run] would create source: {out_path}")
        return out_path

    out_dir.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",
                        help="Run all checks (fetch, dedup, naming) but write nothing")
    parser.add_argument("--allow-duplicate", dest="allow_duplicate", action="store_true",
                        help="File the note even when content_sha256 matches an existing note "
                             "(the new note records duplicate_of)")
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
    original_file: str | None = None
    if args.url:
        print(f"🌐 Fetching: {args.url}...", file=sys.stderr)
        raw_text = extract_text_from_url(args.url)
        title_safe = True
        ref = args.url
        source_type = args.source_type or "article"
        if raw_text:
            # Save fetched content to raw/ for provenance
            url_slug = slugify(args.title) if args.title else slugify(ref.split("/")[-1].split("?")[0] or "web-page")
            raw_path = REPO_ROOT / "raw" / f"{url_slug}.md"
            if args.dry_run:
                print(f"[dry-run] would save raw content: {raw_path}", file=sys.stderr)
            else:
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(raw_text, encoding="utf-8")
                print(f"💾 Raw content saved: {raw_path}", file=sys.stderr)
            original_file = f"raw/{url_slug}.md"
    elif args.file:
        file_path = Path(args.file)
        file_slug = slugify(file_path.stem)
        print(f"📄 Reading: {args.file}...", file=sys.stderr)
        try:
            raw_text, title_safe = extract_text_from_file(
                args.file, slug=file_slug, write_raw=not args.dry_run)
        except BinaryUnavailableError as e:
            # WO-AWIKI-TITLE-06: refuse before any raw write or note
            # creation, dry-run included (the condition is real, not a
            # write-preview).
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        ref = str(file_path.resolve())
        source_type = args.source_type or "other"
        # Determine original_file: MarkItDown may have created raw/<slug>.md
        if raw_text:
            raw_md = REPO_ROOT / "raw" / f"{file_slug}.md"
            if raw_md.exists():
                original_file = f"raw/{file_slug}.md"
            else:
                # Binary copy to raw/ for non-MarkItDown files
                raw_dest = REPO_ROOT / "raw" / f"{file_slug}{file_path.suffix}"
                if args.dry_run:
                    print(f"[dry-run] would save raw copy: {raw_dest}", file=sys.stderr)
                else:
                    raw_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, raw_dest)
                    print(f"💾 Raw copy saved: {raw_dest}", file=sys.stderr)
                original_file = f"raw/{file_slug}{file_path.suffix}"

    if not raw_text:
        print("error: could not fetch/read content", file=sys.stderr)
        sys.exit(1)

    # WO-AWIKI-TITLE-06: non-title-safe text titles from the filename stem
    effective_title = args.title
    if args.file and not title_safe and not effective_title:
        effective_title = prettify_stem(Path(args.file).stem)

    ingest_source(
        title=effective_title,
        domain=args.domain,
        source_type=source_type,
        ref=ref,
        tags=args.tags or [],
        raw_text=raw_text,
        quality=args.quality,
        original_file=original_file,
        dry_run=args.dry_run,
        allow_duplicate=args.allow_duplicate,
    )


if __name__ == "__main__":
    main()