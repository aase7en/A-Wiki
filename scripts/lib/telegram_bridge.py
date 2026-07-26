"""telegram_bridge.py — bidirectional Blackboard ↔ Telegram bridge.

Tier 3 #10. Lets user participate in agent conversations (council, A-Loop)
from their phone via the existing Hermes Telegram bot on Pi5.

Two directions:
  1. blackboard → Telegram: forward critical/needs-review/user questions
     to Telegram so user sees them on mobile (filter rules — not all msgs)
  2. Telegram → blackboard: when user replies in Telegram, write it into
     blackboard as a regular message (agents pick it up via bb_read)

Reuses scripts/hermes/notify.py:send_telegram for the actual API call
(no duplication of bot code). Sender is injectable for tests.

API:
  format_message_for_telegram(msg)         → str (rendered text)
  should_forward(msg)                      → bool (filter rules)
  forward_new_messages(bb_path, since_ts, sender) → int (count sent)
  parse_telegram_reply(text)               → dict (blackboard msg shape)
  write_reply_to_blackboard(bb_path, parsed) → str (msg_id)
  default_sender()                         → callable (notify.send_telegram)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blackboard  # noqa: E402 -- Neural Spine chunk 4


def format_message_for_telegram(msg: dict) -> str:
    """Render a blackboard message as Telegram-friendly text.

    Includes badges for critical/needs-review tags so user sees urgency.
    """
    frm = msg.get("from", "?")
    to = msg.get("to", "*")
    mtype = msg.get("type", "msg")
    body = msg.get("body", "")
    tags = msg.get("tags", [])
    ts = msg.get("ts")

    badges = []
    if "critical" in tags:
        badges.append("🔴 CRITICAL")
    if "needs-review" in tags:
        badges.append("⚠️ NEEDS REVIEW")
    if "council" in tags:
        badges.append("🏛️")

    badge_str = f" [{' '.join(badges)}]" if badges else ""

    time_str = ""
    if ts:
        try:
            time_str = time.strftime("%H:%M", time.localtime(ts))
        except Exception:
            pass

    target = to if to != "*" else "all"
    return f"{badge_str} [{time_str}] <b>{frm}</b> → {target} ({mtype})\n{body}"


def should_forward(msg: dict) -> bool:
    """Decide whether a blackboard message should be forwarded to Telegram.

    Filter rules (any one is enough):
      - has 'critical' tag (security/crash)
      - has 'needs-review' tag (auto-council awaiting input)
      - addressed to 'user' (direct question)
      - type=proposal with 'council' tag (new council opened)
    Routine agent-to-agent chatter is NOT forwarded (noise reduction).
    """
    tags = msg.get("tags", []) or []
    if "critical" in tags:
        return True
    if "needs-review" in tags:
        return True
    if msg.get("to") == "user":
        return True
    if msg.get("type") == "proposal" and "council" in tags:
        return True
    return False


def forward_new_messages(
    bb_path: Path | str,
    *,
    since_ts: float = 0.0,
    sender: Callable[[str], bool] | None = None,
) -> int:
    """Forward new blackboard messages (since since_ts) to Telegram.

    Uses should_forward() to filter. Returns count of messages actually sent.
    Sender defaults to scripts/hermes/notify.py:send_telegram.
    """
    if sender is None:
        sender = default_sender()
    board = blackboard.Blackboard(bb_path)
    msgs = board.read(since_ts=since_ts, limit=200)
    sent = 0
    for m in msgs:
        if not should_forward(m):
            continue
        text = format_message_for_telegram(m)
        try:
            if sender(text):
                sent += 1
        except Exception:
            pass  # never crash on send failure
    return sent


def parse_telegram_reply(text: str) -> dict:
    """Parse a Telegram reply into a blackboard message dict.

    Rules:
      - '@agent' prefix → routes to that agent (else broadcast '*')
      - text ending with '?' → type=question (else type=msg)
      - sender is always 'user' (the human replying)
    """
    text = text or ""
    body = text.strip()
    target = "*"
    # @mention detection
    if body.startswith("@"):
        parts = body.split(None, 1)
        if parts:
            target = parts[0][1:].lower()  # strip '@'
            body = parts[1] if len(parts) > 1 else ""
    mtype = "question" if body.rstrip().endswith("?") else "msg"
    return {
        "frm": "user",
        "to": target,
        "body": body,
        "type": mtype,
    }


def write_reply_to_blackboard(
    bb_path: Path | str,
    parsed: dict,
) -> str:
    """Append a parsed Telegram reply to blackboard.jsonl.

    Returns the new message id.
    """
    board = blackboard.Blackboard(bb_path)
    return board.post(
        frm=parsed.get("frm", "user"),
        to=parsed.get("to", "*"),
        body=parsed.get("body", ""),
        msg_type=parsed.get("type", "msg"),
    )


def default_sender() -> Callable[[str], bool]:
    """Return the default Telegram sender (scripts/hermes/notify.py:send_telegram).

    Falls back to a no-op print sender if notify.py is unavailable (e.g.
    during tests or on machines without Hermes installed).
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hermes"))
        from notify import send_telegram  # type: ignore
        return send_telegram
    except Exception:
        def _fallback_print(text: str) -> bool:
            print(f"[telegram_bridge:fallack] {text[:80]}")
            return True
        return _fallback_print
