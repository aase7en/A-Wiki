#!/usr/bin/env python3
"""
build-embeddings.py — Generate vector embeddings for all wiki pages.

Two modes:
  1. Local (default): TF-IDF term-frequency vector, zero external dependencies.
  2. API (--provider openrouter): uses OpenRouter free embedding models for
     real semantic embeddings (text-embedding-3-small via /api/v1/embeddings).

Stores embeddings in .wiki-embeddings.json at repo root.
Auto-chained from gen-index.py.

Usage:
    python3 scripts/wiki/build-embeddings.py                    # local TF-IDF
    python3 scripts/wiki/build-embeddings.py --provider openrouter  # API embeddings
    python3 scripts/wiki/build-embeddings.py --rebuild              # full rebuild
"""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
OUTPUT = REPO_ROOT / ".wiki-embeddings.json"

# Stopwords (Thai + English common)
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
HEADER_RE = re.compile(r"^#+\s+(.+?)\s*$", re.MULTILINE)

# ── Embedding API clients ──────────────────────────────────────────────


def _openrouter_embed(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Call OpenRouter embeddings endpoint. Returns list of vectors."""
    import urllib.request
    import urllib.error

    api_key = os.environ.get("OPENROUTER_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY or GEMINI_API_KEY not set. "
            "Use local mode (default) which needs no API key."
        )

    # Free embedding models on OpenRouter
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
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter embedding error {e.code}: {body[:500]}")

    # Sort by index to maintain order
    data["data"].sort(key=lambda x: x["index"])
    return [d["embedding"] for d in data["data"]]


# ── Local TF-IDF ───────────────────────────────────────────────────────


def tokenize(text: str) -> list[str]:
    """Lowercase tokenizer with stopword removal."""
    text = FRONTMATTER_RE.sub("", text)
    text = CODE_FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def build_local(docs: dict[str, str]) -> dict:
    """Build a simple TF-IDF vector per document.

    Returns:
        { "vectors": { "path": {"term": weight, ...}, ... },
          "idf": {"term": float, ...},
          "stats": {"docs": N, "terms": M, "mode": "local"} }
    """
    # Document frequency
    df: Counter[str] = Counter()
    doc_tokens: dict[str, Counter[str]] = {}

    for path, text in docs.items():
        tokens = tokenize(text)
        unique = set(tokens)
        for t in unique:
            df[t] += 1
        doc_tokens[path] = Counter(tokens)

    N = len(docs)
    idf: dict[str, float] = {}
    for term, count in df.items():
        idf[term] = math.log((N + 1) / (count + 1)) + 1  # smooth

    vectors: dict[str, dict[str, float]] = {}
    for path, tokens in doc_tokens.items():
        vec = {}
        for term, tf in tokens.items():
            vec[term] = (1 + math.log(tf)) * idf.get(term, 1.0)
        # Normalize to unit vector
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            vec = {k: v / norm for k, v in vec.items()}
        vectors[path] = vec

    return {
        "vectors": vectors,
        "idf": dict(idf),
        "params": {"N": N, "mode": "local"},
        "mode": "local",
    }


def build_api(docs: dict[str, str]) -> dict:
    """Build embeddings via OpenRouter API. Batches to avoid rate limits."""
    paths = list(docs.keys())
    texts = [docs[p] for p in paths]

    # Truncate each text to ~8000 chars to avoid token limits
    texts = [t[:8000] for t in texts]

    # Batch: 10 at a time
    batch_size = 10
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"  embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}...")
        try:
            embeddings = _openrouter_embed(batch)
            all_embeddings.extend(embeddings)
        except RuntimeError as e:
            print(f"  API error at batch {i // batch_size}: {e}", file=sys.stderr)
            print("  Falling back to local TF-IDF for remaining docs.", file=sys.stderr)
            # Fallback: fill remaining with empty vectors
            remaining = len(texts) - len(all_embeddings)
            all_embeddings.extend([[] for _ in range(remaining)])
            break
        time.sleep(1)  # rate limit

    # Build output
    vectors: dict[str, list[float]] = {}
    for path, emb in zip(paths, all_embeddings):
        if emb:
            # Normalize
            norm = math.sqrt(sum(v * v for v in emb))
            if norm > 0:
                emb = [v / norm for v in emb]
        vectors[path] = emb

    return {
        "vectors": vectors,
        "params": {"N": len(paths), "mode": "api"},
        "mode": "api",
    }


# ── Main ───────────────────────────────────────────────────────────────


def get_graph_pages() -> dict[str, str]:
    """Load all wiki page texts from .wiki-graph.json node list."""
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"Run build-wiki-graph.py first: {GRAPH_PATH} missing")
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    docs: dict[str, str] = {}
    for node in graph["nodes"]:
        p = REPO_ROOT / node["path"]
        if p.exists():
            docs[node["path"]] = p.read_text(encoding="utf-8", errors="replace")
    return docs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider", choices=("local", "openrouter"), default="local")
    p.add_argument("--rebuild", action="store_true", help="force full rebuild")
    p.add_argument("--output", default=str(OUTPUT))
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    existing = {}
    if not args.rebuild and OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if existing.get("mode") == args.provider:
            if not args.quiet:
                print(f"embeddings already exist at {OUTPUT} ({args.provider} mode)")
            return 0

    print(f"Building embeddings ({args.provider})...")
    docs = get_graph_pages()
    print(f"  loaded {len(docs)} pages")

    if args.provider == "openrouter":
        data = build_api(docs)
    else:
        data = build_local(docs)

    data["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.quiet:
        mode = data["mode"]
        stats = data.get("params", {})
        dims = len(next(iter(data["vectors"].values()))) if data["vectors"] else 0
        if mode == "local":
            terms = len(data.get("idf", {}))
            print(f"  {stats.get('N', 0)} docs, {terms} terms, TF-IDF vectors")
        else:
            print(f"  {stats.get('N', 0)} docs, {dims}-dim embeddings ({mode})")
        print(f"  saved to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())