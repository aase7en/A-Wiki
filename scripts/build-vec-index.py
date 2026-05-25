#!/usr/bin/env python3
"""
build-vec-index.py - Build sqlite-vec semantic index of wiki/*.md.

Adds two tables to .wiki-index.db (next to the FTS5 'wiki' table):
  wiki_vec        : sqlite-vec virtual table holding float[384] embeddings
  wiki_vec_meta   : rowid -> path mapping for joining back to file paths

Embeddings come from fastembed using paraphrase-multilingual-MiniLM-L12-v2
(384-dim, multilingual - covers Thai + English content). Model is downloaded
to the user-cache dir on first run (~120MB) then runs fully offline.

Usage:
    python scripts/build-vec-index.py             # full rebuild
    python scripts/build-vec-index.py --verify    # exit 1 if missing/stale

Companion: scripts/wiki/query-rag.py for hybrid (FTS5 + vec) querying.
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import struct
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*mean pooling.*", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
DB_PATH = REPO_ROOT / ".wiki-index.db"

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
MAX_DOC_CHARS = 4000  # ~1000 tokens, fits within model's 128-token limit per chunk
BATCH_SIZE = 32

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TAGS_LINE_RE = re.compile(r"^tags?:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def probe_or_die() -> None:
    """Verify sqlite-vec can load via apsw before doing anything expensive."""
    try:
        import apsw
        import sqlite_vec
    except ImportError as e:
        sys.exit(
            f"missing dependency: {e}\n"
            "run: pip install -r requirements.txt"
        )
    try:
        conn = apsw.Connection(":memory:")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        list(conn.execute("select vec_version()"))
    except Exception as e:
        sys.exit(
            f"sqlite-vec failed to load: {e}\n"
            "this typically means your Python build disables sqlite extension loading.\n"
            "the apsw package should bypass that - if you see this, file an issue\n"
            "with your platform (`python -c 'import platform; print(platform.platform())'`)."
        )


def extract_text(text: str, fallback_title: str) -> tuple[str, str]:
    """Return (title, body_for_embedding)."""
    body = text
    m = FRONTMATTER_RE.match(text)
    if m:
        body = text[m.end():]
    h1 = H1_RE.search(body)
    title = h1.group(1).strip() if h1 else fallback_title
    return title, body


def collect_docs() -> list[tuple[str, str]]:
    """Return list of (relative_path, embed_text) for every wiki .md file."""
    if not WIKI_DIR.is_dir():
        return []
    docs: list[tuple[str, str]] = []
    for fp in sorted(WIKI_DIR.rglob("*.md")):
        if not fp.is_file():
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            print(f"warn: skipping {fp.relative_to(REPO_ROOT)}: {e}", file=sys.stderr)
            continue
        rel = fp.relative_to(REPO_ROOT).as_posix()
        title, body = extract_text(text, fp.stem)
        snippet = (body or "").strip()[:MAX_DOC_CHARS]
        embed_text = f"{title}\n\n{snippet}"
        docs.append((rel, embed_text))
    return docs


def pack_vec(values) -> bytes:
    """Pack a float vector into the bytes format sqlite-vec's float[N] expects."""
    return struct.pack(f"{len(values)}f", *values)


def build(db_path: Path = DB_PATH) -> dict:
    import apsw
    import sqlite_vec
    from fastembed import TextEmbedding

    docs = collect_docs()
    if not docs:
        print("warn: no wiki markdown files found", file=sys.stderr)
        return {"files_scanned": 0, "rows_inserted": 0, "db": str(db_path)}

    print(f"loading model {EMBED_MODEL} ...", file=sys.stderr)
    model = TextEmbedding(model_name=EMBED_MODEL)

    print(f"embedding {len(docs)} documents ...", file=sys.stderr)
    texts = [d[1] for d in docs]
    embeddings = list(model.embed(texts, batch_size=BATCH_SIZE))

    if len(embeddings) != len(docs):
        sys.exit(f"embedding count mismatch: got {len(embeddings)} for {len(docs)} docs")
    if len(embeddings[0]) != EMBED_DIM:
        sys.exit(f"unexpected embedding dim: got {len(embeddings[0])}, expected {EMBED_DIM}")

    conn = apsw.Connection(str(db_path))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS wiki_vec")
    cur.execute("DROP TABLE IF EXISTS wiki_vec_meta")
    cur.execute(f"CREATE VIRTUAL TABLE wiki_vec USING vec0(embedding float[{EMBED_DIM}])")
    cur.execute(
        "CREATE TABLE wiki_vec_meta ("
        "rowid INTEGER PRIMARY KEY, "
        "path TEXT UNIQUE NOT NULL, "
        "updated TEXT NOT NULL)"
    )

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cur.execute("BEGIN")
    for i, ((rel, _), emb) in enumerate(zip(docs, embeddings), start=1):
        cur.execute(
            "INSERT INTO wiki_vec (rowid, embedding) VALUES (?, ?)",
            (i, pack_vec(emb)),
        )
        cur.execute(
            "INSERT INTO wiki_vec_meta (rowid, path, updated) VALUES (?, ?, ?)",
            (i, rel, now),
        )
    cur.execute("COMMIT")
    conn.close()

    return {"files_scanned": len(docs), "rows_inserted": len(docs), "db": str(db_path)}


def verify(db_path: Path = DB_PATH) -> int:
    import apsw
    import sqlite_vec

    if not db_path.exists():
        print(f"missing: {db_path}", file=sys.stderr)
        return 1
    conn = apsw.Connection(str(db_path))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    try:
        rows = list(conn.execute("SELECT COUNT(*) FROM wiki_vec_meta"))
        n_db = rows[0][0]
    except apsw.SQLError as e:
        print(f"missing wiki_vec table: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    n_fs = sum(1 for _ in WIKI_DIR.rglob("*.md") if _.is_file())
    if n_db != n_fs:
        print(f"stale: db={n_db} files={n_fs}", file=sys.stderr)
        return 1
    print(f"ok: {n_db} embeddings")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Build sqlite-vec semantic index.")
    p.add_argument("--verify", action="store_true", help="check freshness only")
    args = p.parse_args()
    probe_or_die()
    if args.verify:
        return verify()
    stats = build()
    print(
        f"built {stats['db']}: {stats['rows_inserted']} embeddings "
        f"from {stats['files_scanned']} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
