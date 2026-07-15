#!/usr/bin/env python3
"""Subagent alert poller — Q2 Telegram auto-alert for critical Observatory alerts.

Runs hourly on Pi5 via systemd timer (scripts/hermes/systemd/awiki-alert-poller.timer).
Fetches /api/subagents/alerts from the live dashboard, filters to critical-only,
and sends a Telegram banner via notify.send_alerts.

Idempotency: each subagent is alerted at most once per COOLDOWN_SECONDS (4h default)
to prevent spam. State is persisted to .tmp/subagent-alert-poller-state.json.

CLI:
  python3 subagent_alert_poller.py            # normal run (fetch + send)
  python3 subagent_alert_poller.py --once     # single poll, then exit
  python3 subagent_alert_poller.py --dry-run  # fetch + print, no Telegram send
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

from notify import send_alerts  # noqa: E402

DEFAULT_DASHBOARD_URL = os.environ.get(
    "AWIKI_DASHBOARD_URL", "http://localhost:7790")
ALERTS_ENDPOINT = f"{DEFAULT_DASHBOARD_URL}/api/subagents/alerts?since=3600"
STATE_FILE = REPO_ROOT / ".tmp" / "subagent-alert-poller-state.json"
COOLDOWN_SECONDS = 4 * 3600  # 4h — don't re-alert same subagent within this window
POLL_INTERVAL_SECONDS = 3600  # 1h (matches systemd OnCalendar=hourly)


# ---------------------------------------------------------------------------
# Pure helpers (testable without I/O)
# ---------------------------------------------------------------------------

def filter_critical(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only severity == 'critical' alerts."""
    return [a for a in alerts if a.get("severity") == "critical"]


def should_alert(
    alert: dict[str, Any],
    state: dict[str, float],
    cooldown: int,
    now: float,
) -> bool:
    """True if this alert's subagent hasn't been alerted within the cooldown.

    Boundary exclusive: alerted exactly `cooldown` seconds ago → still blocked
    (must be STRICTLY past the window). A subagent absent from state has never
    been alerted → always returns True (first-time alert).
    """
    subagent = alert.get("subagent", "")
    if subagent not in state:
        return True  # never alerted before
    last_ts = state[subagent]
    return (now - last_ts) > cooldown


def update_state(
    state: dict[str, float],
    alerts: list[dict[str, Any]],
    now: float,
) -> None:
    """Record the alert timestamp for each subagent in the alerts list."""
    for a in alerts:
        subagent = a.get("subagent", "")
        if subagent:
            state[subagent] = now


# ---------------------------------------------------------------------------
# State file I/O
# ---------------------------------------------------------------------------

def load_state() -> dict[str, float]:
    if not STATE_FILE.is_file():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, float]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# HTTP fetch (mockable)
# ---------------------------------------------------------------------------

def fetch_alerts(url: str = ALERTS_ENDPOINT) -> dict[str, Any]:
    """Fetch the alerts JSON from the dashboard endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"[alert-poller] fetch failed ({url}): {e}", file=sys.stderr)
        return {"alerts": [], "summary": {}}


# ---------------------------------------------------------------------------
# Main logic (run_once — testable with mocked fetch + send)
# ---------------------------------------------------------------------------

def run_once(
    cooldown: int = COOLDOWN_SECONDS,
    now: float | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Single poll cycle. Returns {sent, skipped, total_critical}."""
    now_ts = now if now is not None else time.time()
    data = fetch_alerts()
    all_alerts = data.get("alerts", [])
    critical = filter_critical(all_alerts)

    state = load_state()
    to_send = [a for a in critical if should_alert(a, state, cooldown, now_ts)]
    skipped = len(critical) - len(to_send)

    if dry_run:
        print(f"[dry-run] {len(critical)} critical, {len(to_send)} to send, "
              f"{skipped} skipped (cooldown).")
        for a in to_send:
            print(f"  → {a.get('subagent')}: {a.get('msg')}")
        return {"sent": 0, "skipped": skipped, "total_critical": len(critical)}

    sent = 0
    if to_send:
        if send_alerts(to_send):
            sent = len(to_send)
            update_state(state, to_send, now_ts)
            save_state(state)
        else:
            print("[alert-poller] send_alerts returned False (Telegram not "
                  "configured or failed) — state not updated.", file=sys.stderr)

    return {"sent": sent, "skipped": skipped, "total_critical": len(critical)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--once", action="store_true",
                   help="run a single poll cycle and exit (default for systemd timer)")
    p.add_argument("--dry-run", action="store_true",
                   help="fetch + print, do not send Telegram")
    p.add_argument("--loop", action="store_true",
                   help="poll continuously every POLL_INTERVAL_SECONDS (foreground)")
    p.add_argument("--cooldown", type=int, default=COOLDOWN_SECONDS,
                   help=f"cooldown per subagent in seconds (default {COOLDOWN_SECONDS})")
    args = p.parse_args()

    if args.loop:
        print(f"[alert-poller] loop mode — polling every {POLL_INTERVAL_SECONDS}s. "
              f"Ctrl+C to stop.")
        while True:
            try:
                result = run_once(cooldown=args.cooldown)
                print(f"[alert-poller] sent={result['sent']} "
                      f"skipped={result['skipped']} "
                      f"critical={result['total_critical']}")
            except Exception as e:
                print(f"[alert-poller] error: {e}", file=sys.stderr)
            time.sleep(POLL_INTERVAL_SECONDS)
        return 0  # unreachable (infinite loop)

    # Default: single poll (--once is the default behavior for systemd).
    result = run_once(cooldown=args.cooldown, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"[alert-poller] sent={result['sent']} "
              f"skipped={result['skipped']} "
              f"critical={result['total_critical']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
