"""jina_reader.py — last-resort URL → Markdown fallback (no-auth).

Adapted from Agent-Reach channels/web.py:24-34 (MIT, 2026
Pnant/Panniantong) — re-implemented to A-Wiki conventions (fail-soft,
explicit User-Agent, no third-party deps).

Endpoint: https://r.jina.ai/{url} — Jina's free public Reader API that
converts any URL to clean Markdown. Used as the universal fallback when
no platform-specific backend matches.

Public API:
  - read(url) -> str | dict   returns Markdown text, or {"error": ...} on failure

Fail-soft: never raises.
"""
from __future__ import annotations

import urllib.error
import urllib.request

__all__ = ["read", "USER_AGENT", "JINA_PREFIX"]

USER_AGENT = "A-Wiki-PlatformIngestBot/1.0 (Jina Reader; +https://github.com/aase7en/A-Wiki)"
JINA_PREFIX = "https://r.jina.ai/"
TIMEOUT = 30


def read(url: str) -> str | dict:
    """Fetch a URL via Jina Reader and return Markdown.

    Normalizes the scheme: if `url` lacks http:// or https://, prepends
    https:// (matching Agent-Reach's web.py normalization).

    Returns Markdown text on success. Fail-soft: returns {"error": ...}
    on network error or non-200.
    """
    if not url or not isinstance(url, str):
        return {"error": "empty url"}

    target = url.strip()
    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    jina_url = JINA_PREFIX + target
    req = urllib.request.Request(
        jina_url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {url}"}
    except urllib.error.URLError as e:
        return {"error": f"network error: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
