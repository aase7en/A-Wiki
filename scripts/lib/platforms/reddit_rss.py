"""reddit_rss.py — Reddit subreddit feed reader (no-auth, no-cookie).

Endpoint verified alive 2026-08-01: https://www.reddit.com/r/<sub>/.rss
returns HTTP 200 + valid Atom 1.0 (25 entries per page). Reddit's `.json`
endpoint is DEAD (HTTP 403) since 2025 — RSS is the only no-auth path.

Reddit rejects anonymous User-Agents (their bot policy); we send a real,
descriptive UA. Low residential volume is safe; the `comments/.rss` endpoint
429s aggressively and is NOT used here.

Public API:
  - parse_feed(xml_text) -> list[dict]   pure parser (no I/O)
  - fetch_posts(subreddit, limit=25) -> list[dict]   network entry point

Fail-soft: never raises. Returns [{"error": "..."}] on any failure
(missing feedparser, network error, non-200, parse failure).
"""
from __future__ import annotations

import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

try:
    import feedparser  # type: ignore
except ImportError:
    feedparser = None  # type: ignore

__all__ = ["parse_feed", "fetch_posts", "MAX_SUMMARY_CHARS", "USER_AGENT"]

USER_AGENT = "A-Wiki-PlatformIngestBot/1.0 (no-auth RSS; +https://github.com/aase7en/A-Wiki)"
TIMEOUT = 20
MAX_SUMMARY_CHARS = 500  # bound token cost on long HTML Reddit content bodies
ATOM_NS = "{http://www.w3.org/2005/Atom}"


# ── pure parser ──────────────────────────────────────────────────────────

def _text_or_empty(el: Any) -> str:
    return (el.text or "").strip() if el is not None else ""


def parse_feed(xml_text: str) -> list[dict]:
    """Parse a Reddit Atom/RSS feed string into a list of flat entry dicts.

    Each entry: {title, url, summary, published, source}.
    Pure function — no I/O, never raises. Returns [] on empty/garbage input.
    """
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []  # garbage XML → empty list, not exception (fail-soft)

    # Atom feeds (Reddit's primary format) use <entry>; legacy RSS uses <item>
    entries = root.findall(f"{ATOM_NS}entry")
    if not entries:
        entries = root.findall(".//item")

    items: list[dict] = []
    for entry in entries:
        title = _text_or_empty(entry.find(f"{ATOM_NS}title"))
        if not title:
            # legacy RSS <item><title>
            title = _text_or_empty(entry.find("title"))

        # Atom <link href="..."> vs legacy RSS <link>text</link>
        link_el = entry.find(f"{ATOM_NS}link")
        url = ""
        if link_el is not None:
            url = link_el.attrib.get("href", "") or _text_or_empty(link_el)
        if not url:
            legacy_link = entry.find("link")
            if legacy_link is not None:
                url = _text_or_empty(legacy_link)

        summary = _text_or_empty(entry.find(f"{ATOM_NS}content"))
        if not summary:
            summary = _text_or_empty(entry.find(f"{ATOM_NS}summary"))
        if not summary:
            summary = _text_or_empty(entry.find("description"))
        summary = summary[:MAX_SUMMARY_CHARS]

        published = _text_or_empty(entry.find(f"{ATOM_NS}published"))
        if not published:
            published = _text_or_empty(entry.find(f"{ATOM_NS}updated"))
        if not published:
            published = _text_or_empty(entry.find("pubDate"))

        items.append({
            "title": title,
            "url": url,
            "summary": summary,
            "published": published,
            "source": "reddit",
        })
    return items


# ── network entry point ─────────────────────────────────────────────────

def fetch_posts(subreddit: str, limit: int = 25) -> list[dict]:
    """Fetch the latest posts from r/<subreddit> via the public RSS feed.

    Returns up to `limit` items. Fail-soft: returns [{"error": "..."}] on
    network error or non-200 response.

    Implementation note: `feedparser` is OPTIONAL here, not required. The
    stdlib xml.etree parser in parse_feed() handles Reddit's Atom 1.0 format
    fine on its own. feedparser would only be used if you wanted its
    richer entry-object API; we don't, so missing feedparser is a non-event.
    The `if feedparser is None` sentinel is preserved for callers that
    introspect availability, but fetch_posts() must NOT hard-fail on its
    absence — that would defeat the stdlib-only design (Iron Law #6 +
    the no-third-party-dep convention in scripts/lib/).
    """
    subreddit = subreddit.strip().lstrip("/")
    if not subreddit:
        return [{"error": "empty subreddit"}]

    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return [{"error": f"HTTP {e.code}: {subreddit}"}]
    except urllib.error.URLError as e:
        return [{"error": f"network error: {e}"}]
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {e}"}]

    items = parse_feed(xml_text)
    return items[:limit] if limit > 0 else items


# ── Channel wrapper (for doctor registry) ────────────────────────────────

from .base import Channel  # noqa: E402 — circular-safe, base has no deps on this


class RedditChannel(Channel):
    """Doctor-facing wrapper. check() runs a real probe against /r/news/.rss."""

    name = "reddit"
    backends = ["rss"]

    def check(self, config=None):
        # One cheap real probe — better than shutil.which() (Agent-ReachTrap #1).
        items = fetch_posts("news", limit=1)
        if items and "error" not in items[0]:
            return ("ok", "RSS feeds fetch OK", "rss")
        if items and "error" in items[0]:
            return ("warn", items[0]["error"][:80], None)
        return ("warn", "no items returned", None)
