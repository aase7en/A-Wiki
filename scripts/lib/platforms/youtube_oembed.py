"""youtube_oembed.py — YouTube video metadata reader (no-auth, no-cookie).

Endpoint verified alive 2026-08-01: https://www.youtube.com/oembed returns
HTTP 200 + valid JSON with no auth. Gives title, author, thumbnail, embed
HTML. Does NOT give transcript — transcript retrieval needs yt-dlp + the
new yt-dlp-ejs JS engine (Phase 2 opt-in).

Public API:
  - extract_video_id(url) -> str | None      pure URL parser
  - reshape_oembed(raw, video_url) -> dict   reshape API JSON
  - fetch_metadata(url) -> dict              network entry point

Fail-soft: never raises. Returns {"error": "..."} on any failure
(invalid URL, network error, non-200).
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

__all__ = ["extract_video_id", "reshape_oembed", "fetch_metadata", "USER_AGENT"]

USER_AGENT = "A-Wiki-PlatformIngestBot/1.0 (oEmbed; +https://github.com/aase7en/A-Wiki)"
TIMEOUT = 20
# 11-char video id (legacy) — YT also has 1-char experiment ids but they
# never appear in oEmbed-eligible URLs in practice.
_VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")

# URL shapes that actually carry a video id, ordered by frequency.
_KNOWN_SHAPES = (
    re.compile(r"youtube\.com/watch\?[^#]*v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/live/([A-Za-z0-9_-]{11})"),
    re.compile(r"m\.youtube\.com/watch\?[^#]*v=([A-Za-z0-9_-]{11})"),
)


# ── pure URL parser ───────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    """Extract the 11-char video id from any common YouTube URL shape.

    Returns None for non-video URLs (channel pages, search, feed, etc.).
    Pure function — no I/O.
    """
    if not url or not isinstance(url, str):
        return None
    for pattern in _KNOWN_SHAPES:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


# ── reshape API JSON ────────────────────────────────────────────────────

def reshape_oembed(raw: dict, video_url: str) -> dict:
    """Reshape the raw oEmbed JSON into a flat dict with stable keys.

    Tolerant of missing fields — returns "" rather than KeyError.
    """
    return {
        "title":     raw.get("title", ""),
        "author":    raw.get("author_name", ""),
        "thumbnail": raw.get("thumbnail_url", ""),
        "url":       video_url,
        "source":    "youtube",
    }


# ── network entry point ─────────────────────────────────────────────────

def fetch_metadata(url: str) -> dict:
    """Fetch oEmbed metadata for a YouTube URL.

    Returns the reshaped dict on success. Fail-soft: returns
    {"error": "..."} on invalid URL, network error, or non-200.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": f"not a YouTube video URL: {url}"}

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = (
        "https://www.youtube.com/oembed"
        f"?url=https%3A//www.youtube.com/watch%3Fv%3D{video_id}"
        "&format=json"
    )
    req = urllib.request.Request(oembed_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {video_id}"}
    except urllib.error.URLError as e:
        return {"error": f"network error: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    try:
        raw = json.loads(body)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}"}

    return reshape_oembed(raw, canonical_url)


# ── Channel wrapper (for doctor registry) ────────────────────────────────

from .base import Channel  # noqa: E402 — circular-safe


class YoutubeChannel(Channel):
    """Doctor-facing wrapper. check() runs a real oEmbed probe."""

    name = "youtube"
    backends = ["oembed"]

    # dQw4w9WgXcQ is the canonical stable test video (Rick Astley).
    _PROBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def check(self, config=None):
        result = fetch_metadata(self._PROBE_URL)
        if "error" not in result:
            return ("ok", "oEmbed responds (metadata only)", "oembed")
        return ("warn", f"oEmbed: {result['error'][:60]}", None)
