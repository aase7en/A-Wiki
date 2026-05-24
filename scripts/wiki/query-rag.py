#!/usr/bin/env python3
"""
query-rag.py — Hybrid search: combine FTS5 keyword + embedding similarity.

Two modes:
  1. --fts5-only   : pure FTS5 (same as search-wiki.py)
  2. --semantic    : hybrid FTS5 + local TF-IDF cosine similarity
  3. --provider openrouter : use API embeddings for semantic vector search

Usage:
    python3 scripts/wiki/query-rag.py "MQTT esp32"
    python3 scripts/wiki/query-rag.py "MQTT esp32" --semantic
    python3 scripts/wiki/query-rag.py "MQTT esp32" --provider openrouter
    python3 scripts/wiki/query-rag.py "temperature sensor" --limit 5 --json
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sqlite3
import shlex
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / ".wiki-index.db"
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
EMB_PATH = REPO_ROOT / ".wiki-embeddings.json"
BUILDER = REPO_ROOT / "scripts" / "build-wiki-index.py"
EMB_BUILDER = REPO_ROOT / "scripts" / "wiki" / "build-embeddings.py"

STOPWORDS = set("""
a an the and or but in on at to for of with by from as is it its are were
was be been being have has had do does did will would shall should may
might must can could about into over after before between through during
without within across among behind below beneath beside beyond down
inside near off outside top under upon along around
ที่ ใน ของ และ หรือ แต่ นี้ นั้น มี เป็น คือ ได้ ถูก กับ ไว้ ไป มา
ไม่ ได้ ไว้ ยัง อยู่ ที่  ซึ่ง อัน  โดย  จาก  แต่  หาก  เมื่อ
""".split())

TOKEN_RE = re.compile(r"[a-zA-Z\u0E00-\u0E7F]{2,}")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def ensure_db() -> None:
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(BUILDER)], check=True)


def ensure_embeddings(mode: str) -> dict:
    """Load or build embeddings. Returns parsed .wiki-embeddings.json."""
    if not EMB_PATH.exists():
        print("Embeddings not found. Building...", file=sys.stderr)
        args = [sys.executable, str(EMB_BUILDER)]
        if mode == "openrouter":
            args.append("--provider")
            args.append("openrouter")
        subprocess.run(args, check=True)
    data = json.loads(EMB_PATH.read_text(encoding="utf-8"))
    # If mode changed, rebuild
    if data.get("mode") != mode:
        print(f"Rebuilding embeddings ({mode} mode)...", file=sys.stderr)
        args = [sys.executable, str(EMB_BUILDER), "--rebuild"]
        if mode == "openrouter":
            args.append("--provider")
            args.append("openrouter")
        subprocess.run(args, check=True)
        data = json.loads(EMB_PATH.read_text(encoding="utf-8"))
    return data


# ── FTS5 (exact copy of logic from search-wiki.py) ────────────────────


def normalize_query(q: str) -> str:
    q = q.strip()
    if not q:
        return q
    if any(tok in q for tok in (":", " AND ", " OR ", " NEAR(", '"')):
        return q
    parts = shlex.split(q)
    return " ".join(parts)


def search_fts5(query: str, limit: int) -> list[tuple]:
    """Returns list of (path, title, snippet, score)."""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        sql = (
            "SELECT path, title, "
            "snippet(wiki, 3, '«', '»', '…', 16) AS snip, "
            "bm25(wiki) AS score "
            "FROM wiki WHERE wiki MATCH ? "
            "ORDER BY score LIMIT ?"
        )
        return conn.execute(sql, (query, limit)).fetchall()
    finally:
        conn.close()


# ── Local TF-IDF similarity ───────────────────────────────────────────


def tokenize(text: str) -> list[str]:
    text = FRONTMATTER_RE.sub("", text)
    text = CODE_FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def cosine_sim(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse dict vectors."""
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    return dot


