#!/usr/bin/env python3
"""
arxiv — arXiv search + two-tier ingest pipeline

Tier 1: Search & score abstracts (no LLM, heuristic-based)
Tier 2: Download + extract full-text for high-scoring papers

Integration: gen-index.py chains this via --arxiv flag
Manual:     python3 scripts/fetch-arxiv.py --search "LoRa ESP32 IoT" --max 5
            python3 scripts/fetch-arxiv.py --search "LLM agent evaluation" --max 10 --apply

Output:
  raw/arxiv/YYYYMMDD_<slug>.pdf     — downloaded PDF
  raw/arxiv/YYYYMMDD_<slug>.md      — metadata + abstract (Tier 1)
  wiki/sources/arxiv-YYYYMMDD_<slug>.md  — if --apply (Tier 2)
"""

import argparse, json, os, re, sys, time, hashlib, textwrap, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

try:
    import arxiv
except ImportError:
    arxiv = None

RAW_DIR  = Path(__file__).parent.parent / "raw" / "arxiv"
SRC_DIR  = Path(__file__).parent.parent / "wiki" / "sources"
CACHE    = Path(__file__).parent.parent / "raw" / "arxiv" / ".arxiv-cache.json"

os.makedirs(RAW_DIR, exist_ok=True)

# ── Domain classifier (heuristic, no LLM) ──────────────────────────
DOMAIN_KEYWORDS = {
    "iot":       ["iot", "internet of things", "sensor", "lora", "lorawan",
                   "esp32", "raspberry pi", "embedded", "firmware",
                   "microcontroller", "mqtt", "edge", "gateway"],
    "ai-tools":  ["llm", "large language model", "agent", "gpt", "claude",
                   "prompt", "rag", "retrieval augmented", "fine-tun",
                   "tool use", "function calling", "mcp", "model context protocol"],
    "env":       ["environment", "wastewater", "air quality", "water quality",
                   "pollution", "climate", "sustainable"],
    "pharmacy":  ["pharmacy", "pharmac", "drug", "medication", "prescription",
                   "vaccine", "cold chain", "rabies", "dosing"],
}

SCORE_WEIGHTS = {
    "title_kw": 3, "abstract_kw": 1, "recency": 1.5, "open_access": 0.5
}

def classify_domain(title: str, abstract: str) -> tuple:
    """Return (best_domain, score, matched_keywords)"""
    text = (title + " " + abstract).lower()
    best_domain, best_score, best_kws = "uncategorized", 0, []
    for domain, kws in DOMAIN_KEYWORDS.items():
        score = 0
        found = []
        for kw in kws:
            if kw in text:
                score += 1
                found.append(kw)
        if score > best_score:
            best_score = score
            best_domain = domain
            best_kws = found
    return best_domain, best_score, best_kws


def score_paper(paper) -> float:
    """Heuristic relevance score 0-100"""
    t, a = paper.title, paper.summary
    domain, kw_score, _ = classify_domain(t, a)

    # Weighted score
    s = kw_score * 3  # each keyword ≈ 3 pts

    # Recency bonus: papers within 2 years
    if paper.published:
        age_days = (datetime.now(paper.published.tzinfo) - paper.published).days
        if age_days < 365:
            s += 15
        elif age_days < 730:
            s += 8

    # Open access bonus
    if getattr(paper, 'is_open_access', False):
        s += 5

    return min(s, 100), domain


def slugify(title: str) -> str:
    """Generate filesystem-safe slug from title"""
    s = title.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')[:80]
    return s


