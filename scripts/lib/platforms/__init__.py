"""platforms — stdlib-only platform ingestion layer for A-Wiki.

Adds platform-specific ingestion (Reddit RSS, YouTube oEmbed, Bilibili view,
Jina Reader fallback) that the generic curl/scrape-advanced.py path can't
handle safely. All backends use only no-auth public endpoints — no cookies,
no login, no unofficial scrapers (Iron Law #6).

Patterns adapted from Agent-Reach (MIT, 2026 Pnant/Panniantong):
  - ordered_backends 2-pass routing      (channels/base.py:29-70)
  - doctor per-channel resilience        (doctor.py:16-45)
  - Jina Reader fallback                 (channels/web.py:24-34)
Re-implemented to A-Wiki conventions: stdlib-only, fail-soft, no `rich` dep.

Fail-soft contract: every backend returns either:
  - A list[dict] of items on success (reddit, multi-item), OR
  - A dict with the item on success (youtube, bilibili, jina — single item)
  - A dict/list[dict] with an "error" key on failure (never raises).
"""
from __future__ import annotations

__all__ = ["BACKENDS", "get"]
