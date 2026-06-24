#!/usr/bin/env python3
"""
TradingView Ideas Scraper — ดึง community ideas + วิเคราะห์ตลาด
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Usage:
  /opt/data/.venv-news/bin/python3 scripts/news/tv-ideas.py [--topics bitcoin,ethereum,forex]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# ════════════════════════════════
# PATHS
# ════════════════════════════════
OUT_DIR = Path("/opt/data/news/tv-ideas")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════
# TOPICS / SYMBOLS TO TRACK
# ════════════════════════════════
TOPICS = {
    "bitcoin":  "bitcoin",
    "ethereum": "ethereum",
    "crypto":   "cryptocurrency",
    "forex":    "forex",
    "stocks":   "stock-market",
    "gold":     "gold",
}

KEY_LEVEL_PATTERNS = re.compile(
    r'(support|resistance|target|break|trigger|entry|stop[\s-]?loss|take[\s-]?profit|short|long|buy|sell)'
    r'\s*(?::|at|below|above|near|around|level|zone|area)?\s*'
    r'(\$?\d{1,6}(?:,\d{3})*(?:\.\d+)?)',
    re.IGNORECASE
)

SENTIMENT_KEYWORDS = {
    "bullish": ["bullish", "bull", "uptrend", "rally", "breakout", "buy", "long"],
    "bearish": ["bearish", "bear", "downtrend", "sell-off", "breakdown", "sell", "short"],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_ideas_page(topic_key: str, slug: str) -> str | None:
    """Fetch TradingView ideas page HTML."""
    url = f"https://www.tradingview.com/ideas/{slug}/"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  ⚠️  {topic_key}: {exc}")
        return None


def parse_ideas(html: str, topic_key: str) -> list[dict]:
    """Parse TradingView ideas from SSR HTML."""
    items = []

    if BeautifulSoup:
        soup = BeautifulSoup(html, "lxml")
        # Find article cards with ideaCard class
        for art in soup.find_all("article", class_=re.compile(r"ideaCard")):
            # Title link
            title_el = art.find("a", attrs={"data-qa-id": "ui-lib-card-link-title"})
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if not title or len(title) < 15:
                continue

            # Find symbol link
            symbol_el = art.find("a", href=re.compile(r":\w+$"))
            symbol = symbol_el.get_text(strip=True) if symbol_el else ""

            # Find author
            author_el = art.find("a", href=re.compile(r"/u/"))
            author = author_el.get_text(strip=True) if author_el else ""

            items.append({
                "title": title,
                "href": href,
                "url": href if href.startswith("http") else f"https://www.tradingview.com{href}",
                "symbol": symbol,
                "author": author,
                "topic": topic_key,
            })

    # Fallback regex
    if not items:
        for m in re.finditer(
            r'href="(https?://www\.tradingview\.com/chart/[^"]+)"[^>]*data-qa-id="ui-lib-card-link-title"[^>]*>([^<]+)</a>',
            html,
        ):
            href, title = m.group(1), m.group(2).strip()
            if title and len(title) > 15:
                items.append({
                    "title": title,
                    "href": href,
                    "url": href,
                    "topic": topic_key,
                })

    return items


def extract_key_levels(text: str) -> list[dict]:
    """Extract support/resistance levels from analysis text."""
    levels = []
    for match in KEY_LEVEL_PATTERNS.finditer(text):
        label = match.group(1).lower()
        price_str = match.group(2).replace(",", "")
        try:
            price = float(price_str)
            levels.append({"type": label, "price": price})
        except ValueError:
            continue
    return levels


def guess_sentiment(text: str) -> str:
    """Guess sentiment from text keyword matching."""
    low = text.lower()
    bull_score = sum(1 for kw in SENTIMENT_KEYWORDS["bullish"] if kw in low)
    bear_score = sum(1 for kw in SENTIMENT_KEYWORDS["bearish"] if kw in low)
    if bull_score > bear_score:
        return "bullish"
    elif bear_score > bull_score:
        return "bearish"
    return "neutral"


def fetch_idea_detail(url: str) -> str | None:
    """Fetch individual idea page for full analysis text."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        # Extract main content - paragraphs with analysis
        if BeautifulSoup:
            soup = BeautifulSoup(html, "lxml")
            for tag in soup.find_all(["p", "div"]):
                text = tag.get_text(strip=True)
                if len(text) > 100 and any(kw in text.lower() for kw in
                    ["support", "resistance", "analysis", "price"]):
                    return text[:2000]
        # Fallback regex
        paras = re.findall(r'<p[^>]*>([^<]{100,})</p>', html)
        if paras:
            return " ".join(p[:500] for p in paras[:5])
        return None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="TradingView Ideas scraper")
    parser.add_argument("--topics", default="bitcoin,ethereum,crypto",
                        help="Comma-separated topics (default: bitcoin,ethereum,crypto)")
    parser.add_argument("--detail", action="store_true",
                        help="Fetch full analysis for each idea (slower)")
    args = parser.parse_args()

    selected = [t.strip() for t in args.topics.split(",") if t.strip() in TOPICS]
    if not selected:
        selected = list(TOPICS.keys())

    ts = now_iso()
    print(f"[{ts}] TradingView Ideas Scraper — {len(selected)} topics\n")

    all_ideas: list[dict] = []
    topic_counts: dict[str, int] = {}

    for topic_key in selected:
        slug = TOPICS[topic_key]
        print(f"  📡 {topic_key} ({slug}) ...", end=" ", flush=True)

        html = fetch_ideas_page(topic_key, slug)
        if not html:
            print("❌")
            continue

        ideas = parse_ideas(html, topic_key)
        print(f"{len(ideas)} ideas")
        topic_counts[topic_key] = len(ideas)

        # Sample: get key levels from first idea
        sample_text = ""
        if ideas:
            # Try to also find analysis paragraphs in the page
            if BeautifulSoup:
                soup = BeautifulSoup(html, "lxml")
                paras = soup.find_all("div", class_=re.compile(r"paragraph|content|description|text"))
                if not paras:
                    paras = soup.find_all("p")
                for p in paras[:10]:
                    t = p.get_text(strip=True)
                    if len(t) > 100:
                        sample_text += t + "\n"

        # Extract key levels from page
        levels = extract_key_levels(html[:50000])
        sentiment = guess_sentiment(html[:50000])

        for idea in ideas:
            idea["sample_levels"] = levels[:5]
            idea["sentiment"] = sentiment
            all_ideas.append(idea)

    # ── Save ──
    output = {
        "fetched_at": ts,
        "topics_fetched": selected,
        "total_ideas": len(all_ideas),
        "topic_counts": topic_counts,
        "ideas": all_ideas,
    }

    filename = f"tv-ideas-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    out_path = OUT_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Saved: {out_path} ({len(all_ideas)} ideas)")
    for t, c in topic_counts.items():
        print(f"   {t}: {c} ideas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
