"""device_health.py — stale device alarm for cross-device sync.

Surfaces devices that have stopped exporting Neural Spine shards. When a
device (Pi5, Mac, Windows) crashes or goes offline, its .tmp-sync/<device>.jsonl
goes stale. Without this alarm, the cross-device brain silently goes dark
on that machine — no one notices until they need a decision that should
have been synced.

Design mirrors alerts.py: pure function of shard files, no side effects,
clock injected via `now` parameter for deterministic testing.

Defense against clock skew (R-SA1): if the shard's embedded exported_at says
"15h ago" but the FILE's mtime says "10min ago", the device IS alive — its
clock is just wrong. We trust filesystem mtime over the embedded timestamp
in that case and suppress the alert.

Default thresholds:
  - warning:  12h   (missed 2 cron cycles at 6h cadence)
  - critical: 48h   (device likely down / hardware failure)

Used by:
  - server.py /api/devices (dashboard device health panel)
  - tests/test_device_health.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLDS = {
    "warning_hours": 12,    # flag when last export > 12h ago
    "critical_hours": 48,   # escalate to critical when > 48h
}

# Filesystem mtime tolerance for clock-skew detection. If a shard's file
# mtime is within this many seconds of "now", we trust the filesystem over
# the embedded timestamp (the device is alive, its clock is wrong).
MTIME_FRESH_SECONDS = 3600  # 1 hour


def _parse_exported_at(ts_str: str) -> datetime | None:
    """Parse ISO8601 timestamp, return timezone-aware datetime or None."""
    if not ts_str:
        return None
    try:
        # Handle both with and without trailing 'Z'
        ts = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _shard_device_name(shard_path: Path) -> str:
    """Extract device name from shard filename (<device>.jsonl)."""
    return shard_path.stem


def _load_shard(path: Path) -> dict[str, Any] | None:
    """Load a shard JSON file. Returns None on parse failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def evaluate_device_alerts(
    shards_dir: Path | str,
    *,
    now: datetime | None = None,
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return a list of alert dicts for devices whose shards are stale.

    Args:
      shards_dir: directory containing .tmp-sync/<device>.jsonl files
      now: current time (injected for testing; defaults to utcnow)
      thresholds: optional override of warning_hours / critical_hours

    Returns:
      List of alert dicts sorted critical-first, then by device name:
        [{
          "device": "pi5",
          "severity": "critical"|"warning",
          "age_hours": 72.5,
          "last_export": "2026-08-01T...",
          "message": "pi5 last exported 72.5h ago",
        }]
    """
    shards_dir = Path(shards_dir)
    if not shards_dir.is_dir():
        return []

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cfg = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    alerts: list[dict[str, Any]] = []
    shard_files = sorted(shards_dir.glob("*.jsonl"))

    for shard in shard_files:
        data = _load_shard(shard)
        if data is None:
            continue

        exported_at = _parse_exported_at(data.get("exported_at", ""))
        if exported_at is None:
            continue

        # Clock-skew defense (R-SA1): check filesystem mtime
        try:
            file_mtime = datetime.fromtimestamp(
                shard.stat().st_mtime, tz=timezone.utc)
            mtime_age = (now - file_mtime).total_seconds()
            if mtime_age < MTIME_FRESH_SECONDS:
                # File was recently modified → device is alive, clock is wrong
                continue
        except OSError:
            pass  # can't read mtime → proceed with embedded timestamp

        age = now - exported_at
        age_hours = age.total_seconds() / 3600

        if age_hours >= cfg["critical_hours"]:
            severity = "critical"
        elif age_hours >= cfg["warning_hours"]:
            severity = "warning"
        else:
            continue

        alerts.append({
            "device": _shard_device_name(shard),
            "severity": severity,
            "age_hours": round(age_hours, 1),
            "last_export": exported_at.isoformat(),
            "message": f"{_shard_device_name(shard)} last exported "
                       f"{round(age_hours, 1)}h ago",
        })

    # Sort: critical first, then by device name
    sev_order = {"critical": 0, "warning": 1}
    alerts.sort(key=lambda a: (sev_order.get(a["severity"], 99), a["device"]))
    return alerts


def device_summary(
    shards_dir: Path | str,
    *,
    now: datetime | None = None,
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return summary of ALL devices (including fresh ones) for dashboard.

    Unlike evaluate_device_alerts (which only returns stale devices), this
    lists every device with its status, age, and entry count. Used for the
    dashboard device-health panel.
    """
    shards_dir = Path(shards_dir)
    if not shards_dir.is_dir():
        return []

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cfg = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    summary: list[dict[str, Any]] = []
    for shard in sorted(shards_dir.glob("*.jsonl")):
        data = _load_shard(shard)
        if data is None:
            continue

        exported_at = _parse_exported_at(data.get("exported_at", ""))
        if exported_at is None:
            continue

        age_hours = (now - exported_at).total_seconds() / 3600
        if age_hours >= cfg["critical_hours"]:
            status = "critical"
        elif age_hours >= cfg["warning_hours"]:
            status = "warning"
        else:
            status = "fresh"

        summary.append({
            "device": _shard_device_name(shard),
            "status": status,
            "age_hours": round(age_hours, 1),
            "last_export": exported_at.isoformat(),
            "ledger_entries": len(data.get("ledger", [])),
            "blackboard_messages": len(data.get("blackboard", [])),
            "tasks": len(data.get("task_board", {}).get("tasks", [])),
            "source_device": data.get("source_device", _shard_device_name(shard)),
        })

    summary.sort(key=lambda s: s["device"])
    return summary
