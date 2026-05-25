#!/usr/bin/env python3
"""
query-rag.py - Hybrid keyword + semantic search over A-Wiki.

Joins two indexes inside .wiki-index.db:
  * FTS5 'wiki' table        (built by scripts/build-wiki-index.py)
  * sqlite-vec 'wiki_vec'    (built by scripts/build-vec-index.py)

Fusion: weighted RRF. score(d) = alpha/(k+rank_fts) + (1-alpha)/(k+rank_vec)
where k=60. alpha=1.0 -> pure FTS, alpha=0.0 -> pure semantic, default 0.5.

Usage:
    python scripts/wiki/query-rag.py "drug interaction"
    python scripts/wiki/query-rag.py "เซ็นเซอร์อากาศ" --limit 10 --json
    python scripts/wiki/query-rag.py "mqtt vs lorawan" --alpha 0.3   # lean semantic
"""
from __future__ import annotations
import argparse
import json
import re
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / ".wiki-index.db"
WIKI_DIR = REPO_ROOT / "wiki"

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
RRF_K = 60
FETCH_PER_SOURCE = 50  # rows pulled from each index before fusion


def log(msg: str) -> None:
    print(f"[rag] {msg}", file=sys.stderr)


def probe_or_die() -> None:
    try:
        import apsw
        import sqlite_vec
    except ImportError as e:
        sys.exit(f"missing dependency: {e}\nrun: pip install -r requirements.txt")
    try:
        conn = apsw.Connection(":memory:")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        list(conn.execute("select vec_version()"))
    except Exception as e:
        sys.exit(
            f"sqlite-vec failed to load: {e}\n"
            "platform: try `python -c 'import platform; print(platform.platform())'`\n"
            "and file an issue at https://github.com/asg017/sqlite-vec"
        )


def pack_vec(values) -> bytes:
    return struct.pack(f"{len(values)}f", *values)


def fts_escape(query: str) -> str:
    """Tokenize a free-text query into FTS5 MATCH syntax: each whitespace-separated
    word becomes a quoted prefix-match term, joined with OR. Resilient to FTS5
    operator chars in user input (which would otherwise raise OperationalError)."""
    tokens = [t for t in re.split(r"\s+", query.strip()) if t]
    if not tokens:
        return '""'
    quoted = [f'"{t.replace(chr(34), chr(34) * 2)}"' for t in tokens]
    return " OR ".join(quoted)


def _connect():
    import apsw
    import sqlite_vec
    if not DB_PATH.exists():
        sys.exit(f"missing index: {DB_PATH}\nrun: python scripts/build-wiki-index.py && python scripts/build-vec-index.py")
    conn = apsw.Connection(str(DB_PATH))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    return conn


def _embed_query(text: str) -> list[float]:
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name=EMBED_MODEL)
    return list(next(iter(model.embed([text]))))


