"""Tests for scripts/hermes/notify.py — shared Telegram notification module.

P2 refactor: extract send_telegram() from morning-briefing.py into a reusable
module so the Observatory alerting path can notify on critical alerts without
duplicating the bot-API call. The HTTP layer is isolated so tests can mock
urlopen without touching the network.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

import notify  # noqa: E402


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------

def test_missing_token_returns_false(capsys, monkeypatch):
    """No TELEGRAM_BOT_TOKEN → return False, fall back to stdout print."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))
    result = notify.send_telegram("hello")
    assert result is False
    out = capsys.readouterr().out
    assert "hello" in out  # message was printed


def test_token_from_process_env(monkeypatch):
    """Process-env tokens take precedence over the secrets file."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "envtok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "envchat")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["data"] = req.data.decode()
        return FakeResp()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert notify.send_telegram("hi") is True
    assert "envtok" in captured["url"]


# ---------------------------------------------------------------------------
# HTTP call construction
# ---------------------------------------------------------------------------

def test_send_telegram_uses_bot_api_url(monkeypatch):
    """URL must be https://api.telegram.org/bot<TOKEN>/sendMessage."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat456")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["data"] = req.data.decode()
        return FakeResp()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify.send_telegram("test msg")
    assert captured["url"] == "https://api.telegram.org/bottok123/sendMessage"


def test_send_telegram_includes_chat_id_and_message(monkeypatch):
    """Payload must encode chat_id + text so Telegram routes the message."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: (captured.__setitem__("data", req.data.decode()) or FakeResp()))
    notify.send_telegram("hello world")
    import urllib.parse
    parsed = dict(urllib.parse.parse_qsl(captured["data"]))
    assert parsed["chat_id"] == "12345"
    assert parsed["text"] == "hello world"


def test_parse_mode_default_html(monkeypatch):
    """Default parse_mode is HTML (matches morning-briefing.py behavior)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    import urllib.request
    import urllib.parse
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: (captured.__setitem__("data", req.data.decode()) or FakeResp()))
    notify.send_telegram("hi")
    parsed = dict(urllib.parse.parse_qsl(captured["data"]))
    assert parsed["parse_mode"] == "HTML"


# ---------------------------------------------------------------------------
# Return value + error handling
# ---------------------------------------------------------------------------

def test_returns_true_on_ok_response(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: FakeResp())
    assert notify.send_telegram("hi") is True


def test_returns_false_on_http_error(monkeypatch, capsys):
    """Network/HTTP error → return False, do NOT raise."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: (_ for _ in ()).throw(RuntimeError("net fail")))
    result = notify.send_telegram("hi")
    assert result is False


def test_send_alerts_formats_banner(monkeypatch):
    """send_alerts(alerts) renders a Telegram-friendly banner from alert dicts."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(notify, "_SECRETS_PATH", Path("/nonexistent/.env"))

    captured = {}

    def fake_send(message, parse_mode="HTML"):
        captured["message"] = message
        captured["parse_mode"] = parse_mode
        return True

    monkeypatch.setattr(notify, "send_telegram", fake_send)

    alerts = [
        {"severity": "critical", "subagent": "finance-analyst",
         "pass_rate": 0.4, "count": 10, "fail": 6,
         "msg": "finance-analyst: pass_rate=40%", "action": "reroute"},
        {"severity": "warning", "subagent": "code-architect",
         "pass_rate": 0.8, "count": 10, "fail": 2,
         "msg": "code-architect: pass_rate=80%", "action": "eval"},
    ]
    result = notify.send_alerts(alerts)
    assert result is True
    msg = captured["message"]
    assert "🚨" in msg or "critical" in msg.lower()
    assert "finance-analyst" in msg
    assert "code-architect" in msg


def test_send_alerts_empty_returns_true_no_send(monkeypatch):
    """No alerts → no send needed, but return True (no error)."""
    called = {"n": 0}

    def fake_send(msg, parse_mode="HTML"):
        called["n"] += 1
        return True

    monkeypatch.setattr(notify, "send_telegram", fake_send)
    assert notify.send_alerts([]) is True
    assert called["n"] == 0  # no message sent
