"""Tests for scripts/lib/cross_device_sync.py — sync Neural Spine state across machines.

Iron Law #1: failing tests written FIRST.

cross_device_sync ทำให้ .tmp/{memory-ledger,blackboard,task-board} ที่
local-only สามารถ sync ข้ามเครื่องได้ (Win ↔ Mac ↔ Pi5) ผ่าน git-tracked
payload file (.tmp-sync/ เป็น tracked dir — ไม่ใช่ .tmp/ ที่ gitignored).

Flow:
  export_state() → อ่าน .tmp/*.jsonl + .tmp/task-board.json
                 → dedupe + merge → write .tmp-sync/payload.json (tracked)
                 → user commits + push
  import_state() → อ่าน .tmp-sync/payload.json (จาก git pull)
                 → merge entries ที่ยังไม่มีใน local .tmp/
                 → append ใหม่เข้า local state

Idempotent + additive (ไม่ลบของเดิม).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402
import blackboard as bb  # noqa: E402
import task_board as tb  # noqa: E402
import cross_device_sync as cds  # noqa: E402 -- module under test (created here)


def _setup_state(tmp_path: Path) -> dict:
    """Create .tmp/ + .tmp-sync/ structure under tmp_path (parents=True)."""
    tmp_dir = tmp_path / ".tmp"
    sync_dir = tmp_path / ".tmp-sync"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    sync_dir.mkdir(parents=True, exist_ok=True)
    return {
        "tmp_dir": tmp_dir,
        "sync_dir": sync_dir,
        "ledger": tmp_dir / "memory-ledger.jsonl",
        "bb": tmp_dir / "blackboard.jsonl",
        "tasks": tmp_dir / "task-board.json",
        "payload": sync_dir / "payload.json",
    }


# ---------------------------------------------------------------------------
# 1. export_state — reads local .tmp/ and writes payload.json
# ---------------------------------------------------------------------------
def test_export_writes_payload(tmp_path):
    paths = _setup_state(tmp_path)
    # Seed local state
    ml.MemoryLedger(paths["ledger"]).append(
        session_id="device-A", type="decision", summary="test from device A")
    bb.Blackboard(paths["bb"]).post(frm="claude", to="*", body="hello")
    tb.TaskBoard(paths["tasks"]).add(goal="task from A")

    result = cds.export_state(paths["tmp_dir"], paths["sync_dir"])
    assert result["ledger_entries"] >= 1
    assert result["bb_messages"] >= 1
    assert result["tasks"] >= 1
    assert paths["payload"].is_file()
    payload = json.loads(paths["payload"].read_text(encoding="utf-8"))
    assert "ledger" in payload
    assert "blackboard" in payload
    assert "task_board" in payload


def test_export_handles_empty_state(tmp_path):
    """No local state → export writes empty payload (not crash)."""
    paths = _setup_state(tmp_path)
    result = cds.export_state(paths["tmp_dir"], paths["sync_dir"])
    assert result["ledger_entries"] == 0
    assert paths["payload"].is_file()


# ---------------------------------------------------------------------------
# 2. import_state — merges payload into local .tmp/ (additive, idempotent)
# ---------------------------------------------------------------------------
def test_import_adds_new_entries(tmp_path):
    """Payload has entries local doesn't → append them."""
    paths = _setup_state(tmp_path)
    # Local has 1 ledger entry
    ml.MemoryLedger(paths["ledger"]).append(
        session_id="local", type="decision", summary="local entry")
    # Payload has 2 (1 duplicate + 1 new)
    payload = {
        "ledger": [
            {"ts": 1.0, "session_id": "local", "type": "decision",
             "summary": "local entry", "files": [], "tags": [], "parent_ts": None},
            {"ts": 2.0, "session_id": "device-B", "type": "lesson",
             "summary": "new from B", "files": [], "tags": [], "parent_ts": None},
        ],
        "blackboard": [],
        "task_board": {"tasks": [], "version": 1},
        "exported_at": "2026-01-01",
        "source_device": "device-B",
    }
    paths["payload"].write_text(json.dumps(payload), encoding="utf-8")

    result = cds.import_state(paths["tmp_dir"], paths["sync_dir"])
    assert result["ledger_added"] == 1  # only the new one
    entries = ml.MemoryLedger(paths["ledger"])._load_all()
    summaries = [e["summary"] for e in entries]
    assert "local entry" in summaries
    assert "new from B" in summaries


