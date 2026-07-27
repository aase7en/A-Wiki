"""cross_device_sync.py — sync Neural Spine state (.tmp/) across machines.

Tier 3 #11. .tmp/ is gitignored (local-only). This module exports the state
to a TRACKED payload file (.tmp-sync/payload.json) so it travels via git
push/pull. Other machines import it to merge into their local .tmp/.

Design:
  - ADDITIVE only — never deletes local entries (safety)
  - Idempotent — re-importing same payload adds nothing
  - Dedup by (ts, session_id, summary) tuple for ledger/bb; by task id for tasks
  - Payload is a single JSON file (atomic, diff-friendly)

Flow:
  device A:  export_state(.tmp/, .tmp-sync/)  → git add .tmp-sync/ && commit && push
  device B:  git pull                         → import_state(.tmp/, .tmp-sync/)
  → B now has A's ledger/bb/tasks entries merged into its local .tmp/

API:
  export_state(tmp_dir, sync_dir) → {ledger_entries, bb_messages, tasks}
  import_state(tmp_dir, sync_dir) → {ledger_added, bb_added, tasks_added}
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_ledger  # noqa: E402
import blackboard  # noqa: E402
import task_board  # noqa: E402


def _entry_key(entry: dict) -> tuple:
    """Stable dedup key for ledger/bb entries.

    Uses (session_id, summary) — NOT ts, because ts varies slightly between
    devices even for the same logical entry. summary is the semantic identity.
    """
    return (
        entry.get("session_id", entry.get("from", "")),
        entry.get("summary", entry.get("body", "")),
    )


def _task_key(task: dict) -> str:
    """Stable dedup key for tasks."""
    return task.get("id", "")


def export_state(
    tmp_dir: Path | str,
    sync_dir: Path | str,
) -> dict[str, int]:
    """Read local .tmp/ state and write merged payload to sync_dir/payload.json.

    Returns counts of what was exported.
    """
    tmp_dir = Path(tmp_dir)
    sync_dir = Path(sync_dir)
    sync_dir.mkdir(parents=True, exist_ok=True)
    payload_path = sync_dir / "payload.json"

    ledger_entries = []
    if (tmp_dir / "memory-ledger.jsonl").is_file():
        ledger = memory_ledger.MemoryLedger(tmp_dir / "memory-ledger.jsonl")
        ledger_entries = ledger._load_all()

    bb_messages = []
    if (tmp_dir / "blackboard.jsonl").is_file():
        bb_messages = blackboard.Blackboard(tmp_dir / "blackboard.jsonl").read(limit=10000)

    task_state = {"tasks": [], "version": 1}
    if (tmp_dir / "task-board.json").is_file():
        try:
            task_state = json.loads((tmp_dir / "task-board.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    payload = {
        "ledger": ledger_entries,
        "blackboard": bb_messages,
        "task_board": task_state,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_device": _device_id(),
    }
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {
        "ledger_entries": len(ledger_entries),
        "bb_messages": len(bb_messages),
        "tasks": len(task_state.get("tasks", [])),
    }


def import_state(
    tmp_dir: Path | str,
    sync_dir: Path | str,
) -> dict[str, int]:
    """Read payload.json from sync_dir and merge into local .tmp/.

    Additive + idempotent: only appends entries not already present locally.
    Returns counts of what was added.
    """
    tmp_dir = Path(tmp_dir)
    sync_dir = Path(sync_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    payload_path = sync_dir / "payload.json"

    if not payload_path.is_file():
        return {"ledger_added": 0, "bb_added": 0, "tasks_added": 0}

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"ledger_added": 0, "bb_added": 0, "tasks_added": 0}

    # --- Merge ledger ---
    ledger_added = 0
    ledger_path = tmp_dir / "memory-ledger.jsonl"
    local_ledger = memory_ledger.MemoryLedger(ledger_path)
    local_keys = {_entry_key(e) for e in local_ledger._load_all()}
    for entry in payload.get("ledger", []):
        if _entry_key(entry) not in local_keys:
            # Write raw entry (bypass append's redaction/normalization —
            # entries are already in canonical form from another device)
            import atomic_json
            atomic_json.atomic_append_jsonl(ledger_path, entry)
            local_keys.add(_entry_key(entry))
            ledger_added += 1

    # --- Merge blackboard ---
    bb_added = 0
    bb_path = tmp_dir / "blackboard.jsonl"
    local_bb = blackboard.Blackboard(bb_path)
    local_bb_keys = {_entry_key(m) for m in local_bb.read(limit=10000)}
    for msg in payload.get("blackboard", []):
        if _entry_key(msg) not in local_bb_keys:
            import atomic_json
            atomic_json.atomic_append_jsonl(bb_path, msg)
            local_bb_keys.add(_entry_key(msg))
            bb_added += 1

    # --- Merge task board ---
    tasks_added = 0
    tasks_path = tmp_dir / "task-board.json"
    remote_tasks = payload.get("task_board", {}).get("tasks", [])
    if remote_tasks:
        board = task_board.TaskBoard(tasks_path)
        local_tasks = board.list()
        local_task_keys = {_task_key(t) for t in local_tasks}
        # For each remote task not locally present, add it
        import atomic_json
        def mutate(state: dict) -> Any:
            for t in remote_tasks:
                if _task_key(t) and _task_key(t) not in local_task_keys:
                    # Add only if status is todo (don't override local claims)
                    if t.get("status") == "todo":
                        state.setdefault("tasks", []).append(t)
                        local_task_keys.add(_task_key(t))
                        nonlocal tasks_added
                        tasks_added += 1
            return state
        atomic_json.atomic_update(tasks_path, mutate,
                                  missing_default=board._empty_state())

    return {"ledger_added": ledger_added, "bb_added": bb_added, "tasks_added": tasks_added}


def _device_id() -> str:
    """Best-effort device identifier (hostname + user)."""
    import os
    import socket
    try:
        return f"{os.environ.get('USER', os.environ.get('USERNAME', '?'))}@{socket.gethostname()}"
    except Exception:
        return "unknown-device"
