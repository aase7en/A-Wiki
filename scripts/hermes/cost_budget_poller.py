#!/usr/bin/env python3
"""
cost_budget_poller.py — Cost budget Telegram alert (V1).

อ่าน cost_history total_usd จาก dashboard → เทียบ threshold → ส่ง Telegram
alert เมื่อเกิน budget. ใช้ pattern เดียวกับ Q2 subagent_alert_poller:
  - idempotent state (.tmp/cost-budget-poller-state.json)
  - cooldown กัน spam (default 24h)
  - dry-run mode

Driven by: systemd timer / cron / manual (เหมือน Q2).

Usage:
  python3 scripts/hermes/cost_budget_poller.py --once              # single poll
  python3 scripts/hermes/cost_budget_poller.py --once --dry-run    # preview
  python3 scripts/hermes/cost_budget_poller.py --loop              # poll every hour
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from urllib.error import URLError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = REPO_ROOT / ".tmp" / "cost-budget-poller-state.json"
COST_ENDPOINT = os.environ.get("AWIKI_COST_ENDPOINT", "http://localhost:7790/api/eval/cost")

# Reuse Q2 notify (Telegram sender)
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from notify import send_telegram  # noqa: E402
except Exception:
    send_telegram = lambda msg, parse_mode="HTML": False  # noqa: E731


def _fetch_cost_data(url: str = COST_ENDPOINT) -> dict[str, Any]:
    """Fetch cost data from dashboard endpoint. Raises on error."""
    with urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_total_cost() -> float:
    """Fetch total_usd from dashboard. Returns 0.0 on any error."""
    try:
        data = _fetch_cost_data()
        return float(data.get("total_usd", 0.0))
    except Exception:
        return 0.0


def should_alert(
    total_usd: float,
    threshold: float,
    state: dict[str, float],
    cooldown: int,
    now: float,
    key: str = "monthly",
) -> tuple[bool, str]:
    """Decide whether to send a budget alert.

    Returns (alert, reason). Alert is True ถ้า:
      - total_usd > threshold AND
      - (ไม่เคย alert หรือ ผ่าน cooldown แล้ว)
    """
    if total_usd <= threshold:
        return False, f"under budget (${total_usd:.4f} ≤ ${threshold:.2f})"
    last_ts = state.get(key, 0)
    if last_ts == 0:
        return True, f"over budget (${total_usd:.4f} > ${threshold:.2f})"
    elapsed = now - last_ts
    if elapsed <= cooldown:
        return False, f"over budget but in cooldown ({cooldown - elapsed:.0f}s remaining)"
    return True, f"over budget (${total_usd:.4f} > ${threshold:.2f}), re-alert after cooldown"


def update_state(state: dict[str, float], key: str = "monthly", now: float = 0.0) -> None:
    """Record that we alerted at `now`."""
    state[key] = now


def build_alert_message(total_usd: float, threshold: float, period: str = "monthly") -> str:
    """Build the Telegram alert message."""
    pct = (total_usd / threshold * 100) if threshold > 0 else 0
    return (
        f"💰 <b>Cost Budget Alert</b>\n\n"
        f"<b>{period}</b> cost estimate: <b>${total_usd:.4f}</b>\n"
        f"Threshold: ${threshold:.2f}\n"
        f"Usage: {pct:.1f}% of budget\n\n"
        f"ดูรายละเอียดใน dashboard → 💰 Cost tab"
    )


def load_state() -> dict[str, float]:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(state: dict[str, float]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def run_once(
    threshold: float = 10.0,
    cooldown: int = 86400,
    dry_run: bool = False,
    key: str = "monthly",
    period: str = "monthly",
) -> bool:
    """Single poll cycle. Returns True ถ้า alerted (or would alert in dry_run)."""
    total = fetch_total_cost()
    now = time.time()
    state = load_state()
    alert, reason = should_alert(total, threshold, state, cooldown, now, key)
    if not alert:
        print(f"[cost-budget] {reason}")
        return False
    msg = build_alert_message(total, threshold, period)
    print(f"[cost-budget] ALERT: {reason}")
    if dry_run:
        print(f"[cost-budget] (dry-run) would send:\n{msg}")
        return True
    sent = send_telegram(msg)
    if sent:
        update_state(state, key, now)
        save_state(state)
        print("[cost-budget] ✓ Telegram alert sent")
    else:
        print("[cost-budget] ⚠️ Telegram send failed (token not configured?)")
    return sent


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="single poll cycle")
    g.add_argument("--loop", action="store_true", help="poll every hour (foreground)")
    p.add_argument("--threshold", type=float, default=float(os.environ.get("AWIKI_COST_THRESHOLD", "10.0")),
                   help="budget threshold in USD (default: $10)")
    p.add_argument("--cooldown", type=int, default=86400, help="cooldown seconds (default: 86400 = 24h)")
    p.add_argument("--dry-run", action="store_true", help="don't send Telegram, just print")
    p.add_argument("--interval", type=int, default=3600, help="loop interval seconds (default: 3600)")
    args = p.parse_args()

    if args.once:
        alerted = run_once(args.threshold, args.cooldown, args.dry_run)
        return 0 if alerted or not args.dry_run else 0

    # Loop mode
    print(f"[cost-budget] loop mode: threshold=${args.threshold}, cooldown={args.cooldown}s, interval={args.interval}s")
    while True:
        try:
            run_once(args.threshold, args.cooldown, args.dry_run)
        except Exception as e:
            print(f"[cost-budget] error: {e}")
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
