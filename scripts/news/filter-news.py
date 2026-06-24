#!/usr/bin/env python3
"""
News Intelligence — Layer 2: Filtering + Preprocessing
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Dedup, keyword classification, TextBlob sentiment. NO LLM.

Usage:
  /opt/data/.venv-news/bin/python3 scripts/news/filter-news.py [--hours 24]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

# ════════════════════════════════
# PATHS
# ════════════════════════════════
RAW_DIR = Path("/opt/data/news/raw")
OUT_DIR = Path("/opt/data/news/structured")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════
# KEYWORD / TOPIC MAPPING
# ════════════════════════════════
TOPICS = {
    "bitcoin":        ["bitcoin", "btc", "#btc"],
    "ethereum":       ["ethereum", "eth", "#eth"],
    "crypto":         ["crypto", "cryptocurrency", "altcoin", "defi", "nft", "blockchain"],
    "polymarket":     ["polymarket", "prediction market", "election odds"],
    "stock":          ["stock", "share", "nasdaq", "s&p", "dow jones", "nyse", "set index"],
    "forex":          ["usdthb", "usd/thb", "forex", "baht", "currency", "exchange rate"],
    "gold":           ["gold", "xau", "黄金", "ทองคำ"],
    "oil":            ["oil", "crude", "wti", "brent"],
    "thai":           ["ไทย", "เศรษฐกิจไทย", "กนง.", "ธปท.", "แบงก์ชาติ", "set"],
    "economy":        ["economy", "fed", "interest rate", "inflation", "gdp", "recession", "เฟด"],
    "regulation":     ["sec", "regulation", "regulatory", "ban", "crackdown", "ก.ล.ต."],
    "tradingview":    ["tradingview", "technical analysis", "support", "resistance"],
}

# Market assets for quick reference
ASSET_KEYWORDS = {
    "btc":  "Bitcoin",
    "eth":  "Ethereum",
    "xrp":  "XRP",
    "sol":  "Solana",
    "ada":  "Cardano",
    "doge": "Dogecoin",
    "bnb":  "BNB",
}

# Sources to filter out (noise)
EXCLUDE_PATTERNS = [
    r"sponsored\s*post",
    r"advertisement",
    r"press\s*release",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def extract_topics(text: str) -> list[str]:
    """Match keywords against text → return topic tags."""
    low = text.lower()
    found = set()
    for topic, keywords in TOPICS.items():
        if any(kw in low for kw in keywords):
            found.add(topic)
    return sorted(found)


def extract_assets(text: str) -> list[str]:
    """Find mentioned asset symbols."""
    low = text.lower()
    found = []
    for sym, name in ASSET_KEYWORDS.items():
        if sym in low or name.lower() in low:
            found.append(sym)
    return sorted(set(found))


def simple_sentiment(text: str) -> dict:
    """TextBlob sentiment (polarity [-1,1], subjectivity [0,1])."""
    if TextBlob is None or not text.strip():
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}
    try:
        blob = TextBlob(text[:1000])  # first 1000 chars
        pol = blob.sentiment.polarity
        sub = blob.sentiment.subjectivity
        if pol > 0.15:
            label = "positive"
        elif pol < -0.15:
            label = "negative"
        else:
            label = "neutral"
        return {"polarity": round(pol, 3), "subjectivity": round(sub, 3), "label": label}
    except Exception:
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}


def is_noise(title: str, summary: str) -> bool:
    """Check if an article looks like noise."""
    text = f"{title} {summary}".lower()
    return any(re.search(p, text) for p in EXCLUDE_PATTERNS)


def load_raw_files(hours: int) -> list[dict]:
    """Load all raw JSON files from the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[dict] = []

    for fpath in sorted(RAW_DIR.glob("news-*.json")):
        try:
            mtime = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            with open(fpath) as f:
                data = json.load(f)
            items.extend(data.get("items", []))
        except (json.JSONDecodeError, OSError):
            continue

    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter + dedup + sentiment raw news")
    parser.add_argument("--hours", type=int, default=24, help="Look back hours (default 24)")
    args = parser.parse_args()

    raw_items = load_raw_files(args.hours)
    print(f"📥 Loaded {len(raw_items)} raw items from last {args.hours}h")

    # ── Dedup by URL ──
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for item in raw_items:
        url = item.get("url", "")
        if not url:
            continue
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in seen_urls:
            continue
        seen_urls.add(url_hash)
        deduped.append(item)

    print(f"🔀 After dedup: {len(deduped)} unique items")

    # ── Filter noise ──
    cleaned = [item for item in deduped if not is_noise(
        item.get("title", ""), item.get("summary", "")
    )]
    print(f"🧹 After noise filter: {len(cleaned)} items")

    # ── Enrich ──
    enriched: list[dict] = []
    for item in cleaned:
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        sentiment = simple_sentiment(text)
        topics = extract_topics(text)
        assets = extract_assets(text)

        enriched.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "summary": (item.get("summary", "") or "")[:300],
            "source": item.get("source", "?"),
            "source_label": item.get("source_label", "?"),
            "published": item.get("published", ""),
            "fetched_at": item.get("fetched_at", ""),
            "sentiment": sentiment,
            "topics": topics,
            "assets": assets,
            "signal_strength": abs(sentiment["polarity"]) * 10,  # 0-10 scale
        })

    # ── Sort by signal strength ──
    enriched.sort(key=lambda x: -x["signal_strength"])

    # ── Stats ──
    topic_counts: dict[str, int] = {}
    for item in enriched:
        for t in item["topics"]:
            topic_counts[t] = topic_counts.get(t, 0) + 1

    sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
    for item in enriched:
        sentiment_dist[item["sentiment"]["label"]] = (
            sentiment_dist.get(item["sentiment"]["label"], 0) + 1
        )

    # ── Save ──
    ts = now_iso()
    output = {
        "generated_at": ts,
        "lookback_hours": args.hours,
        "stats": {
            "raw_total": len(raw_items),
            "after_dedup": len(deduped),
            "after_filter": len(cleaned),
            "sentiment": sentiment_dist,
            "top_topics": sorted(topic_counts.items(), key=lambda x: -x[1])[:10],
        },
        "items": enriched,
    }

    filename = f"filtered-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    out_path = OUT_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Saved: {out_path} ({len(enriched)} items)")
    print(f"   Sentiment: {sentiment_dist}")
    print(f"   Top topics: {', '.join(f'{t}({c})' for t, c in sorted(topic_counts.items(), key=lambda x: -x[1])[:5])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
