"""Shared notification module — Telegram bot API + alert rendering.

P2 refactor: extracted from scripts/hermes/morning-briefing.py so the
Observatory alerting path (and any future notifier) can reuse a single
send_telegram() instead of duplicating the bot-API call across scripts.

Token resolution order:
  1. process env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
  2. ~/hermes-secrets/.env (the Hermes private secrets file, gitignored)

Library
  load_tokens() -> (token, chat_id)
  send_telegram(message, parse_mode="HTML") -> bool
  send_alerts(alerts: list[dict]) -> bool   # renders a banner from alert dicts
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Private secrets file (gitignored; per-machine). Tests patch this path.
_SECRETS_PATH = Path(os.path.expanduser("~/hermes-secrets/.env"))


def _load_env_file(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file into a dict (mirrors morning-briefing)."""
    env: dict[str, str] = {}
    if path.exists():
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def load_tokens() -> tuple[str, str]:
    """Resolve (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).

    Process env wins over the secrets file so CI/dashboard overrides take
    precedence. Returns ("", "") if neither source has the token.
    """
    env = _load_env_file(_SECRETS_PATH)
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
    return token, chat


def send_telegram(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message via the Telegram bot API. Returns True on success.

    Falls back to printing the message to stdout when no token is configured
    (so callers can still see the output in dev/CI without a bot). Returns
    False on any failure — never raises (callers can ignore the result).
    """
    token, chat = load_tokens()
    if not token or not chat:
        print("Telegram not configured — printing to stdout:")
        print(message)
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"Telegram send failed: {e}")
        print(message)
        return False


def _format_alerts_banner(alerts: list[dict[str, Any]]) -> str:
    """Render alert dicts into a Telegram-friendly HTML banner.

    Alert dict shape (from alerts.evaluate_alerts): severity, subagent,
    pass_rate, count, fail, msg, action.
    """
    critical = [a for a in alerts if a.get("severity") == "critical"]
    warning = [a for a in alerts if a.get("severity") == "warning"]
    lines = [
        f"<b>🔬 Subagent Observatory Alert</b>",
        f"🚨 {len(critical)} critical · ⚠️ {len(warning)} warning",
        "",
    ]
    for a in critical:
        rate_pct = a.get("pass_rate", 0) * 100
        lines.append(
            f"🚨 <b>{a.get('subagent', '?')}</b> — pass_rate {rate_pct:.0f}% "
            f"({a.get('fail', 0)}/{a.get('count', 0)} failed)"
        )
        if a.get("action"):
            lines.append(f"   → {a['action']}")
    for a in warning:
        rate_pct = a.get("pass_rate", 0) * 100
        lines.append(
            f"⚠️ <b>{a.get('subagent', '?')}</b> — pass_rate {rate_pct:.0f}% "
            f"({a.get('fail', 0)}/{a.get('count', 0)} failed)"
        )
    return "\n".join(lines)


def send_alerts(alerts: list[dict[str, Any]]) -> bool:
    """Render + send a banner for a list of Observatory alerts.

    Empty list → return True without sending (nothing to notify, no error).
    """
    if not alerts:
        return True
    return send_telegram(_format_alerts_banner(alerts), parse_mode="HTML")


__all__ = ["load_tokens", "send_telegram", "send_alerts"]
