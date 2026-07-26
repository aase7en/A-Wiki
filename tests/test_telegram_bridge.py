"""Tests for scripts/lib/telegram_bridge.py — bidirectional blackboard ↔ Telegram.

Iron Law #1: failing tests written FIRST.

telegram_bridge ทำ 2 ทิศทาง:
  1. blackboard → Telegram: เมื่อมี message ใหม่ใน blackboard (เช่น council
     critical, needs-review) → ส่งไป Telegram เพื่อ user เห็นจากมือถือ
  2. Telegram → blackboard: เมื่อ user reply ใน Telegram → เขียนเข้า blackboard
     เป็น type=msg (ให้ agents อ่านตอน poll)

ไม่ต้องการ Telegram bot token จริงในการทดสอบ — ใช้ injectable sender.
Reuses scripts/hermes/notify.py:send_telegram pattern (inject for test).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import blackboard as bb  # noqa: E402
import telegram_bridge as tb  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. format_message_for_telegram — render blackboard msg as Telegram text
# ---------------------------------------------------------------------------
def test_format_renders_basic_message():
    msg = {
        "from": "claude", "to": "codex", "type": "question",
        "body": "what about X?", "ts": 1785000000.0,
    }
    text = tb.format_message_for_telegram(msg)
    assert "claude" in text
    assert "codex" in text
    assert "what about X?" in text
    assert "question" in text.lower()


def test_format_includes_critical_badge():
    msg = {
        "from": "security-auditor", "to": "*", "type": "answer",
        "body": "sql injection found", "tags": ["council", "critical"],
    }
    text = tb.format_message_for_telegram(msg)
    assert "CRITICAL" in text or "critical" in text.lower()


def test_format_includes_needs_review_badge():
    msg = {
        "from": "auto-council", "to": "*", "type": "proposal",
        "body": "review auth.py", "tags": ["council", "needs-review"],
    }
    text = tb.format_message_for_telegram(msg)
    assert "REVIEW" in text.upper() or "needs-review" in text.lower()


# ---------------------------------------------------------------------------
# 2. should_forward — filter rules (don't forward everything)
# ---------------------------------------------------------------------------
def test_should_forward_critical():
    msg = {"tags": ["council", "critical"]}
    assert tb.should_forward(msg) is True


def test_should_forward_needs_review():
    msg = {"tags": ["council", "needs-review"]}
    assert tb.should_forward(msg) is True


def test_should_forward_question_to_user():
    msg = {"to": "user", "type": "question"}
    assert tb.should_forward(msg) is True


def test_should_not_forward_routine_msg():
    """Routine msg between agents (no critical/review/user) → skip (noise)."""
    msg = {"to": "codex", "type": "msg", "body": "ok", "tags": []}
    assert tb.should_forward(msg) is False


# ---------------------------------------------------------------------------
# 3. forward_new_messages — send blackboard msgs since last_ts to Telegram
# ---------------------------------------------------------------------------
def test_forward_new_messages_calls_sender(tmp_path):
    """Messages since since_ts that pass should_forward → sender called."""
    bb_path = tmp_path / "bb.jsonl"
    board = bb.Blackboard(bb_path)
    board.post(frm="security-auditor", to="*", body="sql injection",
               msg_type="answer")  # has no critical tag yet, but we'll add
    # Augment with critical tag
    import json
    lines = bb_path.read_text(encoding="utf-8").splitlines()
    last = json.loads(lines[-1])
    last["tags"] = ["council", "critical"]
    lines[-1] = json.dumps(last, ensure_ascii=False)
    bb_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    sent = []
    def fake_send(text):
        sent.append(text)
        return True

    n = tb.forward_new_messages(bb_path, since_ts=0, sender=fake_send)
    assert n >= 1
    assert len(sent) >= 1
    assert "sql injection" in sent[0]


def test_forward_returns_zero_when_nothing_to_send(tmp_path):
    """No messages match should_forward → 0 sent."""
    bb_path = tmp_path / "bb.jsonl"
    bb.Blackboard(bb_path).post(frm="a", to="b", body="routine", msg_type="msg")
    sent = []
    n = tb.forward_new_messages(bb_path, since_ts=0,
                                 sender=lambda t: sent.append(t) or True)
    assert n == 0
    assert sent == []


# ---------------------------------------------------------------------------
# 4. parse_telegram_reply — convert Telegram text → blackboard msg dict
# ---------------------------------------------------------------------------
def test_parse_reply_basic():
    """Plain reply text → {frm:user, to:*, body:text, type:msg}."""
    msg = tb.parse_telegram_reply(text="please fix the auth bug first")
    assert msg["frm"] == "user"
    assert msg["to"] == "*"
    assert msg["type"] == "msg"
    assert "auth bug" in msg["body"]


def test_parse_reply_with_mention():
    """@codex prefix → routes to specific agent."""
    msg = tb.parse_telegram_reply(text="@codex can you check the test?")
    assert msg["to"] == "codex"
    assert "check the test" in msg["body"]


def test_parse_reply_question_mark():
    """Text ending with '?' → type=question."""
    msg = tb.parse_telegram_reply(text="is the deploy done?")
    assert msg["type"] == "question"


# ---------------------------------------------------------------------------
# 5. write_reply_to_blackboard — append parsed reply to blackboard.jsonl
# ---------------------------------------------------------------------------
def test_write_reply_appends_to_blackboard(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    parsed = {"frm": "user", "to": "*", "body": "ship it", "type": "msg"}
    msg_id = tb.write_reply_to_blackboard(bb_path, parsed)
    assert msg_id is not None
    msgs = bb.Blackboard(bb_path).read()
    assert len(msgs) == 1
    assert msgs[0]["body"] == "ship it"
    assert msgs[0]["from"] == "user"  # blackboard uses 'from' not 'frm'


# ---------------------------------------------------------------------------
# 6. injectable sender — works with scripts/hermes/notify.py:send_telegram
# ---------------------------------------------------------------------------
def test_default_sender_is_notify_send_telegram():
    """When no sender provided, default to scripts/hermes/notify.py:send_telegram.

    This wires the bridge into the existing Telegram bot infra without
    duplicating API code.
    """
    sender = tb.default_sender()
    assert callable(sender)
