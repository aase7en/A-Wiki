"""bilibili_view.py — Bilibili video metadata reader (no-auth, no-cookie).

Endpoint verified alive 2026-08-01: https://api.bilibili.com/x/web-interface/view?bvid=<BV>
returns HTTP 200 + JSON with code:0, no auth required. Gives title, owner,
duration, pic (thumbnail), description. Comments need wbi-signing (Phase 2).

Public API:
  - extract_bvid(url) -> str | None        pure URL parser
  - reshape_view(raw, bvid) -> dict        reshape API JSON
  - fetch_metadata(url) -> dict            network entry point

Fail-soft: never raises. Returns {"error": "..."} on any failure
(invalid URL, code != 0, network error).
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

__all__ = ["extract_bvid", "reshape_view", "fetch_metadata", "USER_AGENT"]

USER_AGENT = "A-Wiki-PlatformIngestBot/1.0 (Bilibili; +https://github.com/aase7en/A-Wiki)"
TIMEOUT = 20

# BV ids are BV + 10 chars from [A-Za-z0-9]. We're conservative — require BV
# prefix so we don't accidentally match unrelated path segments.
_BVID_RE = re.compile(r"BV[1-9A-HJ-NP-Za-km-z]{10}")


# ── pure URL parser ───────────────────────────────────────────────────────

def extract_bvid(url: str) -> str | None:
    """Extract the BV id from any common Bilibili URL shape.

    Returns None for non-video URLs. Pure function — no I/O.
    """
    if not url or not isinstance(url, str):
        return None
    m = _BVID_RE.search(url)
    return m.group(0) if m else None


# ── reshape API JSON ────────────────────────────────────────────────────

def reshape_view(raw: dict, bvid: str) -> dict:
    """Reshape the raw Bilibili view JSON into a flat dict with stable keys.

    Tolerant of missing fields — returns "" / 0 rather than KeyError.
    """
    data = raw.get("data") or {}
    owner = data.get("owner") or {}
    return {
        "title":     data.get("title", ""),
        "author":    owner.get("name", ""),
        "bvid":      data.get("bvid") or bvid,
        "aid":       int(data.get("aid") or 0),
        "url":       f"https://www.bilibili.com/video/{data.get('bvid') or bvid}",
        "source":    "bilibili",
        "thumbnail": data.get("pic", ""),
    }


# ── network entry point ─────────────────────────────────────────────────

def fetch_metadata(url: str) -> dict:
    """Fetch video metadata for a Bilibili URL via the public view API.

    Returns the reshaped dict on success. Fail-soft: returns
    {"error": "..."} on invalid URL, code != 0, or network error.
    """
    bvid = extract_bvid(url)
    if not bvid:
        return {"error": f"not a Bilibili video URL: {url}"}

    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    # Referer is critical — Bilibili CDN sometimes 412s without it (verified).
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://www.bilibili.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {bvid}"}
    except urllib.error.URLError as e:
        return {"error": f"network error: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    try:
        raw = json.loads(body)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}"}

    if raw.get("code") != 0:
        msg = raw.get("message", "")
        return {"error": f"Bilibili code={raw.get('code')}: {msg}"}

    return reshape_view(raw, bvid)