def query_local_embeddings(emb_data: dict, query: str, limit: int, alpha: float = 0.7) -> list[tuple]:
    """Hybrid search: weight FTS5 * alpha + cosine * (1-alpha).

    Returns list of (path, title, snippet, combined_score, fts5_score, cosine_score).
    """
    # Get FTS5 results first
    q_normal = normalize_query(query)
    try:
        fts5_results = search_fts5(q_normal, limit * 3)  # overfetch for hybrid mix
    except sqlite3.OperationalError:
        fts5_results = []

    # Build query TF-IDF vector
    num_docs = emb_data["params"]["N"]
    idf = emb_data.get("idf", {})
    query_tokens = Counter(tokenize(query))
    q_vec: dict[str, float] = {}
    for term, tf in query_tokens.items():
        q_vec[term] = (1 + math.log(tf)) * idf.get(term, math.log((num_docs + 1) / 1 + 1))
    q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
    if q_norm > 0:
        q_vec = {k: v / q_norm for k, v in q_vec.items()}

    # If query is empty (all stopwords), just return FTS5
    if not q_vec:
        results = []
        for i, (path, title, snip, score) in enumerate(fts5_results[:limit]):
            results.append((path, title, snip, score, score, 0.0))
        return results

    vectors = emb_data.get("vectors", {})
    scored: list[tuple[str, str, str, float, float, float]] = []

    # Build lookup from FTS5 results
    fts5_map: dict[str, tuple[str, str, float]] = {}
    fts5_scores: list[float] = []
    for path, title, snip, score in fts5_results:
        fts5_map[path] = (title, snip, score)
        fts5_scores.append(score)

    # Normalize FTS5 scores to [0,1]
    fts5_min = min(fts5_scores) if fts5_scores else 0
    fts5_max = max(fts5_scores) if fts5_scores else 1
    fts5_range = max(fts5_max - fts5_min, 1e-10)

    # Score all pages that have vectors
    for path, vec in vectors.items():
        if not vec:
            continue
        cosim = cosine_sim(q_vec, vec)
        if path in fts5_map:
            title, snip, raw_fts5 = fts5_map[path]
            fts5_norm = (raw_fts5 - fts5_min) / fts5_range
            combined = alpha * fts5_norm + (1 - alpha) * cosim
            scored.append((path, title, snip, combined, raw_fts5, cosim))
        elif cosim > 0.3:  # include semantically close even if FTS5 missed
            title = Path(path).stem.replace("-", " ").title()
            snip = f"[semantic match: similarity {cosim:.3f}]"
            combined = (1 - alpha) * cosim
            scored.append((path, title, snip, combined, 0.0, cosim))

    # Sort by combined score descending
    scored.sort(key=lambda x: -x[3])
    return scored[:limit]


# ── API embedding similarity ──────────────────────────────────────────


