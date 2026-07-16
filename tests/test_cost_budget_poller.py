"""Tests for scripts/hermes/cost_budget_poller.py — cost budget Telegram alert (V1).

Iron Law #1: failing tests written FIRST.

V1 อ่าน cost_history total_usd → เทียบ threshold → ส่ง Telegram alert
เมื่อเกิน budget. Reuse Q2 subagent_alert_poller pattern (idempotent state).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

import cost_budget_poller  # noqa: E402  -- module under test (created by V1)


# ---------------------------------------------------------------------------
# 1. should_alert — over threshold, first time → True
# ---------------------------------------------------------------------------
def test_should_alert_over_threshold_first_time():
    state = {}
    alert, reason = cost_budget_poller.should_alert(
        total_usd=15.0, threshold=10.0, state=state, cooldown=86400, now=1000.0, key="monthly",
    )
    assert alert is True
    assert "over" in reason.lower() or "exceed" in reason.lower() or "budget" in reason.lower()


# ---------------------------------------------------------------------------
# 2. should_alert — under threshold → False
# ---------------------------------------------------------------------------
def test_should_alert_under_threshold():
    state = {}
    alert, reason = cost_budget_poller.should_alert(
        total_usd=5.0, threshold=10.0, state=state, cooldown=86400, now=1000.0, key="monthly",
    )
    assert alert is False


# ---------------------------------------------------------------------------
# 3. should_alert — within cooldown → False (idempotent)
# ---------------------------------------------------------------------------
def test_should_alert_within_cooldown():
    now = 10000.0
    state = {"monthly": now - 100}
    alert, reason = cost_budget_poller.should_alert(
        total_usd=15.0, threshold=10.0, state=state, cooldown=86400, now=now, key="monthly",
    )
    assert alert is False
    assert "cooldown" in reason.lower()


# ---------------------------------------------------------------------------
# 4. should_alert — after cooldown → True (re-alert)
# ---------------------------------------------------------------------------
def test_should_alert_after_cooldown():
    now = 100000.0
    state = {"monthly": now - 90000}
    alert, reason = cost_budget_poller.should_alert(
        total_usd=15.0, threshold=10.0, state=state, cooldown=86400, now=now, key="monthly",
    )
    assert alert is True


# ---------------------------------------------------------------------------
# 5. update_state — records timestamp
# ---------------------------------------------------------------------------
def test_update_state_records_timestamp():
    state = {}
    cost_budget_poller.update_state(state, key="monthly", now=5000.0)
    assert state["monthly"] == 5000.0


# ---------------------------------------------------------------------------
# 6. build_alert_message — format
# ---------------------------------------------------------------------------
def test_build_alert_message_format():
    msg = cost_budget_poller.build_alert_message(total_usd=15.50, threshold=10.0, period="monthly")
    assert "15.50" in msg or "15.5" in msg
    assert "10" in msg
    assert "monthly" in msg.lower() or "budget" in msg.lower()


# ---------------------------------------------------------------------------
# 7. fetch_total_cost
# ---------------------------------------------------------------------------
def test_fetch_total_cost_returns_float(monkeypatch):
    monkeypatch.setattr(cost_budget_poller, "_fetch_cost_data", lambda url="": {"total_usd": 7.42, "run_count": 3})
    total = cost_budget_poller.fetch_total_cost()
    assert isinstance(total, (int, float))
    assert total == pytest.approx(7.42, abs=0.01)


def test_fetch_total_cost_handles_error(monkeypatch):
    def boom(url=""):
        raise ConnectionError("dashboard down")
    monkeypatch.setattr(cost_budget_poller, "_fetch_cost_data", boom)
    total = cost_budget_poller.fetch_total_cost()
    assert total == 0.0


# ---------------------------------------------------------------------------
# 8. run_once — full cycle
# ---------------------------------------------------------------------------
def test_run_once_alerts_when_over_budget(monkeypatch):
    sent = {"msg": None}
    monkeypatch.setattr(cost_budget_poller, "fetch_total_cost", lambda: 15.0)
    monkeypatch.setattr(cost_budget_poller, "send_telegram", lambda m, parse_mode="HTML": sent.__setitem__("msg", m) or True)
    monkeypatch.setattr(cost_budget_poller, "load_state", lambda: {})
    monkeypatch.setattr(cost_budget_poller, "save_state", lambda s: None)
    result = cost_budget_poller.run_once(threshold=10.0, cooldown=86400, dry_run=False)
    assert result is True
    assert sent["msg"] is not None


def test_run_once_no_alert_when_under_budget(monkeypatch):
    monkeypatch.setattr(cost_budget_poller, "fetch_total_cost", lambda: 5.0)
    monkeypatch.setattr(cost_budget_poller, "send_telegram", lambda m, parse_mode="HTML": True)
    monkeypatch.setattr(cost_budget_poller, "load_state", lambda: {})
    monkeypatch.setattr(cost_budget_poller, "save_state", lambda s: None)
    result = cost_budget_poller.run_once(threshold=10.0, cooldown=86400, dry_run=False)
    assert result is False


def test_run_once_dry_run_does_not_send(monkeypatch):
    sent = {"count": 0}
    def mock_send(m, parse_mode="HTML"):
        sent["count"] += 1
        return True
    monkeypatch.setattr(cost_budget_poller, "fetch_total_cost", lambda: 15.0)
    monkeypatch.setattr(cost_budget_poller, "send_telegram", mock_send)
    monkeypatch.setattr(cost_budget_poller, "load_state", lambda: {})
    monkeypatch.setattr(cost_budget_poller, "save_state", lambda s: None)
    result = cost_budget_poller.run_once(threshold=10.0, cooldown=86400, dry_run=True)
    assert sent["count"] == 0
    assert result is True
