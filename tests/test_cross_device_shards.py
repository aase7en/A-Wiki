"""Tests for cross_device_sync.py per-device shard API (Approach B).

Iron Law #1: failing tests written FIRST.

Rationale (A-Think pre-mortem R2): a single tracked payload.json creates
near-certain git merge conflict when 2+ devices export concurrently (Pi5 cron
every 6h + Windows manual + MacBook manual). Per-device shards
(`.tmp-sync/<device>.jsonl`) make conflicts near-impossible because each device
writes only its own file. Import does set-union across all shards.

These tests also enforce defense layer 2 (R1): even though memory_ledger already
redacts on append, export must re-scan and refuse to write a shard containing
anything that looks like a secret. Belt + suspenders — a secret leaking to
GitHub is a one-way-door (Iron Law #6).
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
import cross_device_sync as cds  # noqa: E402


def _setup(tmp_path: Path) -> dict:
    tmp_dir = tmp_path / ".tmp"
    sync_dir = tmp_path / ".tmp-sync"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    sync_dir.mkdir(parents=True, exist_ok=True)
    return {
        "tmp_dir": tmp_dir,
        "sync_dir": sync_dir,
        "ledger": tmp_dir / "memory-ledger.jsonl",
        "bb": tmp_dir / "blackboard.jsonl",  # MUST live inside .tmp/ (matches hook paths)
        "tasks": tmp_dir / "task-board.json",
    }


# ---------------------------------------------------------------------------
# 1. export_shard — writes .tmp-sync/<device>.jsonl (NOT payload.json)
# ---------------------------------------------------------------------------
def test_export_shard_writes_per_device_file(tmp_path):
    """export_shard writes <sync_dir>/<device>.jsonl, not payload.json."""
    p = _setup(tmp_path)
    ml.MemoryLedger(p["ledger"]).append(
        session_id="win", type="decision", summary="win work")
    out = cds.export_shard(p["tmp_dir"], p["sync_dir"], device="windows")
    shard = p["sync_dir"] / "windows.jsonl"
    assert shard.is_file(), f"expected per-device shard at {shard}"
    # Old payload.json must NOT be created by export_shard
    assert not (p["sync_dir"] / "payload.json").exists()
    assert out["ledger_entries"] >= 1


def test_export_shard_is_idempotent_within_device(tmp_path):
    """Same device exporting twice → shard contains each entry once.

    A device that exports, then exports again after importing other devices'
    shards, must not duplicate its own earlier entries in its shard. We
    overwrite-with-dedup (canonical: latest snapshot of THIS device's local
    entries that originated here).
    """
    p = _setup(tmp_path)
    ledger = ml.MemoryLedger(p["ledger"])
    ledger.append(session_id="win", type="decision", summary="entry-1")
    cds.export_shard(p["tmp_dir"], p["sync_dir"], device="windows")
    ledger.append(session_id="win", type="decision", summary="entry-2")
    cds.export_shard(p["tmp_dir"], p["sync_dir"], device="windows")
    shard = (p["sync_dir"] / "windows.jsonl").read_text(encoding="utf-8")
    assert shard.count("entry-1") == 1
    assert shard.count("entry-2") == 1


# ---------------------------------------------------------------------------
# 2. Two devices → no conflict — each has own file
# ---------------------------------------------------------------------------
def test_two_devices_no_conflict_separate_files(tmp_path):
    """Two devices exporting to same sync_dir → 2 files, 0 overwrite."""
    p = _setup(tmp_path)

    # Device A writes
    ml.MemoryLedger(p["ledger"]).append(
        session_id="A", type="decision", summary="A entry")
    cds.export_shard(p["tmp_dir"], p["sync_dir"], device="deviceA")

    # Device B writes (fresh .tmp simulated by clearing then re-seeding)
    (p["ledger"]).unlink()
    ml.MemoryLedger(p["ledger"]).append(
        session_id="B", type="decision", summary="B entry")
    cds.export_shard(p["tmp_dir"], p["sync_dir"], device="deviceB")

    assert (p["sync_dir"] / "deviceA.jsonl").is_file()
    assert (p["sync_dir"] / "deviceB.jsonl").is_file()
    # A's file untouched by B
    a_text = (p["sync_dir"] / "deviceA.jsonl").read_text(encoding="utf-8")
    assert "A entry" in a_text
    assert "B entry" not in a_text


# ---------------------------------------------------------------------------
# 3. import_all_shards — set-union merge across all *.jsonl in sync_dir
# ---------------------------------------------------------------------------
def test_import_all_shards_merges_every_device(tmp_path):
    """import_all_shards reads all <device>.jsonl and merges into local .tmp/."""
    p = _setup(tmp_path)
    # Simulate 2 devices having pushed their shards
    for dev, summ in [("deviceA", "from A"), ("deviceB", "from B")]:
        shard_path = p["sync_dir"] / f"{dev}.jsonl"
        entry = {
            "ts": 1.0, "session_id": dev, "type": "decision",
            "summary": summ, "files": [], "tags": [], "parent_ts": None,
        }
        shard_path.write_text(
            json.dumps({"ledger": [entry], "blackboard": [],
                        "task_board": {"tasks": [], "version": 1},
                        "source_device": dev, "exported_at": "2026-01-01"}),
            encoding="utf-8")

    result = cds.import_all_shards(p["tmp_dir"], p["sync_dir"])
    assert result["ledger_added"] == 2
    entries = ml.MemoryLedger(p["ledger"])._load_all()
    summaries = [e["summary"] for e in entries]
    assert "from A" in summaries and "from B" in summaries


def test_import_all_shards_idempotent(tmp_path):
    """import_all_shards twice → 2nd run adds 0."""
    p = _setup(tmp_path)
    shard = p["sync_dir"] / "deviceA.jsonl"
    shard.write_text(json.dumps({
        "ledger": [{"ts": 1.0, "session_id": "A", "type": "decision",
                    "summary": "x", "files": [], "tags": [], "parent_ts": None}],
        "blackboard": [], "task_board": {"tasks": [], "version": 1},
        "source_device": "deviceA", "exported_at": "2026-01-01"}), encoding="utf-8")
    first = cds.import_all_shards(p["tmp_dir"], p["sync_dir"])
    second = cds.import_all_shards(p["tmp_dir"], p["sync_dir"])
    assert first["ledger_added"] == 1
    assert second["ledger_added"] == 0


def test_import_all_shards_skips_payload_json(tmp_path):
    """import_all_shards reads only <device>.jsonl, never payload.json (legacy)."""
    p = _setup(tmp_path)
    # Legacy payload.json present (from old export_state API) → must be ignored
    (p["sync_dir"] / "payload.json").write_text(json.dumps({
        "ledger": [{"ts": 1.0, "session_id": "legacy", "type": "decision",
                    "summary": "legacy", "files": [], "tags": [], "parent_ts": None}],
        "blackboard": [], "task_board": {"tasks": [], "version": 1}}),
        encoding="utf-8")
    result = cds.import_all_shards(p["tmp_dir"], p["sync_dir"])
    assert result["ledger_added"] == 0, "must not read legacy payload.json"


# ---------------------------------------------------------------------------
# 4. Defense layer 2 — export refuses to write secret-bearing shard (R1)
# ---------------------------------------------------------------------------
def test_export_shard_refuses_secret_in_summary(tmp_path):
    """If a ledger entry somehow contains a real-looking key, export must
    refuse to write the shard (return error dict, write nothing)."""
    p = _setup(tmp_path)
    # Bypass ledger.append (which redacts) — write raw line with a fake key
    p["ledger"].write_text(json.dumps({
        "ts": 1.0, "session_id": "x", "type": "decision",
        "summary": "leaked key sk-1234567890abcdefWXYZ in summary",
        "files": [], "tags": [], "parent_ts": None,
    }), encoding="utf-8")
    result = cds.export_shard(p["tmp_dir"], p["sync_dir"], device="leaky")
    assert result.get("blocked"), "export must block on detected secret"
    assert "secret" in result.get("reason", "").lower()
    # Nothing written
    assert not (p["sync_dir"] / "leaky.jsonl").exists()


def test_export_shard_redacts_generic_secret_in_files(tmp_path):
    """A 'password=...' substring in files[] must block too (defense layer 2)."""
    p = _setup(tmp_path)
    p["ledger"].write_text(json.dumps({
        "ts": 1.0, "session_id": "x", "type": "decision",
        "summary": "ok",
        "files": ["/etc/conf", "password=abcdefghijklmnopabcdefghijklmnop0123456789"],
        "tags": [], "parent_ts": None,
    }), encoding="utf-8")
    result = cds.export_shard(p["tmp_dir"], p["sync_dir"], device="leaky")
    assert result.get("blocked")


# ---------------------------------------------------------------------------
# 5. No infinite loop — export does not call import (R3)
# ---------------------------------------------------------------------------
def test_export_shard_does_not_import(tmp_path, monkeypatch):
    """export_shard must NOT call import_state/import_all_shards (loop guard)."""
    p = _setup(tmp_path)
    ml.MemoryLedger(p["ledger"]).append(
        session_id="x", type="decision", summary="ok")
    called = {"import_state": 0, "import_all_shards": 0}
    monkeypatch.setattr(cds, "import_state",
                        lambda *a, **k: called.__setitem__("import_state",
                                                            called["import_state"] + 1))
    monkeypatch.setattr(cds, "import_all_shards",
                        lambda *a, **k: called.__setitem__(
                            "import_all_shards", called["import_all_shards"] + 1))
    cds.export_shard(p["tmp_dir"], p["sync_dir"], device="win")
    assert called["import_state"] == 0
    assert called["import_all_shards"] == 0


# ---------------------------------------------------------------------------
# 6. Round-trip end-to-end (Approach B): A exports shard → B imports all
# ---------------------------------------------------------------------------
def test_round_trip_shard_approach(tmp_path):
    """End-to-end: device A writes shard, B imports_all_shards → B sees A."""
    device_a = tmp_path / "A"
    device_a.mkdir()
    pa = _setup(device_a)
    ml.MemoryLedger(pa["ledger"]).append(
        session_id="A", type="decision", summary="A's real work",
        tags=["cross-device"])
    bb.Blackboard(pa["bb"]).post(
        frm="claude", to="codex", body="msg from A", msg_type="question")
    cds.export_shard(pa["tmp_dir"], pa["sync_dir"], device="deviceA")

    device_b = tmp_path / "B"
    pb = _setup(device_b)
    # Simulate git pull: copy A's shard to B's sync_dir
    shard_text = (pa["sync_dir"] / "deviceA.jsonl").read_text(encoding="utf-8")
    (pb["sync_dir"] / "deviceA.jsonl").write_text(shard_text, encoding="utf-8")

    result = cds.import_all_shards(pb["tmp_dir"], pb["sync_dir"])
    assert result["ledger_added"] >= 1
    assert result["bb_added"] >= 1
    entries = ml.MemoryLedger(pb["ledger"])._load_all()
    assert any("A's real work" in e["summary"] for e in entries)
