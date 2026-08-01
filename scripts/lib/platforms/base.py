"""base.py — Channel ABC + ordered_backends routing + check_all resilience.

This module is the routing primitive for the platform-ingest layer. The
ordered-backends-with-override pattern is adapted from Agent-Reach
(channels/base.py:29-70, MIT, 2026 Pnant/Panniantong) — re-implemented to
A-Wiki conventions: no third-party deps, plain ABC, narrower scope.

Why an ABC + registry, not a free function per backend?
  Each backend has (1) a list of candidate endpoints to try in order,
  (2) a per-channel health probe, and (3) a way to report its status.
  Encoding those three things on one type lets doctor.check_all() iterate
  them uniformly. The override hook (config[f"{name}_backend"]) lets an
  operator pin a fallback to the front without editing code.

Public API:
  - Channel (ABC)            base type for backends
  - check_all(channels)      resilient per-channel probe → dict report

Fail-soft: check_all must never raise. A channel whose check() raises is
reported with status="error" but does NOT abort the whole report
(resilience pattern from Agent-Reach doctor.py:16-45).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["Channel", "check_all"]


# ── Channel ABC ──────────────────────────────────────────────────────────

class Channel(ABC):
    """Base type for a platform ingestion channel.

    Subclasses set:
      name      str       identifier used in config keys + reports
      backends  list[str] ordered candidate endpoints/tools

    Subclasses implement:
      check(config=None) -> (status, message, active_backend)

    The `check()` contract is a 3-tuple (status, message, active_backend):
      status           "ok" | "warn" | "error"
      message          human-readable detail (one line)
      active_backend   the backend that responded, or None if none
    """

    name: str = ""
    backends: list[str] = []

    @abstractmethod
    def check(self, config: dict[str, Any] | None = None) -> tuple[str, str, str | None]:
        ...

    def ordered_backends(self, config: dict[str, Any] | None = None) -> list[str]:
        """Return candidate backends in the order they should be tried.

        The declared order is preserved unless config has a
        `f"{self.name}_backend"` override key — in which case the matching
        backend is promoted to the front. If the override does not match
        any declared backend, it is ignored (fall back to declared order).
        """
        candidates = list(self.backends)
        if not config:
            return candidates
        override = config.get(f"{self.name}_backend")
        if not override:
            return candidates
        for i, b in enumerate(candidates):
            if b == override or b.startswith(override):
                candidates.insert(0, candidates.pop(i))
                break
        return candidates


# ── check_all resilience ─────────────────────────────────────────────────

def check_all(
    channels: list[Channel],
    config: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Probe every channel and return a per-channel status dict.

    Resilient: if a channel's check() raises, that channel is reported as
    status="error" but does NOT abort the iteration. Other channels still
    get probed and reported.

    Returns dict[name -> {"status", "message", "active_backend"}].
    """
    report: dict[str, dict[str, Any]] = {}
    for ch in channels:
        try:
            status, message, active = ch.check(config)
        except Exception as exc:  # one broken channel must not kill the report
            status, message, active = "error", f"{type(exc).__name__}: {exc}", None
        report[ch.name] = {
            "status": status,
            "message": message,
            "active_backend": active,
        }
    return report
