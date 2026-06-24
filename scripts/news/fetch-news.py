#!/usr/bin/env python3
"""
News Intelligence — Layer 1: Data Collection
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Fetches news from RSS feeds + free APIs. No LLM involved.
Saves raw JSON to /opt/data/news/raw/

Usage:
  /opt/data/.venv-news/bin/python3 scripts/news/fetch-news.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

try:
    import feedparser
except ImportError:
    feedparser = None

# ════════════════════════════════
# PATHS
# ════════════════════════════════
DATA_ROOT = Path("/opt/data/news/raw")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════
# SOURCES (RSS + free APIs)
# ════════════════════════════════
SOURCES = [
    # ── Crypto ──
    {"id": "cointelegraph", "label": "Cointelegraph", "url": "https://cointelegraph.com/rss", "type": "rss"},
    {"id": "coindesk",      "label": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "type": "rss"},
    {"id": "decrypt",       "label": "Decrypt",       "url": "https://decrypt.co/feed", "type": "rss"},
    {"id": "cryptoslate",   "label": "CryptoSlate",   "url": "https://cryptoslate.com/feed/", "type": "rss"},

    # ── TradingView / Technical Analysis (same parent as TradingView) ──
    {"id": "investing",    "label":"Investing.com","url":"https://www.investing.com/rss/news.rss","type":"rss"},
    {"id": "investing-crypto","label":"Investing Crypto","url":"https://www.investing.com/rss/crypto_news.rss","type":"rss"},

    # ── Market Analysis ──
    {"id": "marketbeat",   "label":"MarketBeat","url":"https://www.marketbeat.com/rss/","type":"rss"},
    {"id": "reuters-finance","label":"Reuters Finance","url":"https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best","type":"rss"},
    {"id": "bnn-bleeding",  "label": "BNN Bloomberg", "url": "https://www.bnnbloomberg.ca/feed/", "type": "rss"},

    # ── Thai ──
    {"id": "prachachat-econ","label":"Prachachat","url":"https://www.prachachat.net/feed", "type":"rss"},
    {"id": "thairath-biz",  "label": "Thairath Biz", "url": "https://www.thairath.co.th/rss/biz", "type": "rss"},

    # ── Polymarket (free CLOB API) ──
    {
        "id": "polymarket",
        "label": "Polymarket Trending",
        "url": "https://clob.polymarket.com/markets?limit=20&closed=false&tag=election&tag=crypto&tag=financial",
        "type": "json",
    },

    # ── CoinGecko (free API, no key needed) ──
    {
        "id": "coingecko",
        "label": "CoinGecko Top Coins",
        "url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=20&page=1&sparkline=false",
        "type": "json",
    },
]

TIMEOUT = 20

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_rss(source: dict) -> list[dict]:
    """Fetch RSS feed via feedparser."""
    if feedparser is None:
        return [{"error": "feedparser not installed"}]

    try:
        feed = feedparser.parse(source["url"])
    except Exception as exc:
        return [{"error": str(exc)[:100]}]

    items = []
    for entry in feed.entries[:20]:  # top 20 per source
        items.append({
            "title": getattr(entry, "title", ""),
            "url": getattr(entry, "link", "") or getattr(entry, "id", ""),
            "summary": (getattr(entry, "summary", "") or "")[:500],
            "published": getattr(entry, "published", ""),
            "source": source["id"],
            "source_label": source["label"],
            "fetched_at": now_iso(),
        })
    return items


def fetch_json(source: dict) -> list[dict]:
    """Fetch JSON API endpoint."""
    try:
        req = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "A-Wiki-NewsBot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        return [{"error": str(exc)[:100]}]

    items = []
    if source["id"] == "polymarket" and isinstance(data, list):
        for m in data[:20]:
            title = m.get("question", "") or m.get("title", "")
            items.append({
                "title": f"[Polymarket] {title}",
                "url": f"https://polymarket.com/event/{m.get('condition_id', '')}",
                "summary": f"Volume: ${m.get('volume', 0):,.0f}  |  Outcome: {m.get('outcome_prices', '?')}  |  Closed: {m.get('closed', '?')}",
                "published": m.get("created_at", ""),
                "source": source["id"],
                "source_label": source["label"],
                "fetched_at": now_iso(),
                "tags": ["polymarket", "prediction-market"],
            })
    elif source["id"] == "coingecko" and isinstance(data, list):
        for coin in data[:20]:
            symbol = (coin.get("symbol") or "?").upper()
            name = coin.get("name") or "?"
            raw_price = coin.get("current_price")
            price = float(raw_price) if raw_price is not None else 0.0
            raw_chg = coin.get("price_change_percentage_24h")
            change_24h = float(raw_chg) if raw_chg is not None else 0.0
            raw_mcap = coin.get("market_cap")
            mcap = float(raw_mcap) if raw_mcap is not None else 0
            raw_vol = coin.get("total_volume")
            vol = float(raw_vol) if raw_vol is not None else 0
            items.append({
                "title": f"[{symbol}] {name} @ ${price:,.2f} ({change_24h:+.2f}% 24h)",
                "url": f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                "summary": f"MarketCap: ${mcap:,.0f}  Vol24h: ${vol:,.0f}",
                "published": now_iso(),
                "source": source["id"],
                "source_label": source["label"],
                "fetched_at": now_iso(),
                "tags": ["crypto", "price", symbol.lower()],
            })
    return items


def main() -> int:
    all_items: list[dict] = []
    errors: list[str] = []

    ts = now_iso()
    print(f"[{ts}] News Fetcher — {len(SOURCES)} sources")

    for src in SOURCES:
        try:
            if src["type"] == "rss":
                items = fetch_rss(src)
            elif src["type"] == "json":
                items = fetch_json(src)
            else:
                items = [{"error": f"unknown type: {src['type']}"}]

            error_items = [i for i in items if "error" in i]
            if error_items:
                errors.append(f"  {src['id']}: {error_items[0]['error']}")
                print(f"  ⚠️  {src['id']}: {error_items[0]['error']}")
            else:
                all_items.extend(items)
                print(f"  ✅ {src['id']}: {len(items)} items")

        except Exception as exc:
            errors.append(f"  {src['id']}: {exc}")
            print(f"  ❌ {src['id']}: {exc}")

    # Save raw output
    output = {
        "fetched_at": ts,
        "total_items": len(all_items),
        "sources": len(SOURCES),
        "source_errors": len(errors),
        "errors": errors,
        "items": all_items,
    }

    filename = f"news-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    out_path = DATA_ROOT / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Saved: {out_path} ({len(all_items)} items, {len(errors)} errors)")
    return 0 if len(errors) < len(SOURCES) else 1


if __name__ == "__main__":
    sys.exit(main())
