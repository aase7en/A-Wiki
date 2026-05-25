#!/usr/bin/env python3
"""
query-rag.py — GraphRAG semantic query over A-Wiki sources and syntheses.

Embeds wiki/sources/ and wiki/synthesis/ documents using sentence-transformers,
indexes them with FAISS, and supports hybrid search (semantic + tag/concept filter).

Usage:
    python3 scripts/query-rag.py build                           # build/rebuild the index
    python3 scripts/query-rag.py "water quality iot sensor"      # search with query
    python3 scripts/query-rag.py "water quality" --domain env    # filter by domain
    python3 scripts/query-rag.py "edge ML" --top-k 10            # top 10 results
    python3 scripts/query-rag.py "drug interaction" --tags "clinical-decision-support,pharmacy"
    python3 scripts/query-rag.py "mqtt vs lorawan" --expand      # query expansion (3 variants)
    python3 scripts/query-rag.py "air quality" --source-only     # sources only, no syntheses
    python3 scripts/query-rag.py "emerging contaminants" --synthesis-only
    python3 scripts/query-rag.py status                           # show index stats
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
SYNTHESIS_DIR = REPO_ROOT / "wiki" / "synthesis"
INDEX_DIR = REPO_ROOT / ".rag-index"
INDEX_FILE = INDEX_DIR / "index.faiss"
META_FILE = INDEX_DIR / "metadata.json"

# Embedding config
EMBED_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast, good for semantic similarity
EMBED_DIM = 384


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def log(msg: str) -> None:
    print(f"[rag] {msg}", file=sys.stderr)


# ─── Document Loading ────────────────────────────────────────────────

def parse_doc_frontmatter(text: str, rel_path: str, doc_type: str) -> dict[str, Any]:
    """Parse a .md document into a structured entry for indexing."""
    doc: dict[str, Any] = {
        "path": rel_path,
        "title": "Untitled",
        "type": doc_type,
        "domain": "general",
        "tags": [],
        "concepts": [],
        "content": "",
        "quality": "seed",
    }
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        doc["title"] = m.group(1).strip()

    for line in text.splitlines():
        line_s = line.strip()
        kv = re.match(r">\s*\*\*(\w+):\*\*\s*(.+)", line_s)
        if kv:
            key = kv.group(1).lower()
            val = kv.group(2).strip()
            if key == "type":
                doc["type"] = val
            elif key == "domain":
                doc["domain"] = val
            elif key == "quality":
                doc["quality"] = val
            elif key == "tags":
                doc["tags"] = [t.strip().lower() for t in val.split(",")]

    # Concepts from body
    for cm in re.finditer(r"\*\*(.+?)\*\*\s*[—–-]\s*(.+?)(?=\n|$)", text):
        doc["concepts"].append(cm.group(1).strip())

    # Content: strip metadata header, keep Abstract + body for embedding
    body = re.sub(r"^# .+\n", "", text, count=1)
    body = re.sub(r"^>.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^---.*?---", "", body, flags=re.DOTALL)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    doc["content"] = body
    doc["content_len"] = len(body)

    return doc


def load_all_documents() -> list[dict[str, Any]]:
    """Load all source and synthesis documents."""
    docs: list[dict[str, Any]] = []

    # Sources
    if SOURCES_DIR.is_dir():
        for domain_dir in sorted(SOURCES_DIR.iterdir()):
            if not domain_dir.is_dir():
                continue
            for md_file in sorted(domain_dir.glob("*.md")):
                try:
                    text = md_file.read_text(encoding="utf-8")
                    rel = str(md_file.relative_to(REPO_ROOT))
                    doc = parse_doc_frontmatter(text, rel, "source")
                    docs.append(doc)
                except Exception as e:
                    log(f"skip source {md_file}: {e}")

    # Syntheses
    if SYNTHESIS_DIR.is_dir():
        for md_file in sorted(SYNTHESIS_DIR.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                rel = str(md_file.relative_to(REPO_ROOT))
                doc = parse_doc_frontmatter(text, rel, "synthesis")
                docs.append(doc)
            except Exception as e:
                log(f"skip synthesis {md_file}: {e}")

    log(f"loaded {len(docs)} documents ({sum(1 for d in docs if d['type']=='source')} sources, "
        f"{sum(1 for d in docs if d['type']=='synthesis')} syntheses)")
    return docs


# ─── Embedding + Indexing ────────────────────────────────────────────

def build_index(docs: list[dict[str, Any]]) -> tuple[Any, list[dict[str, Any]]]:
    """Build FAISS index from document embeddings."""
    np_dep = __import__("numpy", fromlist=["array"])
    faiss_dep = __import__("faiss", fromlist=["IndexFlatIP"])
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        log("ERROR: sentence-transformers not installed. Install with:")
        log("  pip install sentence-transformers faiss-cpu numpy")
        sys.exit(1)

    log(f"loading embedding model '{EMBED_MODEL}'...")
    model = SentenceTransformer(EMBED_MODEL)

    # Prepare texts for embedding
    texts = []
    valid_docs = []
    for doc in docs:
        content = doc.get("content", "").strip()
        if not content or len(content) < 10:
            continue
        texts.append(content)
        valid_docs.append(doc)

    log(f"embedding {len(texts)} documents...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    log(f"embeddings shape: {embeddings.shape}")

    # Build FAISS index (IP = cosine similarity on normalized vectors)
    index = faiss_dep.IndexFlatIP(EMBED_DIM)
    index.add(np_dep.array(embeddings, dtype=np.float32))
    log(f"index size: {index.ntotal} vectors")

    return index, valid_docs


def save_index(index: Any, docs: list[dict[str, Any]]) -> None:
    """Persist FAISS index + metadata to disk."""
    import pickle
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss_dep = __import__("faiss", fromlist=["write_index"])
    faiss_dep.write_index(index, str(INDEX_FILE))

    # Save metadata
    meta = {
        "build_time": dt.datetime.now().isoformat(),
        "embed_model": EMBED_MODEL,
        "num_docs": len(docs),
        "docs": [
            {
                "path": d["path"],
                "title": d["title"],
                "type": d["type"],
                "domain": d["domain"],
                "tags": d["tags"],
                "concepts": d["concepts"][:8],
                "quality": d["quality"],
                "content_len": d["content_len"],
            }
            for d in docs
        ],
    }
    META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log(f"saved {len(docs)} docs to {META_FILE}, index to {INDEX_FILE}")


def load_index() -> tuple[Any, list[dict[str, Any]]]:
    """Load FAISS index + metadata from disk."""
    if not INDEX_FILE.exists() or not META_FILE.exists():
        log("ERROR: no index found. Run 'query-rag.py build' first.")
        sys.exit(1)

    faiss_dep = __import__("faiss", fromlist=["read_index"])
    index = faiss_dep.read_index(str(INDEX_FILE))
    meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    docs = meta["docs"]
    log(f"loaded index: {index.ntotal} vectors, {len(docs)} docs (built {meta['build_time']})")
    return index, docs


# ─── Query ───────────────────────────────────────────────────────────

def generate_query_variants(query: str) -> list[str]:
    """Generate query expansion variants."""
    variants = [query]

    # Add prefix variants
    prefixes = [
        "Explain", "What is", "Compare and contrast",
    ]
    for p in prefixes:
        if not query.lower().startswith(p.lower()):
            variants.append(f"{p} {query}")

    # Add question variant
    if not query.endswith("?"):
        variants.append(f"What are key aspects of {query}?")
        variants.append(f"Describe {query}")

    # Dedupe while preserving order — original query stays first
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out[:5]


def search(
    query: str,
    index: Any,
    docs: list[dict[str, Any]],
    top_k: int = 5,
    domain: str | None = None,
    tags: list[str] | None = None,
    source_only: bool = False,
    synthesis_only: bool = False,
    expand: bool = False,
) -> list[dict[str, Any]]:
    """Search the index and return ranked results."""
    np_dep = __import__("numpy", fromlist=["array"])
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        log("ERROR: sentence-transformers not installed.")
        sys.exit(1)

    model = SentenceTransformer(EMBED_MODEL)

    # Query expansion
    query_variants = generate_query_variants(query) if expand else [query]

    all_scores: list[tuple[int, float]] = []
    seen_pairs: set[tuple[int, int]] = set()

    for qv in query_variants:
        q_emb = model.encode([qv], normalize_embeddings=True)
        scores_matrix, idx_matrix = index.search(np_dep.array(q_emb, dtype=np.float32), top_k * 2)

        for doc_idx, score in zip(idx_matrix[0], scores_matrix[0]):
            if doc_idx < 0:
                continue
            pair_id = (doc_idx, id(qv))
            if pair_id not in seen_pairs:
                seen_pairs.add((doc_idx, id(qv)))
                all_scores.append((doc_idx, float(score)))

    # Aggregate scores (max across variants)
    doc_scores: dict[int, float] = {}
    for doc_idx, score in all_scores:
        if doc_idx not in doc_scores or score > doc_scores[doc_idx]:
            doc_scores[doc_idx] = score

    # Sort by score descending
    ranked = sorted(doc_scores.items(), key=lambda x: -x[1])

    # Build results with metadata
    results = []
    for doc_idx, score in ranked:
        if len(results) >= top_k:
            break
        doc = docs[doc_idx]

        # Apply filters
        if domain and doc.get("domain", "").lower() != domain.lower():
            continue
        if tags:
            doc_tags = set(t.lower() for t in doc.get("tags", []))
            if not doc_tags & set(t.lower() for t in tags):
                continue
        if source_only and doc.get("type") != "source":
            continue
        if synthesis_only and doc.get("type") != "synthesis":
            continue

        results.append({
            "rank": len(results) + 1,
            "score": round(score, 4),
            "title": doc["title"],
            "path": doc["path"],
            "type": doc.get("type", "unknown"),
            "domain": doc.get("domain", "general"),
            "tags": doc.get("tags", []),
            "concepts": doc.get("concepts", [])[:5],
            "quality": doc.get("quality", "seed"),
            "content_len": doc.get("content_len", 0),
        })

    return results


def format_results(results: list[dict[str, Any]], show_content: bool = False) -> str:
    """Format search results for terminal display."""
    if not results:
        return "No results found."

    lines = [f"Found {len(results)} results:\n"]
    for r in results:
        score_pct = int(r["score"] * 100)
        bar = "█" * (score_pct // 10) + "░" * (10 - score_pct // 10)
        lines.append(
            f"  [{r['rank']}] {r['title']}\n"
            f"      Score: {r['score']:.4f} {bar}\n"
            f"      Path:  {r['path']}\n"
            f"      Type:  {r['type']} | Domain: {r['domain']} | Quality: {r['quality']}\n"
        )
        if r.get("tags"):
            lines.append(f"      Tags:  {', '.join(r['tags'][:6])}\n")
        if r.get("concepts"):
            lines.append(f"      Concepts: {', '.join(r['concepts'][:5])}\n")
        lines.append("\n")

    return "".join(lines)


def format_json(results: list[dict[str, Any]]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2, ensure_ascii=False)


def show_status() -> None:
    """Display index statistics."""
    if not META_FILE.exists():
        print("No index found. Run 'query-rag.py build' first.")
        return
    meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    docs = meta["docs"]

    print(f"GraphRAG Index Status\n")
    print(f"  Build time:    {meta['build_time']}")
    print(f"  Embed model:   {meta['embed_model']}")
    print(f"  Total docs:    {meta['num_docs']}\n")

    # Count by type
    sources = [d for d in docs if d["type"] == "source"]
    syntheses = [d for d in docs if d["type"] == "synthesis"]
    print(f"  Sources:       {len(sources)}")
    print(f"  Syntheses:     {len(syntheses)}\n")

    # Count by domain
    domains: dict[str, int] = defaultdict(int)
    for d in docs:
        domains[d.get("domain", "unknown")] += 1
    print("  By domain:")
    for dom in sorted(domains.keys()):
        print(f"    {dom:20s}: {domains[dom]}")

    # Tag cloud
    tag_counts: dict[str, int] = defaultdict(int)
    for d in docs:
        for tag in d.get("tags", []):
            tag_counts[tag.lower()] += 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:15]
    if top_tags:
        print("\n  Top tags:")
        for tag, count in top_tags:
            print(f"    {tag:30s}: {count}")


# ─── CLI ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GraphRAG query over A-Wiki")
    parser.add_argument("command", nargs="?", default="status",
                        help="'build' to index, 'status' for stats, or a search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--domain", help="Filter by domain (e.g., iot, env, ai-tools)")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    parser.add_argument("--source-only", action="store_true", help="Only return source documents")
    parser.add_argument("--synthesis-only", action="store_true", help="Only return synthesis documents")
    parser.add_argument("--expand", action="store_true", help="Enable query expansion")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    cmd = args.command

    if cmd == "build":
        log("building GraphRAG index...")
        docs = load_all_documents()
        if not docs:
            log("ERROR: no documents found to index")
            sys.exit(1)
        index, valid_docs = build_index(docs)
        save_index(index, valid_docs)
        print(f"[rag] Index built: {index.ntotal} vectors across {len(valid_docs)} documents")

    elif cmd == "status":
        show_status()

    else:
        # Search
        if not INDEX_FILE.exists():
            print("No index found. Run 'query-rag.py build' first.")
            sys.exit(1)
        index, docs = load_index()

        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        results = search(
            query=cmd,
            index=index,
            docs=docs,
            top_k=args.top_k,
            domain=args.domain,
            tags=tags,
            source_only=args.source_only,
            synthesis_only=args.synthesis_only,
            expand=args.expand,
        )

        if args.json:
            print(format_json(results))
        else:
            print(format_results(results))


if __name__ == "__main__":
    main()