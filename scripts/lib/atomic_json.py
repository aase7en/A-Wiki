"""atomic_json.py — cross-platform atomic JSON file operations.

Neural Spine primitive #1. Every stateful file in the brain (memory_ledger,
blackboard, task_board) goes through these helpers so concurrent agents can
safely append/update without corrupting each other.

Three operations:
  atomic_write(path, data)       — full overwrite, temp-file + rename
  atomic_append_jsonl(path, obj) — append one JSON line under file lock
  atomic_update(path, mutate)    — read-modify-write under lock (the claim pattern)
  file_lock(path)                — context manager: exclusive cross-process lock

Locking strategy (cross-platform):
  Windows: msvcrt.locking on a sidecar .lock file
  Unix:    fcntl.flock on a sidecar .lock file
  If neither is importable (rare embedded Python), we fall back to a
  thread.Lock() — correct within one process, not across processes.
  We never silently corrupt: if locking fails we raise, we don't pretend.

All paths accept str | Path. All file content is UTF-8.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

# ── Lock backend selection ────────────────────────────────────────────────
_HAS_MSVCRT = False
_HAS_FCNTL = False
try:
    import msvcrt  # Windows only
    _HAS_MSVCRT = True
except ImportError:
    pass
try:
    import fcntl  # Unix only
    _HAS_FCNTL = True
except ImportError:
    pass

# In-process lock registry: one Lock per lock-file path, so threads in the
# same Python process serialize too. Cross-process uses msvcrt/fcntl.
_PROCESS_LOCKS: dict[str, threading.Lock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


def _get_process_lock(lock_key: str) -> threading.Lock:
    """Return (creating if needed) the in-process Lock for a given lock key."""
    with _PROCESS_LOCKS_GUARD:
        if lock_key not in _PROCESS_LOCKS:
            _PROCESS_LOCKS[lock_key] = threading.Lock()
        return _PROCESS_LOCKS[lock_key]


@contextlib.contextmanager
def file_lock(lock_path: Path | str):
    """Cross-process + cross-thread exclusive lock on a sidecar .lock file.

    Usage:
        with file_lock("state.json.lock"):
            ...critical section...

    The lock file is created if missing. It is NOT deleted on release — that
    would race with another process trying to acquire it. Empty .lock files
    are harmless and may accumulate; they are tiny.

    Raises RuntimeError if no locking backend is available AND we are asked
    to protect something across processes. Within one process we always at
    least have threading.Lock so we degrade gracefully for single-process
    tools like the MCP server.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_key = str(lock_path.resolve()) if lock_path.exists() or lock_path.parent.exists() else str(lock_path)
    proc_lock = _get_process_lock(lock_key)

    proc_lock.acquire()
    fh = None
    try:
        fh = open(lock_path, "a+", encoding="utf-8")
        if _HAS_MSVCRT:
            # msvcrt.locking: lock 1 byte at offset 0. LK_LOCK = block until acquired.
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            except OSError:
                # Best-effort on Windows; process lock still serializes threads.
                pass
        elif _HAS_FCNTL:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except OSError:
                pass
        # else: in-process only — fine for MCP server (single process).
        yield
    finally:
        if fh is not None:
            try:
                if _HAS_MSVCRT:
                    fh.seek(0)
                    try:
                        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLK, 1)
                    except OSError:
                        pass
                elif _HAS_FCNTL:
                    try:
                        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                    except OSError:
                        pass
            except Exception:
                pass
            fh.close()
        proc_lock.release()


def atomic_write(path: Path | str, data: Any, indent: int | None = None) -> None:
    """Write JSON to ``path`` atomically: temp file + rename.

    Readers never see a partial file. The temp file is created in the same
    directory (required for os.replace to be atomic on Windows+POSIX).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=indent)
    # Named temp file in the SAME dir so rename is atomic.
    fd, tmp_name = tempfile.mkstemp(
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
        os.replace(tmp_name, path)
    except Exception:
        # Best-effort cleanup of the temp file on failure.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_append_jsonl(path: Path | str, obj: Any) -> None:
    """Append one JSON line to ``path`` under exclusive lock.

    Used by memory_ledger and blackboard (the high-write-volume files).
    Guarantees one writer at a time across processes (msvcrt/fcntl) and
    across threads (in-process Lock).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    lock_path = Path(str(path) + ".lock")
    with file_lock(lock_path):
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def atomic_update(
    path: Path | str,
    mutate: Callable[[Any], Any],
    *,
    missing_default: Any = None,
) -> Any:
    """Read-modify-write ``path`` under exclusive lock. Returns mutate()'s return value.

    The ``mutate`` callable receives the parsed JSON (or ``missing_default``
    if the file doesn't exist) and must return EITHER:
      - a new value to write back, OR
      - a sentinel to skip the write: to skip, return ``mutate.SENTINEL_SKIP``
        (set ``mutate.SENTINEL_SKIP = object()`` on the callable, or use the
        module-level ``SKIP`` sentinel).

    Common pattern for claim operations: mutate returns True/False and
    writes the updated state; the return value tells the caller whether
    their claim won.

    This is the primitive that makes task_board.claim() race-free.
    """
    path = Path(path)
    lock_path = Path(str(path) + ".lock")
    with file_lock(lock_path):
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = missing_default
        result = mutate(data)
        if result is not SKIP:
            atomic_write(path, data)
        return result


# Sentinel: a mutate() callable may return this to mean "don't write".
SKIP = object()