def _openrouter_embed(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    import urllib.request
    import urllib.error
    import os

    api_key = os.environ.get("OPENROUTER_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY or GEMINI_API_KEY not set. "
            "Use --semantic (local) mode instead."
        )

    url = "https://openrouter.ai/api/v1/embeddings"
    payload = json.dumps({
        "model": model,
        "input": texts,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    data["data"].sort(key=lambda x: x["index"])
    return [d["embedding"] for d in data["data"]]


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def query_api_embeddings(emb_data: dict, query: str, limit: int, alpha: float = 0.7) -> list[tuple]:
    """API-mode hybrid: embed the query, cosine vs all doc vectors."""
    # Get FTS5 results
    q_normal = normalize_query(query)
    try:
        fts5_results = search_fts5(q_normal, limit * 3)
    except sqlite3.OperationalError:
        fts5_results = []

    # Embed the query
    print(f"  embedding query...", file=sys.stderr)
    try:
        q_emb = _openrouter_embed([query])[0]
    except RuntimeError as e:
        print(f"  API error: {e}. Falling back to local TF-IDF.", file=sys.stderr)
        return query_local_embeddings(emb_data, query, limit, alpha)

    # Normalize query embedding
    q_norm = math.sqrt(sum(v * v for v in q_emb))
    if q_norm > 0:
        q_emb = [v / q_norm for v in q_emb]

    vectors = emb_data.get("vectors", {})
    scored: list[tuple[str, str, str, float, float, float]] = []

    fts5_map: dict[str, tuple[str, str, float]] = {}
    fts5_scores: list[float] = []
    for path, title, snip, score in fts5_results:
        fts5_map[path] = (title, snip, score)
        fts5_scores.append(score)

    fts5_min = min(fts5_scores) if fts5_scores else 0
    fts5_max = max(fts5_scores) if fts5_scores else 1
    fts5_range = max(fts5_max - fts5_min, 1e-10)

    for path, emb in vectors.items():
        if not emb:
            continue
        cosim = dot_product(q_emb, emb)
        if path in fts5_map:
            title, snip, raw_fts5 = fts5_map[path]
            fts5_norm = (raw_fts5 - fts5_min) / fts5_range
            combined = alpha * fts5_norm + (1 - alpha) * cosim
            scored.append((path, title, snip, combined, raw_fts5, cosim))
        elif cosim > 0.4:
            title = Path(path).stem.replace("-", " ").title()
            snip = f"[semantic match: similarity {cosim:.3f}]"
            combined = (1 - alpha) * cosim
            scored.append((path, title, snip, combined, 0.0, cosim))

    scored.sort(key=lambda x: -x[3])
    return scored[:limit]


# ── Main ───────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query", nargs="?", help="search query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--fts5-only", action="store_true", help="pure FTS5 only")
    p.add_argument("--semantic", action="store_true", help="hybrid FTS5 + local TF-IDF")
    p.add_argument("--provider", choices=("local", "openrouter"), help="embedding provider")
    p.add_argument("--alpha", type=float, default=0.7,
                   help="FTS5 weight (0-1) in hybrid search (default 0.7)")
    p.add_argument("--json", action="store_true", help="output JSON")
    args = p.parse_args()

    if not args.query:
        p.error("query required")

    q = normalize_query(args.query)
    mode = "openrouter" if args.provider == "openrouter" else "local"

    if args.fts5_only or not (args.semantic or args.provider):
        # Pure FTS5
        try:
            results = search_fts5(q, args.limit)
        except sqlite3.OperationalError as e:
            print(f"FTS5 query error: {e}", file=sys.stderr)
            return 2
    else:
        # Hybrid: load/build embeddings
        emb_data = ensure_embeddings(mode)
        if mode == "openrouter":
            results = query_api_embeddings(emb_data, args.query, args.limit, args.alpha)
        else:
            results = query_local_embeddings(emb_data, args.query, args.limit, args.alpha)

    if args.json:
        output = []
        for r in results:
            if len(r) == 4:
                path, title, snip, score = r
                output.append({"path": path, "title": title, "snippet": snip, "score": score})
            else:
                path, title, snip, combined, fts5, cosine = r
                output.append({
                    "path": path, "title": title, "snippet": snip,
                    "score": round(combined, 4),
                    "fts5_score": round(fts5, 4),
                    "cosine_score": round(cosine, 4),
                    "mode": "hybrid",
                })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("(no hits)")
            return 0
        for i, r in enumerate(results, 1):
            if len(r) == 4:
                path, title, snip, score = r
                snip_clean = " ".join(snip.split())
                print(f"{i}\t{path}\t{title}\t{snip_clean}")
            else:
                path, title, snip, combined, fts5, cosine = r
                snip_clean = " ".join(snip.split())
                label = f"H={combined:.3f} (FTS5={fts5:.2f}, Cos={cosine:.3f})"
                print(f"{i}\t{path}\t{title}\t{snip_clean}\t{label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())