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

BACKENDS: dict[name -> Channel instance]. Used by doctor.check_all() as the
default registry. Lazy-populated on first access to avoid import cycles
(each backend module imports .base at its bottom).

Fail-soft contract: every backend returns either:
  - A list[dict] of items on success (reddit, multi-item), OR
  - A dict with the item on success (youtube, bilibili, jina — single item)
  - A dict/list[dict] with an "error" key on failure (never raises).
"""
from __future__ import annotations

from typing import Any

__all__ = ["BACKENDS", "get"]


# Lazy registry. backend modules import .base at their tail, and .base has
# no deps on the backends, so the cycle is safe — but populating at import
# time would still force every backend module to load even if the caller
# only wants one. Lazy dict keeps the cheap path cheap.
class _LazyBackends(dict):
    _loaded = False

    def _ensure(self) -> None:
        if self._loaded:
            return
        from .reddit_rss import RedditChannel
        from .youtube_oembed import YoutubeChannel
        from .bilibili_view import BilibiliChannel
        from .jina_reader import JinaChannel
        self.update({
            "reddit":   RedditChannel(),
            "youtube":  YoutubeChannel(),
            "bilibili": BilibiliChannel(),
            "jina":     JinaChannel(),
        })
        self._loaded = True

    def __contains__(self, key: object) -> bool:
        self._ensure()
        return super().__contains__(key)

    def __getitem__(self, key: str) -> Any:
        self._ensure()
        return super().__getitem__(key)

    def values(self):  # type: ignore[override]
        self._ensure()
        return super().values()

    def keys(self):  # type: ignore[override]
        self._ensure()
        return super().keys()

    def items(self):  # type: ignore[override]
        self._ensure()
        return super().items()

    def __iter__(self):
        self._ensure()
        return super().__iter__()

    def __len__(self) -> int:
        self._ensure()
        return super().__len__()


BACKENDS: dict[str, Any] = _LazyBackends()


def get(name: str) -> Any:
    """Return the Channel instance for `name`, or None if unknown."""
    return BACKENDS.get(name)
