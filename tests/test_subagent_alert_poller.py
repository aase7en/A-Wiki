"""Tests for scripts/hermes/subagent_alert_poller.py — Q2 Telegram auto-alert.

The poller runs hourly on Pi5 (systemd timer), fetches /api/subagents/alerts,
filters to critical-only, and sends a Telegram banner via notify.send_alerts.
Idempotency is enforced via a state file: each subagent is alerted at most
once per cooldown window (4h default) to prevent spam.

Pure helpers (should_alert, filter_critical) are tested here; the HTTP +
Telegram I/O is mocked.
"""
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

import subagent_alert_poller as sap  # noqa: E402


def _alert(severity, subagent, ts=1000):
    return {"severity": severity, "subagent": subagent, "pass_rate": 0.4,
            "count": 10, "fail": 6, "msg": f"{subagent} low", "action": "reroute"}


# ---------------------------------------------------------------------------
# filter_critical — keep only severity == "critical"
# ---------------------------------------------------------------------------

def test_filter_critical_keeps_only_critical():
    alerts = [
        _alert("critical", "a"),
        _alert("warning", "b"),
        _alert("critical", "c"),
    ]
    out = sap.filter_critical(alerts)
    assert len(out) == 2
    assert all(a["severity"] == "critical" for a in out)
    assert {a["subagent"] for a in out} == {"a", "c"}


def test_filter_critical_empty():
    assert sap.filter_critical([]) == []
    assert sap.filter_critical([_alert("warning", "x")]) == []


# ---------------------------------------------------------------------------
# should_alert — idempotency via state + cooldown
# ---------------------------------------------------------------------------

def test_should_alert_first_time():
    """No prior state for this subagent → alert (first time seeing it)."""
    state = {}  # empty
    now = 5000
    cooldown = 4 * 3600  # 4h
    assert sap.should_alert(_alert("critical", "x", ts=5000), state, cooldown, now) is True


def test_should_not_alert_within_cooldown():
    """Alerted 1h ago, cooldown is 4h → do NOT re-alert (within window)."""
    now = 5000
    state = {"x": 5000 - 3600}  # alerted 1h ago
    cooldown = 4 * 3600
    assert sap.should_alert(_alert("critical", "x", ts=5000), state, cooldown, now) is False


def test_should_alert_after_cooldown():
    """Alerted 5h ago, cooldown is 4h → re-alert allowed (window expired)."""
    now = 5000
    state = {"x": 5000 - 5 * 3600}  # alerted 5h ago
    cooldown = 4 * 3600
    assert sap.should_alert(_alert("critical", "x", ts=5000), state, cooldown, now) is True


def test_should_alert_boundary_exclusive():
    """Alerted exactly cooldown seconds ago → NOT allowed (boundary exclusive).
    Cooldown 4h, last alert 4h ago → still within (must be STRICTLY after)."""
    now = 5000
    cooldown = 4 * 3600
    state = {"x": 5000 - cooldown}  # exactly at boundary
    assert sap.should_alert(_alert("critical", "x"), state, cooldown, now) is False


def test_should_alert_independent_per_subagent():
    """Subagent A alerted recently → A blocked, but B (never alerted) → allowed."""
    now = 5000
    state = {"a": 5000 - 3600}  # A alerted 1h ago
    cooldown = 4 * 3600
    assert sap.should_alert(_alert("critical", "a"), state, cooldown, now) is False
    assert sap.should_alert(_alert("critical", "b"), state, cooldown, now) is True


# ---------------------------------------------------------------------------
# update_state — record alert timestamps
# ---------------------------------------------------------------------------

def test_update_state_records_timestamp():
    state = {"a": 100}
    sap.update_state(state, [_alert("critical", "b"), _alert("critical", "c")], now=5000)
    assert state["b"] == 5000
    assert state["c"] == 5000
    assert state["a"] == 100  # untouched


def test_update_state_overwrites_old_timestamp():
    state = {"x": 100}
    sap.update_state(state, [_alert("critical", "x")], now=9999)
    assert state["x"] == 9999  # overwritten


# ---------------------------------------------------------------------------
# State file load/save (round-trip)
# ---------------------------------------------------------------------------

def test_load_state_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(sap, "STATE_FILE", tmp_path / "nope.json")
    assert sap.load_state() == {}


def test_save_load_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(sap, "STATE_FILE", tmp_path / "state.json")
    state = {"x": 1234, "y": 5678}
    sap.save_state(state)
    loaded = sap.load_state()
    assert loaded == state


# ---------------------------------------------------------------------------
# run_once — integration (mocked HTTP + notify)
# ---------------------------------------------------------------------------

def test_run_once_sends_critical_only(monkeypatch, tmp_path):
    """run_once fetches alerts, filters critical, sends via notify, updates state."""
    monkeypatch.setattr(sap, "STATE_FILE", tmp_path / "state.json")

    fetched = {"alerts": [
        _alert("critical", "alpha"),
        _alert("warning", "beta"),
        _alert("critical", "gamma"),
    ], "summary": {"total": 3, "critical": 2, "warning": 1}}

    sent = {"calls": 0, "alerts": None}

    def fake_fetch(url=None):
        return fetched

    def fake_send(alerts):
        sent["calls"] += 1
        sent["alerts"] = alerts
        return True

    monkeypatch.setattr(sap, "fetch_alerts", fake_fetch)
    monkeypatch.setattr(sap, "send_alerts", fake_send)

    result = sap.run_once(cooldown=4 * 3600, now=5000)
    assert sent["calls"] == 1  # one batch send
    assert {a["subagent"] for a in sent["alerts"]} == {"alpha", "gamma"}
    assert result["sent"] == 2
    # State updated for both
    state = sap.load_state()
    assert state["alpha"] == 5000
    assert state["gamma"] == 5000


def test_run_once_skips_within_cooldown(monkeypatch, tmp_path):
    """Already-alerted subagent (within cooldown) → not re-sent."""
    monkeypatch.setattr(sap, "STATE_FILE", tmp_path / "state.json")
    # Pre-populate state: alpha was alerted 1h ago.
    sap.save_state({"alpha": 5000 - 3600})

    fetched = {"alerts": [_alert("critical", "alpha")], "summary": {}}

    sent = {"calls": 0}

    monkeypatch.setattr(sap, "fetch_alerts", lambda url=None: fetched)
    monkeypatch.setattr(sap, "send_alerts", lambda a: sent.__setitem__("calls", sent["calls"] + 1) or True)

    result = sap.run_once(cooldown=4 * 3600, now=5000)
    assert sent["calls"] == 0  # nothing sent (within cooldown)
    assert result["sent"] == 0
    assert result["skipped"] == 1


def test_run_once_no_alerts_no_send(monkeypatch, tmp_path):
    """Empty alerts → no send, no state change."""
    monkeypatch.setattr(sap, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(sap, "fetch_alerts", lambda url=None: {"alerts": [], "summary": {}})
    sent = {"calls": 0}
    monkeypatch.setattr(sap, "send_alerts", lambda a: sent.__setitem__("calls", sent["calls"] + 1) or True)
    result = sap.run_once(now=5000)
    assert sent["calls"] == 0
    assert result["sent"] == 0
