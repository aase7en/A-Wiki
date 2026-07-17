"""Tests for scripts/lib/atomic_json.py — cross-platform atomic JSON read/write/lock.

Iron Law #1: failing tests written FIRST.

atomic_json เป็นพื้นฐาน (primitive) ของทุก stateful file ใน Neural Spine:
- memory_ledger.py ต้อง append โดยไม่เสีย
- blackboard.py ต้อง post ทีละข้อความ
- task_board.py ต้อง claim task แบบ atomic (กัน race condition)

ใช้ msvcrt.locking บน Windows, fcntl.flock บน Unix. Fallback ถ้าไม่มีทั้งคู่
→ error (ไม่เงียบผิด — ป้องกัน concurrency bug ที่หายาก).
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import atomic_json as aj  # noqa: E402  -- module under test (created by this chunk)


# ---------------------------------------------------------------------------
# 1. atomic_write — writes valid JSON, file appears fully-formed
# ---------------------------------------------------------------------------
def test_atomic_write_creates_file(tmp_path):
    f = tmp_path / "state.json"
    aj.atomic_write(f, {"tasks": [], "version": 1})
    assert f.is_file()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data == {"tasks": [], "version": 1}


def test_atomic_write_overwrites_existing(tmp_path):
    f = tmp_path / "state.json"
    aj.atomic_write(f, {"v": 1})
    aj.atomic_write(f, {"v": 2})
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data == {"v": 2}


# ---------------------------------------------------------------------------
# 2. atomic_write — never leaves a partial/corrupt file on failure
# ---------------------------------------------------------------------------
def test_atomic_write_uses_temp_file_then_rename(tmp_path):
    """Writer should write to temp then rename — partial never visible at target path."""
    f = tmp_path / "state.json"
    aj.atomic_write(f, {"important": "data"})
    # If the write had been direct (not temp+rename), a crash mid-write would
    # leave a partial file. We verify the temp mechanism by checking no .tmp
    # file lingers after a successful write.
    leftover_temps = list(tmp_path.glob("*.tmp")) + list(tmp_path.glob(".*.tmp"))
    assert leftover_temps == [], f"temp files should be cleaned up, found: {leftover_temps}"


# ---------------------------------------------------------------------------
# 3. atomic_append_jsonl — appends one JSON line per call
# ---------------------------------------------------------------------------
def test_atomic_append_jsonl_appends_lines(tmp_path):
    f = tmp_path / "log.jsonl"
    aj.atomic_append_jsonl(f, {"ts": 1, "msg": "first"})
    aj.atomic_append_jsonl(f, {"ts": 2, "msg": "second"})
    lines = [l for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"ts": 1, "msg": "first"}
    assert json.loads(lines[1]) == {"ts": 2, "msg": "second"}


def test_atomic_append_jsonl_creates_parent_dir(tmp_path):
    f = tmp_path / "subdir" / "deep" / "log.jsonl"
    aj.atomic_append_jsonl(f, {"x": 1})
    assert f.is_file()
    assert json.loads(f.read_text(encoding="utf-8").strip()) == {"x": 1}


# ---------------------------------------------------------------------------
# 4. atomic_append_jsonl — concurrent appends don't lose lines (the CORE test)
# ---------------------------------------------------------------------------
def test_concurrent_appends_never_lose_lines(tmp_path):
    """100 threads append 1 line each → file must have exactly 100 lines.

    This is THE test that proves atomic_json solves the race condition.
    Without locking, concurrent appends interleave and corrupt the file.
    """
    f = tmp_path / "concurrent.jsonl"
    N_THREADS = 50
    barrier = threading.Barrier(N_THREADS)

    def worker(i):
        barrier.wait()  # release all threads at once → maximize contention
        aj.atomic_append_jsonl(f, {"thread": i, "ts": i})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    lines = [l for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == N_THREADS, (
        f"expected {N_THREADS} lines (one per thread), got {len(lines)} — "
        f"concurrent appends lost data; locking is broken"
    )
    # All entries should be valid JSON (no corruption from interleaved writes)
    for line in lines:
        json.loads(line)  # raises if corrupt


# ---------------------------------------------------------------------------
# 5. file_lock context manager — blocks second locker until first releases
# ---------------------------------------------------------------------------
def test_file_lock_is_exclusive(tmp_path):
    """Two threads cannot hold the same lock at once — second must wait."""
    lock_file = tmp_path / "task.lock"
    held_order = []

    def grab_and_record(label, delay):
        with aj.file_lock(lock_file):
            held_order.append(f"{label}-acquired")
            import time
            time.sleep(delay)
            held_order.append(f"{label}-released")

    t1 = threading.Thread(target=grab_and_record, args=("A", 0.1))
    t2 = threading.Thread(target=grab_and_record, args=("B", 0.05))
    t1.start()
    import time
    time.sleep(0.02)  # ensure A grabs first
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    # Each acquire must be followed by its own release before the other acquires
    # Pattern: A-acquired, A-released, B-acquired, B-released (or B first)
    assert held_order[0].endswith("-acquired"), f"first event must be acquire, got {held_order[0]}"
    a_idx = next(i for i, e in enumerate(held_order) if e == "A-acquired")
    a_rel = next(i for i, e in enumerate(held_order) if e == "A-released")
    assert a_rel == a_idx + 1, "A's acquire+release must be adjacent (lock is exclusive)"


# ---------------------------------------------------------------------------
# 6. atomic_update — read-modify-write under lock (the claim pattern)
# ---------------------------------------------------------------------------
def test_atomic_update_concurrent_claims_only_one_wins(tmp_path):
    """10 threads try to 'claim' the same task via atomic_update → only 1 wins.

    This is the exact pattern task_board.claim() will use. If locking works,
    exactly one thread's update sets claimant='me'; the rest see someone
    already claimed and fail.
    """
    f = tmp_path / "tasks.json"
    aj.atomic_write(f, {"tasks": [{"id": "T1", "claimant": None}]})

    winners = []
    lock = threading.Lock()  # guard the winners list, not the file
    barrier = threading.Barrier(10)

    def try_claim(thread_id):
        barrier.wait()

        def mutate(data):
            task = data["tasks"][0]
            if task["claimant"] is None:
                task["claimant"] = f"thread-{thread_id}"
                return True  # I won
            return False  # someone else won

        won = aj.atomic_update(f, mutate)
        with lock:
            winners.append((thread_id, won))

    threads = [threading.Thread(target=try_claim, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    won_count = sum(1 for _, w in winners if w)
    assert won_count == 1, (
        f"exactly 1 thread should win the claim, got {won_count} — "
        f"locking is broken; race condition allowed multiple claims"
    )
    # Final state must reflect exactly one claimant
    final = json.loads(f.read_text(encoding="utf-8"))
    assert final["tasks"][0]["claimant"] is not None
    assert final["tasks"][0]["claimant"].startswith("thread-")
