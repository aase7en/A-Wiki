#!/usr/bin/env python3
"""
build-wiki-index.py — Build SQLite FTS5 full-text index of wiki/*.md.

Creates .wiki-index.db at repo root with a single FTS5 virtual table 'wiki'
containing (path, title, tags, body) for every markdown file under wiki/.

Why FTS5: built-in to Python sqlite3 (zero install, zero ops). Wiki-wide
keyword search becomes O(log n) instead of O(files) grep.

Usage:
    python3 scripts/build-wiki-index.py             # rebuild full
    python3 scripts/build-wiki-index.py --verify    # exit 1 if missing/stale

Companion: scripts/search-wiki.py for querying.
"""
from __future__ import annotations
import argparse
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
DB_PATH = REPO_ROOT / ".wiki-index.db"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TAGS_LINE_RE = re.compile(r"^tags?:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def extract_meta(text: str, fallback_title: str) -> tuple[str, str, str]:
    """Return (title, tags, body). Strips frontmatter from body."""
    tags = ""
    body = text
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = m.group(1)
        body = text[m.end():]
        tm = TAGS_LINE_RE.search(fm)
        if tm:
            tags = tm.group(1).strip().strip("[]").replace(",", " ")
    # Title: first H1 in body, else frontmatter title, else filename
    h1 = H1_RE.search(body)
    title = h1.group(1).strip() if h1 else fallback_title
    return title, tags, body


def collect_files() -> list[Path]:
    if not WIKI_DIR.is_dir():
        return []
    return sorted(p for p in WIKI_DIR.rglob("*.md") if p.is_file())


def build(db_path: Path = DB_PATH) -> dict:
    files = collect_files()
    conn = sqlite3.connect(db_path)
    try:
        # Drop only the FTS5 'wiki' table — leave sibling tables (e.g. wiki_vec
        # from build-vec-index.py) intact so a partial rebuild doesn't wipe them.
        conn.execute("DROP TABLE IF EXISTS wiki")
        conn.execute(
            "CREATE VIRTUAL TABLE wiki USING fts5("
            "path UNINDEXED, title, tags, body, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        rows = 0
        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                print(f"warn: skipping {fp.relative_to(REPO_ROOT)}: {e}", file=sys.stderr)
                continue
            rel = fp.relative_to(REPO_ROOT).as_posix()
            title, tags, body = extract_meta(text, fp.stem)
            conn.execute(
                "INSERT INTO wiki (path, title, tags, body) VALUES (?, ?, ?, ?)",
                (rel, title, tags, body),
            )
            rows += 1
        conn.commit()
    finally:
        conn.close()
    return {"files_scanned": len(files), "rows_inserted": rows, "db": str(db_path)}


def verify(db_path: Path = DB_PATH) -> int:
    if not db_path.exists():
        print(f"missing: {db_path}", file=sys.stderr)
        return 1
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM wiki")
        n_db = cur.fetchone()[0]
    finally:
        conn.close()
    n_fs = len(collect_files())
    if n_db != n_fs:
        print(f"stale: db={n_db} files={n_fs}", file=sys.stderr)
        return 1
    print(f"ok: {n_db} rows")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true", help="check freshness only")
    args = p.parse_args()
    if args.verify:
        return verify()
    stats = build()
    print(f"built {stats['db']}: {stats['rows_inserted']} rows from {stats['files_scanned']} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
