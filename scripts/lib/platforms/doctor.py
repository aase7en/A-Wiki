"""doctor.py — platform-ingest health-check orchestrator.

The doctor concept is borrowed from Agent-Reach (doctor.py:16-45, MIT, 2026
Pnant/Panniantong) — re-implemented for A-Wiki with three deliberate
differences (Agent-ReachTrap #1):

1. Ours ACTUALLY runs a real HTTP probe. Agent-Reach's doctor refuses to
   execute upstream commands (to avoid their auto-cookie-fallback policy)
   and reports nearly everything as "warn". That's fine for a system that
   wraps cookie-based CLIs — it would be wrong for ours, which hits
   no-auth public endpoints where a live probe is safe and informative.

2. No `rich` dependency. Plain text, no ANSI escapes (cross-platform,
   grep-friendly, JSON-friendly).

3. Reports dict[name -> status_dict] instead of formatted tables. The
   rendering is a separate function (render_text) — agents that want JSON
   can bypass it.

Public API:
  - probe(channel) -> status_dict         single-channel probe
  - check_all(channels=None) -> dict       default registry = BACKENDS
  - render_text(report) -> str             plain-text table (no color codes)
"""
from __future__ import annotations

from typing import Any

from .base import Channel

__all__ = ["probe", "check_all", "render_text"]


# ── single-channel probe ────────────────────────────────────────────────

def probe(channel: Channel, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Probe a single channel and return its status_dict.

    Catches exceptions inside channel.check() — never raises.
    """
    try:
        status, message, active = channel.check(config)
    except Exception as exc:
        status, message, active = "error", f"{type(exc).__name__}: {exc}", None
    return {
        "status": status,
        "message": message,
        "active_backend": active,
    }


# ── batch probe ─────────────────────────────────────────────────────────

def check_all(
    channels: list[Channel] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Probe every channel and return a per-channel status dict.

    Default registry is the package-level BACKENDS (lazy import to avoid
    circular imports at module load time). One broken channel must not
    abort the report.
    """
    if channels is None:
        # Lazy import — BACKENDS imports the backend modules which import base.
        from . import BACKENDS
        channels = list(BACKENDS.values())

    report: dict[str, dict[str, Any]] = {}
    for ch in channels:
        report[ch.name] = probe(ch, config)
    return report


# ── plain-text renderer ─────────────────────────────────────────────────

def render_text(report: dict[str, dict[str, Any]]) -> str:
    """Render a status report as plain text. No ANSI/rich color codes.

    Format:
      summary:  N ok · M warn · K error
      <name>      <status>   <active_backend>   <message>
    """
    counts = {"ok": 0, "warn": 0, "error": 0}
    for entry in report.values():
        status = entry.get("status", "error")
        if status in counts:
            counts[status] += 1

    lines = [
        f"summary:  {counts['ok']} ok · {counts['warn']} warn · {counts['error']} error",
        "",
    ]
    # Name column width = longest name, min 8
    name_w = max([len(n) for n in report], default=8)
    name_w = max(name_w, 8)
    for name, entry in report.items():
        status = entry.get("status", "error")
        active = entry.get("active_backend") or "-"
        # splitlines on "" gives [], so guard first line access.
        raw_msg = entry.get("message") or ""
        first_line = raw_msg.splitlines()[0] if raw_msg.splitlines() else ""
        message = first_line[:60]
        lines.append(f"{name:<{name_w}}  {status:<6}  {active:<18}  {message}")
    return "\n".join(lines)