def _read_snippet(path: str, query: str, ctx: int = 220) -> str:
    """Return ~ctx chars of body around first query-token match (best effort)."""
    fp = REPO_ROOT / path
    try:
        text = fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    token = re.split(r"\s+", query.strip())[0] if query.strip() else ""
    if token:
        m = re.search(re.escape(token), text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - ctx // 2)
            end = min(len(text), m.end() + ctx // 2)
            chunk = text[start:end]
            return " ".join(chunk.split())[:ctx]
    return " ".join(text.split())[:ctx]


def hybrid_search(query: str, limit: int, alpha: float) -> list[dict]:
    """Run FTS5 + sqlite-vec, fuse with weighted RRF, return ranked results."""
    conn = _connect()
    try:
        fts_rows: list[tuple[str, str, float]] = []
        try:
            rows = list(conn.execute(
                "SELECT path, title, bm25(wiki) AS score "
                "FROM wiki WHERE wiki MATCH ? "
                "ORDER BY score LIMIT ?",
                (fts_escape(query), FETCH_PER_SOURCE),
            ))
            fts_rows = [(r[0], r[1], r[2]) for r in rows]
        except Exception as e:
            log(f"FTS5 query skipped: {e}")

        q_emb = _embed_query(query)
        vec_rows: list[tuple[str, str, float]] = []
        try:
            rows = list(conn.execute(
                "SELECT m.path, COALESCE(w.title, '') AS title, v.distance "
                "FROM wiki_vec v "
                "JOIN wiki_vec_meta m ON m.rowid = v.rowid "
                "LEFT JOIN wiki w ON w.path = m.path "
                "WHERE v.embedding MATCH ? AND k = ? "
                "ORDER BY v.distance",
                (pack_vec(q_emb), FETCH_PER_SOURCE),
            ))
            vec_rows = [(r[0], r[1], r[2]) for r in rows]
        except Exception as e:
            log(f"vec query failed: {e}")
    finally:
        conn.close()

    fts_rank = {path: i for i, (path, _, _) in enumerate(fts_rows)}
    vec_rank = {path: i for i, (path, _, _) in enumerate(vec_rows)}
    title_map: dict[str, str] = {}
    for path, title, _ in fts_rows + vec_rows:
        if path not in title_map and title:
            title_map[path] = title

    fused: dict[str, float] = {}
    for path, i in fts_rank.items():
        fused[path] = fused.get(path, 0.0) + alpha / (RRF_K + i + 1)
    for path, i in vec_rank.items():
        fused[path] = fused.get(path, 0.0) + (1 - alpha) / (RRF_K + i + 1)

    ranked = sorted(fused.items(), key=lambda x: -x[1])[:limit]
    out = []
    for rank, (path, score) in enumerate(ranked, start=1):
        out.append({
            "rank": rank,
            "path": path,
            "title": title_map.get(path) or Path(path).stem,
            "snippet": _read_snippet(path, query),
            "score": round(score, 6),
            "fts_rank": fts_rank.get(path),
            "vec_rank": vec_rank.get(path),
        })
    return out


def format_results(results: list[dict]) -> str:
    if not results:
        return "no results"
    lines = []
    for r in results:
        bits = []
        if r["fts_rank"] is not None:
            bits.append(f"fts#{r['fts_rank'] + 1}")
        if r["vec_rank"] is not None:
            bits.append(f"vec#{r['vec_rank'] + 1}")
        tag = f" [{' '.join(bits)}]" if bits else ""
        lines.append(f"[{r['rank']}] {r['title']}{tag}")
        lines.append(f"    {r['path']}  score={r['score']:.4f}")
        if r["snippet"]:
            lines.append(f"    {r['snippet']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Hybrid FTS5 + sqlite-vec search over A-Wiki")
    p.add_argument("query", nargs="?", help="search query")
    p.add_argument("--limit", type=int, default=10, help="max results (default 10)")
    p.add_argument("--alpha", type=float, default=0.5,
                   help="weight on FTS rank vs vec rank, 0-1 (default 0.5)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--status", action="store_true", help="show index stats and exit")
    # back-compat no-ops so old callers (mcp-wiki-server) don't break
    p.add_argument("--semantic", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--provider", default=None, help=argparse.SUPPRESS)
    args = p.parse_args()

    probe_or_die()

    if args.status:
        conn = _connect()
        try:
            n_fts = list(conn.execute("SELECT COUNT(*) FROM wiki"))[0][0]
            n_vec = list(conn.execute("SELECT COUNT(*) FROM wiki_vec_meta"))[0][0]
        finally:
            conn.close()
        print(f"db:    {DB_PATH}")
        print(f"fts5:  {n_fts} rows")
        print(f"vec:   {n_vec} embeddings ({EMBED_MODEL}, {EMBED_DIM}-dim)")
        return 0

    if not args.query:
        p.error("query is required (or use --status)")

    if not 0.0 <= args.alpha <= 1.0:
        p.error("--alpha must be between 0.0 and 1.0")

    results = hybrid_search(args.query, args.limit, args.alpha)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_results(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