def fetch(search_query: str, max_results: int = 10) -> list:
    """Search arxiv and return scored results (Tier 1)"""
    if arxiv is None:
        print("❌ arxiv library not installed. Run: pip3 install arxiv")
        sys.exit(1)

    print(f"🔍 Searching arxiv: {search_query}")
    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=3)
    search = arxiv.Search(
        query=search_query,
        max_results=max_results * 2,  # fetch extra for scoring
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    for i, paper in enumerate(client.results(search)):
        if i >= max_results * 2:
            break
        score, domain = score_paper(paper)
        if score < 10:
            continue
        results.append({
            "id": paper.entry_id.split("/")[-1].split("v")[0],
            "title": paper.title,
            "authors": [a.name for a in paper.authors[:5]],
            "published": str(paper.published.date()) if paper.published else "unknown",
            "updated": str(paper.updated.date()) if paper.updated else "unknown",
            "abstract": paper.summary[:2000],
            "url": paper.entry_id,
            "pdf_url": paper.pdf_url,
            "domain": domain,
            "score": round(score, 1),
            "categories": paper.categories,
        })
        print(f"  [{len(results)}] score={score:.0f} domain={domain:12s} | {paper.title[:60]}")

    # Sort by score descending, return top max_results
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def download(paper: dict, apply: bool = False) -> str:
    """Download PDF and save metadata to raw/arxiv/ (Tier 2)"""
    date_prefix = paper["published"].replace("-", "")[:8] or datetime.now().strftime("%Y%m%d")
    slug = slugify(paper["title"])
    base = f"{date_prefix}_{slug}"

    pdf_path = RAW_DIR / f"{base}.pdf"
    meta_path = RAW_DIR / f"{base}.md"
    src_path = SRC_DIR / f"arxiv-{base}.md"

    # Skip if already exists
    if meta_path.exists():
        print(f"  ⏭  Already exists: {base}")
        return str(meta_path)

    # Download PDF
    try:
        print(f"  ⬇️  Downloading PDF: {paper['pdf_url']}")
        urllib.request.urlretrieve(paper["pdf_url"], pdf_path)
        time.sleep(1)
    except Exception as e:
        print(f"  ⚠️  PDF download failed: {e}")
        pdf_path = None

    # Save metadata + abstract
    meta = f"""---
arxiv_id: "{paper['id']}"
title: "{paper['title']}"
authors: {json.dumps(paper['authors'])}
published: {paper['published']}
updated: {paper['updated']}
domain: {paper['domain']}
score: {paper['score']}
categories: {json.dumps(paper['categories'])}
source: arxiv
---

# {paper['title']}

**Authors:** {', '.join(paper['authors'])}
**Published:** {paper['published']}
**URL:** {paper['url']}
**Domain:** {paper['domain']} | **Relevance:** {paper['score']}/100

## Abstract

{paper['abstract']}
"""
    meta_path.write_text(meta)
    print(f"  📄 Saved meta: {meta_path.name}")

    # Tier 2: Generate wiki source file (abstract only — no full-text extraction)
    if apply and src_path:
        source_content = f"""---
type: source
domain: {paper['domain']}
arxiv_id: "{paper['id']}"
score: {paper['score']}
tags: [{', '.join(paper['categories'][:5])}]
---

# Source: {paper['title']}

**Source:** arXiv ({paper['id']})  
**Authors:** {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}  
**Published:** {paper['published']}

## Key Insights

- arXiv paper scored {paper['score']}/100 for domain "{paper['domain']}"
- Categorized under: {', '.join(paper['categories'][:5])}

## Abstract (Condensed)

{paper['abstract'][:500]}

## Relevance

{heuristic_relevance_note(paper)}
"""
        src_path.write_text(source_content)
        print(f"  🧠 Wiki source created: {src_path.name}")

    return str(meta_path)


def heuristic_relevance_note(paper: dict) -> str:
    """Generate a short relevance note based on heuristics"""
    lines = []
    if paper["score"] >= 50:
        lines.append("- **High relevance** — strong keyword match with current wiki domains.")
    elif paper["score"] >= 25:
        lines.append("- **Medium relevance** — some keywords match, worth reviewing abstract.")
    else:
        lines.append("- **Low relevance** — minimal keyword overlap, consider skipping.")

    lines.append(f"- Domain classification: {paper['domain']} (heuristic)")
    lines.append(f"- Click through to arXiv for full text: [{paper['id']}]({paper['url']})")
    return "\n".join(lines)


def stats() -> dict:
    """Show download stats"""
    pdfs = list(RAW_DIR.glob("*.pdf"))
    metas = list(RAW_DIR.glob("*.md"))
    return {"pdfs": len(pdfs), "metas": len(metas), "dir": str(RAW_DIR)}


def main():
    parser = argparse.ArgumentParser(description="arXiv search + two-tier ingest")
    parser.add_argument("--search", "-s", help="Search query for arxiv")
    parser.add_argument("--max", "-n", type=int, default=5, help="Max results")
    parser.add_argument("--apply", "-a", action="store_true",
                        help="Tier 2: download PDFs + create wiki sources")
    parser.add_argument("--stats", action="store_true", help="Show download stats")
    parser.add_argument("--domain", choices=list(DOMAIN_KEYWORDS.keys()) + ["all"],
                        default=None, help="Filter results by domain")
    args = parser.parse_args()

    if args.stats:
        s = stats()
        print(f"📊 arXiv raw/ directory: {s['pdfs']} PDFs, {s['metas']} metadata files")
        return

    if not args.search:
        parser.print_help()
        print("\n💡 Example: python3 scripts/fetch-arxiv.py --search 'LoRa ESP32 IoT' --max 5 --apply")
        return

    results = fetch(args.search, args.max)

    if args.domain and args.domain != "all":
        results = [r for r in results if r["domain"] == args.domain]
        print(f"   Filtered to domain={args.domain}: {len(results)} results")

    if not results:
        print("❌ No matching results found.")
        return

    if args.apply:
        print(f"\n⬇️  Tier 2: Downloading {len(results)} papers...")
        for r in results:
            download(r, apply=True)
    else:
        print(f"\n📋 Tier 1 results (use --apply to download):")
        for r in results:
            print(f"  [{r['score']:5.1f}] [{r['domain']:12s}] {r['title'][:70]}")
        print(f"\n{'~'*60}")
        print(f"Total: {len(results)} papers. Re-run with --apply to download + create sources.")

    # Cache results
    cache = {"query": args.search, "timestamp": datetime.now().isoformat(), "hits": len(results)}
    try:
        CACHE.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass


if __name__ == "__main__":
    main()