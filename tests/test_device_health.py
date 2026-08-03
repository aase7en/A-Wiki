"""Tests for scripts/live-dashboard/device_health.py — stale device alarm.

Iron Law #1: failing tests written FIRST.

Purpose: after cross_device_sync activation (#2), each device writes a shard
to .tmp-sync/<device>.jsonl with exported_at timestamp. If a device stops
exporting (crash, network, SD card dead), the cross-device brain goes dark
on that machine. This alarm surfaces stale devices in the dashboard.

Design mirrors alerts.py: pure function of shard files, no I/O side effects,
no clock dependency (now injected), trivially testable.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import device_health as dh  # noqa: E402 -- module under test (created here)


def _make_shard(path: Path, device: str, exported_at: str,
                entries: int = 1, mtime_now: datetime | None = None) -> None:
    """Write a shard file with given metadata.

    If mtime_now is set, the file's mtime is forced to that instant — used
    for clock-skew detection testing (the file appears freshly written even
    though exported_at says otherwise).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ledger": [{"ts": 1.0, "session_id": device, "type": "decision",
                    "summary": "x", "files": [], "tags": [], "parent_ts": None}
                   for _ in range(entries)],
        "blackboard": [],
        "task_board": {"tasks": [], "version": 1},
        "exported_at": exported_at,
        "source_device": device,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    # Set mtime to match the exported_at by default (simulates a real scp'd
    # file whose filesystem mtime matches when it was exported). Override
    # with mtime_now to test clock-skew defense specifically.
    import os
    from datetime import datetime as _dt
    if mtime_now is not None:
        ts = mtime_now.timestamp()
    else:
        # Parse exported_at to match — realistic for non-clock-skew scenario
        try:
            ts = _dt.fromisoformat(exported_at.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return  # can't parse → leave mtime as-is (file creation time)
    os.utime(path, (ts, ts))


NOW = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 1. evaluate_device_alerts — basic detection
# ---------------------------------------------------------------------------
def test_fresh_device_no_alert(tmp_path):
    """Device exported 1h ago → no alert."""
    fresh = NOW - timedelta(hours=1)
    _make_shard(tmp_path / ".tmp-sync" / "win.jsonl", "win",
                fresh.isoformat())
    alerts = dh.evaluate_device_alerts(tmp_path / ".tmp-sync", now=NOW)
    assert alerts == []


def test_stale_device_warning(tmp_path):
    """Device exported 15h ago → warning (default threshold 12h)."""
    stale = NOW - timedelta(hours=15)
    _make_shard(tmp_path / ".tmp-sync" / "pi5.jsonl", "pi5",
                stale.isoformat())
    alerts = dh.evaluate_device_alerts(tmp_path / ".tmp-sync", now=NOW)
    assert len(alerts) == 1
    assert alerts[0]["device"] == "pi5"
    assert alerts[0]["severity"] == "warning"


def test_stale_device_critical(tmp_path):
    """Device exported 72h ago → critical (default threshold 48h)."""
    stale = NOW - timedelta(hours=72)
    _make_shard(tmp_path / ".tmp-sync" / "mac.jsonl", "mac",
                stale.isoformat())
    alerts = dh.evaluate_device_alerts(tmp_path / ".tmp-sync", now=NOW)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# 2. Clock-skew detection (R-SA1) — filesystem mtime is the truth
# ---------------------------------------------------------------------------
def test_clock_skew_suppresses_alert(tmp_path):
    """exported_at says 15h ago but file mtime is 10min ago → clock skew,
    suppress the alert (the device IS alive, its clock is just wrong)."""
    stale_ts = (NOW - timedelta(hours=15)).isoformat()
    # mtime forced to 10 minutes before NOW (relative to test clock, not real)
    _make_shard(tmp_path / ".tmp-sync" / "pi5.jsonl", "pi5",
                stale_ts, mtime_now=NOW - timedelta(minutes=10))
    alerts = dh.evaluate_device_alerts(tmp_path / ".tmp-sync", now=NOW)
    assert alerts == [], "clock skew should suppress stale alert"


# ---------------------------------------------------------------------------
# 3. Multi-device — mixed states, sorted critical-first
# ---------------------------------------------------------------------------
def test_mixed_devices_sorted_by_severity(tmp_path):
    sync = tmp_path / ".tmp-sync"
    _make_shard(sync / "fresh.jsonl", "fresh",
                (NOW - timedelta(hours=1)).isoformat())
    _make_shard(sync / "warn.jsonl", "warn",
                (NOW - timedelta(hours=15)).isoformat())
    _make_shard(sync / "crit.jsonl", "crit",
                (NOW - timedelta(hours=72)).isoformat())
    alerts = dh.evaluate_device_alerts(sync, now=NOW)
    assert len(alerts) == 2
    # Critical must come before warning
    assert alerts[0]["severity"] == "critical"
    assert alerts[1]["severity"] == "warning"


# ---------------------------------------------------------------------------
# 4. Empty / missing sync dir
# ---------------------------------------------------------------------------
def test_no_shards_no_alerts(tmp_path):
    """No shard files → no alerts (don't alarm on empty/missing dir)."""
    alerts = dh.evaluate_device_alerts(tmp_path / ".tmp-sync", now=NOW)
    assert alerts == []


def test_corrupt_shard_skipped(tmp_path):
    """Malformed shard file → skipped, not crash."""
    sync = tmp_path / ".tmp-sync"
    sync.mkdir(parents=True)
    (sync / "broken.jsonl").write_text("{not valid json", encoding="utf-8")
    alerts = dh.evaluate_device_alerts(sync, now=NOW)
    assert alerts == []


# ---------------------------------------------------------------------------
# 5. device_summary — for dashboard display
# ---------------------------------------------------------------------------
def test_device_summary_returns_all_devices(tmp_path):
    """Summary lists every device (even fresh ones) with last_export age."""
    sync = tmp_path / ".tmp-sync"
    _make_shard(sync / "win.jsonl", "win",
                (NOW - timedelta(hours=2)).isoformat(), entries=5)
    _make_shard(sync / "pi5.jsonl", "pi5",
                (NOW - timedelta(hours=15)).isoformat(), entries=3)
    summary = dh.device_summary(sync, now=NOW)
    assert len(summary) == 2
    devices = {s["device"] for s in summary}
    assert devices == {"win", "pi5"}
    win = next(s for s in summary if s["device"] == "win")
    assert win["age_hours"] == pytest.approx(2.0, abs=0.1)
    assert win["ledger_entries"] == 5
    assert win["status"] == "fresh"
    pi5 = next(s for s in summary if s["device"] == "pi5")
    assert pi5["status"] == "warning"