def test_import_idempotent(tmp_path):
    """Running import twice on same payload → second run adds nothing."""
    paths = _setup_state(tmp_path)
    payload = {
        "ledger": [
            {"ts": 1.0, "session_id": "B", "type": "decision",
             "summary": "from B", "files": [], "tags": [], "parent_ts": None},
        ],
        "blackboard": [],
        "task_board": {"tasks": [], "version": 1},
    }
    paths["payload"].write_text(json.dumps(payload), encoding="utf-8")
    first = cds.import_state(paths["tmp_dir"], paths["sync_dir"])
    second = cds.import_state(paths["tmp_dir"], paths["sync_dir"])
    assert first["ledger_added"] == 1
    assert second["ledger_added"] == 0, "second import should not re-add"


def test_import_no_op_when_payload_missing(tmp_path):
    """No payload.json → import returns zeros, doesn't crash."""
    paths = _setup_state(tmp_path)
    result = cds.import_state(paths["tmp_dir"], paths["sync_dir"])
    assert result["ledger_added"] == 0
    assert result["bb_added"] == 0
    assert result["tasks_added"] == 0


# ---------------------------------------------------------------------------
# 3. round-trip: export from A → import to B
# ---------------------------------------------------------------------------
def test_round_trip_export_then_import(tmp_path):
    """Simulate: device A exports → device B imports → B sees A's state."""
    # Device A
    device_a = tmp_path / "deviceA"
    device_a.mkdir()
    paths_a = _setup_state(device_a)
    ml.MemoryLedger(paths_a["ledger"]).append(
        session_id="device-A", type="decision", summary="A's work",
        tags=["cross-device"])
    bb.Blackboard(paths_a["bb"]).post(
        frm="claude", to="codex", body="msg from A", msg_type="question")
    cds.export_state(paths_a["tmp_dir"], paths_a["sync_dir"])

    # Device B (fresh — no local state)
    device_b = tmp_path / "deviceB"
    paths_b = _setup_state(device_b)
    # Simulate git: copy payload from A to B
    payload_a = paths_a["payload"].read_text(encoding="utf-8")
    paths_b["payload"].write_text(payload_a, encoding="utf-8")

    result = cds.import_state(paths_b["tmp_dir"], paths_b["sync_dir"])
    assert result["ledger_added"] >= 1
    assert result["bb_added"] >= 1

    # Verify B now has A's entries
    b_ledger_entries = ml.MemoryLedger(paths_b["ledger"])._load_all()
    assert any("A's work" in e["summary"] for e in b_ledger_entries)
    b_msgs = bb.Blackboard(paths_b["bb"]).read()
    assert any("msg from A" in m["body"] for m in b_msgs)


# ---------------------------------------------------------------------------
# 4. merge safety — never delete local entries
# ---------------------------------------------------------------------------
def test_import_never_deletes_local_entries(tmp_path):
    """Local has 5 entries, payload has 1 → local still has 5+0 or 5+1."""
    paths = _setup_state(tmp_path)
    ledger = ml.MemoryLedger(paths["ledger"])
    for i in range(5):
        ledger.append(session_id="local", type="decision", summary=f"local-{i}")
    payload = {
        "ledger": [
            {"ts": 99.0, "session_id": "remote", "type": "idea",
             "summary": "remote", "files": [], "tags": [], "parent_ts": None},
        ],
        "blackboard": [],
        "task_board": {"tasks": [], "version": 1},
    }
    paths["payload"].write_text(json.dumps(payload), encoding="utf-8")
    cds.import_state(paths["tmp_dir"], paths["sync_dir"])
    entries = ml.MemoryLedger(paths["ledger"])._load_all()
    # Must have at least the 5 original + possibly the 1 new
    assert len(entries) >= 5
    summaries = [e["summary"] for e in entries]
    for i in range(5):
        assert f"local-{i}" in summaries, f"local-{i} was deleted!"
