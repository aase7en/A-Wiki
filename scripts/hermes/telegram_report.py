#!/usr/bin/env python3
"""Telegram report sender — chunks the ENTIRE report, never truncates.

R-P1-002 (vNext Phase 1 remediation): the P1.5 inline sender in
provider-balance.yml computed chunks over `min(len(text), 4000)` — silently
discarding everything past 4,000 characters. This helper splits the whole
report into ordered parts, each fitting Telegram's 4,096-char message limit
including header/prefix and (i/n) suffix framing.

Usage (CLI):
  python3 scripts/hermes/telegram_report.py --file report.md --header "☁️ Title"
  TG_CHAT / TG_TOKEN env vars (or --chat/--token flags) provide credentials.

Usage (library):
  from telegram_report import chunk_report
  messages = chunk_report(text, header="☁️ Title")   # list[str]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

TELEGRAM_HARD_LIMIT = 4096  # Telegram sendMessage hard cap
DEFAULT_CHUNK = 3600        # leaves >= 400 chars of framing headroom


def chunk_report(text: str, header: str = "", chunk_size: int = DEFAULT_CHUNK) -> list[str]:
    """Split the ENTIRE report into ordered Telegram messages.

    Guarantees:
      - concatenating the payload parts (header/suffix stripped) == text
      - each message length <= TELEGRAM_HARD_LIMIT for sane chunk sizes
      - a non-empty report never produces an empty message list
    """
    if chunk_size + len(header) + 32 > TELEGRAM_HARD_LIMIT:
        raise ValueError(
            f"chunk_size {chunk_size} + header {len(header)} leaves no framing headroom "
            f"under Telegram's {TELEGRAM_HARD_LIMIT}-char limit"
        )
    parts = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
    total = len(parts)
    prefix = f"{header}\n\n" if header else ""
    messages = []
    for i, part in enumerate(parts, 1):
        suffix = f"\n\n({i}/{total})" if total > 1 else ""
        messages.append(f"{prefix}{part}{suffix}")
    return messages


def send_messages(token: str, chat: str, messages: list[str], timeout: int = 30) -> int:
    """POST each message via the Bot API; returns the number sent."""
    sent = 0
    for msg in messages:
        body = json.dumps({"chat_id": chat, "text": msg}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=timeout).read()
        sent += 1
    return sent


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a report file to Telegram in full (chunked)")
    parser.add_argument("--file", required=True, help="path to the report (utf-8 text)")
    parser.add_argument("--header", default="", help="title prepended to every message")
    parser.add_argument("--chunk", type=int, default=DEFAULT_CHUNK)
    parser.add_argument("--chat", default=os.environ.get("TG_CHAT", ""))
    parser.add_argument("--token", default=os.environ.get("TG_TOKEN", ""))
    parser.add_argument("--dry-run", action="store_true", help="chunk only; print message count")
    args = parser.parse_args()

    if not args.chat or not args.token:
        print("ERROR: --chat/--token (or TG_CHAT/TG_TOKEN env) required", file=sys.stderr)
        return 2

    text = Path(args.file).read_text(encoding="utf-8")
    messages = chunk_report(text, header=args.header, chunk_size=args.chunk)

    if args.dry_run:
        print(f"dry-run: {len(messages)} message(s), "
              f"payload {len(text)} chars, max message {max(len(m) for m in messages)} chars")
        return 0

    sent = send_messages(args.token, args.chat, messages)
    print(f"telegram: posted {sent}/{len(messages)} message(s)")
    return 0 if sent == len(messages) else 1


if __name__ == "__main__":
    sys.exit(main())
