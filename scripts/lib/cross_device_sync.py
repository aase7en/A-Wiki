"""cross_device_sync.py — sync Neural Spine state (.tmp/) across machines.

Tier 3 #11. .tmp/ is gitignored (local-only). This module publishes the state
to TRACKED files under .tmp-sync/ so it travels via git push/pull. Other
machines import it to merge into their local .tmp/.

Two APIs (both kept; Approach B is the conflict-safe default):

  Approach A (legacy single payload) — keep for back-compat, NOT recommended
    for concurrent multi-device use:
      export_state(.tmp/, .tmp-sync/)  → writes .tmp-sync/payload.json
      import_state(.tmp/, .tmp-sync/)  → merges payload.json into .tmp/

  Approach B (per-device shards, default 2026-08-03) — each device writes only
    its OWN file, so concurrent exports never collide in git:
      export_shard(.tmp/, .tmp-sync/, device="<name>")
        → writes .tmp-sync/<device>.jsonl (overwrite-with-dedup of THIS device's
          entries; never touches other devices' files)
      import_all_shards(.tmp/, .tmp-sync/)
        → set-union merge of every .tmp-sync/<device>.jsonl into local .tmp/

Design:
  - ADDITIVE only — never deletes local entries (safety, one-way-door)
  - Idempotent — re-importing same shard adds nothing
  - Dedup by (session_id, summary) for ledger/bb; by task id for tasks
    (NOT ts — ts drifts across machines/clocks)
  - Defense layer 2: export_shard re-scans for secrets even though
    memory_ledger already redacts on append. A secret reaching git is a
    one-way door (Iron Law #6), so we do not trust a single layer.
  - No loops: export never calls import (R3).

Flow (Approach B):
  device A:  export_shard(.tmp/, .tmp-sync/, device="windows")
             → git add .tmp-sync/ && commit && push
  device B:  git pull
             → import_all_shards(.tmp/, .tmp-sync/)
             → B now has A's entries merged into its local .tmp/
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_ledger  # noqa: E402
import blackboard  # noqa: E402
import task_board  # noqa: E402
import atomic_json  # noqa: E402


# --- Defense layer 2: secret re-scan (independent copy — do NOT import from
#     memory_ledger, so a regression there cannot silently disable this gate) ---
_SECRET_RESCAN = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[bp]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{30,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    re.compile(
        r"(?:api[_-]?key|token|secret|password|pwd)[\"'\s:=]+[A-Za-z0-9_\-]{32,}",
        re.IGNORECASE),
]


def _load_privacy_patterns() -> list[re.Pattern]:
    """Load the project-name / codename / foreign-path denylist that Layer 2
    historically ignored.

    A-Council test-engineer 2026-08-03 (cb839d5d regression): _scan_for_secret
    only matched credential SHAPES (sk-/AKIA/...). It had no concept of
    private project names, so `sunday-estate-webapp` sailed through Layer 2
    AND Layer 3 (staged-diff), even though check-privacy.py (Layer 3.5 / CI)
    caught it. This closes the gap by reading the SAME source of truth
    check-privacy.py uses (drive/personal/privacy-patterns.txt, overridable
    via AWIKI_PRIVACY_PATTERNS_FILE for hermetic tests). If the file is
    missing/unreadable, returns [] (fail-open for the privacy axis — the
    credential regexes in _SECRET_RESCAN still run independently).
    """
    env = os.environ.get("AWIKI_PRIVACY_PATTERNS_FILE", "").strip()
    # cross_device_sync.py is at scripts/lib/cross_device_sync.py → parents[2] = repo root
    default_path = Path(__file__).resolve().parents[2] / "drive" / "personal" / "privacy-patterns.txt"
    path = Path(env) if env else default_path
    if not path.exists():
        return []
    patterns: list[re.Pattern] = []
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                patterns.append(re.compile(line))
            except re.error:
                # Skip unparseable lines rather than crashing the export gate.
                continue
    except OSError:
        return []
    return patterns


def _find_secret(text: str) -> str | None:
    """Return the first matching secret-looking substring, or None.

    Defense layer 2 — independent of memory_ledger._redact. If this returns
    non-None, export_shard refuses to write.

    A-Council 2026-08-03: extended beyond credential SHAPES to also match
    the project-name / foreign-path denylist in privacy-patterns.txt. The
    two axes (credential shape + privacy name) are now both consulted —
    either one firing blocks the export. The patterns file is re-read on
    every call so a freshly-added denylist entry takes effect immediately
    (no server restart).
    """
    if not text:
        return None
    for pat in _SECRET_RESCAN:
        m = pat.search(text)
        if m:
            return m.group(0)
    # Privacy axis — project names, codenames, foreign-repo paths.
    # Cheap: only runs if the credential axis missed, and the file is small.
    for pat in _load_privacy_patterns():
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


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

    # Defense layer 2 on legacy path too — never trust an inbound payload
    if _scan_for_secret(payload):
        return {"ledger_added": 0, "bb_added": 0, "tasks_added": 0}

    return _merge_payload_into_local(tmp_dir, payload)


# ---------------------------------------------------------------------------
# Approach B — per-device shards (default 2026-08-03, conflict-safe)
# ---------------------------------------------------------------------------

def _sanitize_device_name(device: str) -> str:
    """Make `device` safe as a filename component (no path traversal, no ext).

    Allows [A-Za-z0-9._-], lowercases, strips leading dots. Empty → 'unknown'.
    """
    if not device:
        return "unknown"
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", device).lstrip(".").lower()
    return cleaned or "unknown"


def _collect_local_state(tmp_dir: Path) -> dict:
    """Read ledger + blackboard + task-board from tmp_dir. Returns raw dicts."""
    ledger_entries = []
    if (tmp_dir / "memory-ledger.jsonl").is_file():
        ledger_entries = memory_ledger.MemoryLedger(
            tmp_dir / "memory-ledger.jsonl")._load_all()

    bb_messages = []
    if (tmp_dir / "blackboard.jsonl").is_file():
        bb_messages = blackboard.Blackboard(
            tmp_dir / "blackboard.jsonl").read(limit=10000)

    task_state = {"tasks": [], "version": 1}
    if (tmp_dir / "task-board.json").is_file():
        try:
            task_state = json.loads(
                (tmp_dir / "task-board.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return {"ledger": ledger_entries, "blackboard": bb_messages,
            "task_board": task_state}


def _scan_for_secret(state: Any) -> str | None:
    """Defense layer 2 — scan every string field of state for secret patterns.

    Returns the first match found, or None. We scan summary/body/files/tags
    because those are the user/agent-authored fields where a leak would land.

    Resilient: if state is not a dict (corrupt shard, double-encoded string,
    etc.), we scan the raw stringified form as a last line of defense and
    never raise — a malformed shard should be skipped, not crash import.
    """
    if not isinstance(state, dict):
        # Last-resort: scan whatever it is as a string
        return _find_secret(str(state))
    for entry in state.get("ledger", []):
        hit = (_find_secret(entry.get("summary", ""))
               or _find_secret(" ".join(str(f) for f in entry.get("files", []))))
        if hit:
            return hit
        for tag in entry.get("tags", []) or []:
            hit = _find_secret(str(tag))
            if hit:
                return hit
    for msg in state.get("blackboard", []):
        hit = (_find_secret(msg.get("body", ""))
               or _find_secret(msg.get("from", ""))
               or _find_secret(msg.get("to", "")))
        if hit:
            return hit
    for task in state.get("task_board", {}).get("tasks", []):
        hit = (_find_secret(task.get("goal", ""))
               or _find_secret(task.get("claimant", "")))
        if hit:
            return hit
    return None


def export_shard(
    tmp_dir: Path | str,
    sync_dir: Path | str,
    device: str | None = None,
) -> dict:
    """Write THIS device's current local state to .tmp-sync/<device>.jsonl.

    Conflict-safe: only writes <device>.jsonl (never other devices' files).
    Overwrite-with-dedup: re-exporting the same device overwrites its own shard
    with the current snapshot, deduped by (session_id, summary) / task id.

    Defense layer 2: if any secret-looking substring is found, returns
    {"blocked": True, "reason": ...} and writes NOTHING.

    This function never calls import_* (loop guard, R3).
    """
    tmp_dir = Path(tmp_dir)
    sync_dir = Path(sync_dir)
    sync_dir.mkdir(parents=True, exist_ok=True)

    device_name = _sanitize_device_name(device or _device_id())
    state = _collect_local_state(tmp_dir)

    # Defense layer 2 — refuse to ship secrets (Iron Law #6)
    leaked = _scan_for_secret(state)
    if leaked:
        return {"blocked": True,
                "reason": f"secret-like pattern detected in local state: "
                          f"{leaked[:8]}*** — refusing to write shard "
                          f"(Iron Law #6). Scrub the source entry first."}

    # Dedup within this device's snapshot
    seen_keys: set = set()
    deduped_ledger = []
    for e in state["ledger"]:
        k = _entry_key(e)
        if k not in seen_keys:
            seen_keys.add(k)
            deduped_ledger.append(e)

    seen_bb_keys: set = set()
    deduped_bb = []
    for m in state["blackboard"]:
        k = _entry_key(m)
        if k not in seen_bb_keys:
            seen_bb_keys.add(k)
            deduped_bb.append(m)

    seen_task_keys: set = set()
    deduped_tasks = []
    for t in state["task_board"].get("tasks", []):
        k = _task_key(t)
        if k and k not in seen_task_keys:
            seen_task_keys.add(k)
            deduped_tasks.append(t)

    payload = {
        "ledger": deduped_ledger,
        "blackboard": deduped_bb,
        "task_board": {"tasks": deduped_tasks, "version": 1},
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_device": device_name,
    }

    shard_path = sync_dir / f"{device_name}.jsonl"
    # Atomic overwrite of THIS device's shard only.
    # atomic_write already json.dumps() — pass the dict, not a pre-serialized
    # string, to avoid double-encoding.
    atomic_json.atomic_write(shard_path, payload, indent=2)

    return {
        "device": device_name,
        "shard": str(shard_path),
        "ledger_entries": len(deduped_ledger),
        "bb_messages": len(deduped_bb),
        "tasks": len(deduped_tasks),
    }


def import_all_shards(
    tmp_dir: Path | str,
    sync_dir: Path | str,
) -> dict[str, int]:
    """Read every .tmp-sync/<device>.jsonl and merge (set-union) into .tmp/.

    Additive + idempotent. NEVER reads payload.json (legacy Approach A) — that
    file is ignored on purpose to avoid double-merging.
    """
    tmp_dir = Path(tmp_dir)
    sync_dir = Path(sync_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    total = {"ledger_added": 0, "bb_added": 0, "tasks_added": 0}
    if not sync_dir.is_dir():
        return total

    # Sort for deterministic ordering; only <device>.jsonl files
    shard_files = sorted(p for p in sync_dir.glob("*.jsonl")
                         if p.name != "payload.jsonl")
    for shard in shard_files:
        try:
            payload = json.loads(shard.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        # Defense layer 2 on import too — never trust an inbound shard
        if _scan_for_secret(payload):
            continue
        # Reuse the well-tested single-payload merger for each shard
        per = _merge_payload_into_local(tmp_dir, payload)
        total["ledger_added"] += per["ledger_added"]
        total["bb_added"] += per["bb_added"]
        total["tasks_added"] += per["tasks_added"]
    return total


def _merge_payload_into_local(tmp_dir: Path, payload: dict) -> dict[str, int]:
    """Merge one payload dict into local .tmp/. Factored out of import_state."""
    # --- Merge ledger ---
    ledger_added = 0
    ledger_path = tmp_dir / "memory-ledger.jsonl"
    local_ledger = memory_ledger.MemoryLedger(ledger_path)
    local_keys = {_entry_key(e) for e in local_ledger._load_all()}
    for entry in payload.get("ledger", []):
        if _entry_key(entry) not in local_keys:
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
            atomic_json.atomic_append_jsonl(bb_path, msg)
            local_bb_keys.add(_entry_key(msg))
            bb_added += 1

    # --- Merge task board (todo only, never override local claims) ---
    tasks_added = 0
    tasks_path = tmp_dir / "task-board.json"
    remote_tasks = payload.get("task_board", {}).get("tasks", [])
    if remote_tasks:
        board = task_board.TaskBoard(tasks_path)
        local_tasks = board.list()
        local_task_keys = {_task_key(t) for t in local_tasks}

        def mutate(state: dict) -> Any:
            nonlocal tasks_added
            for t in remote_tasks:
                if _task_key(t) and _task_key(t) not in local_task_keys:
                    if t.get("status") == "todo":
                        state.setdefault("tasks", []).append(t)
                        local_task_keys.add(_task_key(t))
                        tasks_added += 1
            return state

        atomic_json.atomic_update(tasks_path, mutate,
                                  missing_default=board._empty_state())

    return {"ledger_added": ledger_added, "bb_added": bb_added,
            "tasks_added": tasks_added}


def _device_id() -> str:
    """Best-effort device identifier (hostname + user)."""
    import os
    import socket
    try:
        return f"{os.environ.get('USER', os.environ.get('USERNAME', '?'))}@{socket.gethostname()}"
    except Exception:
        return "unknown-device"


# ---------------------------------------------------------------------------
# CLI — `python scripts/lib/cross_device_sync.py --export|--import`
# ---------------------------------------------------------------------------
def _cli() -> int:
    """Command-line entrypoint for manual and cron-driven sync.

    Usage:
      python scripts/lib/cross_device_sync.py --export [--device win]
      python scripts/lib/cross_device_sync.py --import
      python scripts/lib/cross_device_sync.py --export --device win --import

    Env overrides:
      AWIKI_TMP_DIR     default .tmp/   (default: <repo>/.tmp)
      AWIKI_SYNC_DIR    default .tmp-sync/ (default: <repo>/.tmp-sync)
      AWIKI_SYNC_DEVICE default device name (default: auto-detect)
    """
    import argparse
    import os

    repo_root = Path(__file__).resolve().parents[2]
    default_tmp = Path(os.environ.get("AWIKI_TMP_DIR", repo_root / ".tmp"))
    default_sync = Path(os.environ.get("AWIKI_SYNC_DIR", repo_root / ".tmp-sync"))
    default_device = os.environ.get("AWIKI_SYNC_DEVICE") or _device_id()

    ap = argparse.ArgumentParser(
        prog="cross_device_sync",
        description="Sync Neural Spine state (.tmp/) across machines via "
                    "git-tracked shards (.tmp-sync/*.jsonl).")
    ap.add_argument("--export", action="store_true",
                    help="Write this device's shard to .tmp-sync/<device>.jsonl")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="Merge every .tmp-sync/*.jsonl into local .tmp/")
    ap.add_argument("--device", default=default_device,
                    help=f"Device name (default: {default_device})")
    ap.add_argument("--tmp-dir", default=str(default_tmp),
                    help=f"Local state dir (default: {default_tmp})")
    ap.add_argument("--sync-dir", default=str(default_sync),
                    help=f"Sync shard dir (default: {default_sync})")
    args = ap.parse_args()

    if not args.export and not args.do_import:
        ap.print_help()
        return 2

    tmp_dir = Path(args.tmp_dir)
    sync_dir = Path(args.sync_dir)

    if args.export:
        result = export_shard(tmp_dir, sync_dir, device=args.device)
        if result.get("blocked"):
            print(f"BLOCKED: {result['reason']}", file=sys.stderr)
            return 1  # never commit a blocked export
        print(f"[export] device={result['device']} "
              f"ledger={result['ledger_entries']} "
              f"blackboard={result['bb_messages']} "
              f"tasks={result['tasks']} → {result['shard']}")

    if args.do_import:
        result = import_all_shards(tmp_dir, sync_dir)
        print(f"[import] ledger+={result['ledger_added']} "
              f"blackboard+={result['bb_added']} "
              f"tasks+={result['tasks_added']}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
