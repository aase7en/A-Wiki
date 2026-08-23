"""live_docs.py — Slice C: fetch LIVE upstream docs for the grill stage.

Skills declare `docs: <raw-markdown-url>` in SKILL.md frontmatter.
fetch_doc() returns one of:

  live         — fetched now (and cached)
  cache        — served from fresh cache (TTL 7 days)
  cache-stale  — fetch failed but an old cache exists (marked stale!)
  unavailable  — fetch failed, nothing cached (content="", reason set)

Never raises: grilling must proceed offline with an honest label.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Callable

TTL_SECONDS = 7 * 86400
_TIMEOUT = 15


def _cache_path(url: str, cache_dir: Path) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    d = Path(cache_dir) / "docs-cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def _default_get(url: str, timeout: int) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def fetch_doc(url: str, cache_dir: Path,
              http_get: Callable[[str, int], str] | None = None) -> dict:
    get = http_get or _default_get
    cp = _cache_path(url, cache_dir)
    cached = None
    if cp.is_file():
        try:
            cached = json.loads(cp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cached = None

    fresh = cached is not None and (
        time.time() - cached.get("fetched_at", 0) <= TTL_SECONDS)
    if fresh:
        return {"source": "cache", "content": cached["content"],
                "url": url, "fetched_at": cached["fetched_at"]}

    try:
        content = get(url, _TIMEOUT)
    except Exception as e:  # offline / 404 / timeout — never crash the grill
        if cached:
            return {"source": "cache-stale", "content": cached["content"],
                    "url": url, "fetched_at": cached["fetched_at"],
                    "reason": f"fetch failed: {e}"}
        return {"source": "unavailable", "content": "", "url": url,
                "reason": f"fetch failed: {e}"}

    now = round(time.time(), 3)
    cp.write_text(json.dumps({"url": url, "content": content,
                               "fetched_at": now}, ensure_ascii=False),
                  encoding="utf-8")
    return {"source": "live", "content": content, "url": url,
            "fetched_at": now}


def skill_docs_url(skill_md: Path) -> str | None:
    """`docs:` frontmatter field of a SKILL.md (None when absent)."""
    try:
        text = Path(skill_md).read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    for line in m.group(1).splitlines():
        mm = re.match(r"^docs:\s*(\S+)\s*$", line.strip())
        if mm:
            return mm.group(1)
    return None
