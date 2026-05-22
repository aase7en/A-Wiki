#!/usr/bin/env python3
"""
search-wiki.py — Query the FTS5 wiki index built by build-wiki-index.py.

Usage:
    python3 scripts/search-wiki.py "MQTT esp32"
    python3 scripts/search-wiki.py "ขยะติดเชื้อ" --limit 5
    python3 scripts/search-wiki.py "supabase" --field title  # search title only
    python3 scripts/search-wiki.py --rebuild "query"          # rebuild then search

Output: one hit per line — `<rank>\t<path>\t<title>\t<snippet>`. Use this
instead of grep+read across many files to save Claude context tokens.
"""
from __future__ import annotations
import argparse
import shlex
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / ".wiki-index.db"
BUILDER = REPO_ROOT / "scripts" / "build-wiki-index.py"


def ensure_db() -> None:
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(BUILDER)], check=True)


def normalize_query(q: str) -> str:
    """FTS5-friendly query. Bare terms → match-anywhere; quoted phrases preserved."""
    q = q.strip()
    if not q:
        return q
    # If user wrote raw FTS5 (contains : or AND/OR/NEAR), pass through
    if any(tok in q for tok in (":", " AND ", " OR ", " NEAR(", '"')):
        return q
    parts = shlex.split(q)
    return " ".join(parts)


def search(query: str, limit: int, field: str | None) -> list[tuple]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        if field in ("title", "tags", "body"):
            fts_query = f"{field}:({query})"
        else:
            fts_query = query
        sql = (
            "SELECT path, title, "
            "snippet(wiki, 3, '«', '»', '…', 16) AS snip, "
            "bm25(wiki) AS score "
            "FROM wiki WHERE wiki MATCH ? "
            "ORDER BY score LIMIT ?"
        )
        return conn.execute(sql, (fts_query, limit)).fetchall()
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query", nargs="?", help="search query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--field", choices=("title", "tags", "body"))
    p.add_argument("--rebuild", action="store_true", help="rebuild index first")
    p.add_argument("--json", action="store_true", help="output JSON")
    args = p.parse_args()

    if args.rebuild:
        subprocess.run([sys.executable, str(BUILDER)], check=True)

    if not args.query:
        p.error("query required (unless only --rebuild)")

    q = normalize_query(args.query)
    try:
        results = search(q, args.limit, args.field)
    except sqlite3.OperationalError as e:
        print(f"FTS5 query error: {e}\nquery: {q}", file=sys.stderr)
        return 2

    if args.json:
        import json
        print(json.dumps([
            {"path": r[0], "title": r[1], "snippet": r[2], "score": r[3]}
            for r in results
        ], ensure_ascii=False, indent=2))
    else:
        if not results:
            print("(no hits)")
            return 0
        for i, (path, title, snip, score) in enumerate(results, 1):
            snip_clean = " ".join(snip.split())
            print(f"{i}\t{path}\t{title}\t{snip_clean}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
