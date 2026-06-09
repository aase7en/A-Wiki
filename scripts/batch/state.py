"""
state.py — Persistent batch state on the user's drive/ layer.

Cross-device safe: state lives under drive/batch-state/, which is the
gitignored cloud-synced layer (Google Drive / iCloud / Dropbox / OneDrive
or a local fallback). Multiple machines see the same state through the
user's cloud sync.

File format: JSONL — one batch record per line. Append-only writes;
read-and-rewrite for status updates.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from drive_path import get_drive_root  # noqa: E402


PENDING = "pending"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
FAILED = "failed"
COLLECTED = "collected"


def state_dir() -> Path:
    """Return drive/batch-state/ — created on first use."""
    d = get_drive_root() / "batch-state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_file() -> Path:
    return state_dir() / "state.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_all() -> list[dict]:
    f = state_file()
    if not f.is_file():
        return []
    records: list[dict] = []
    with f.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _write_all(records: Iterable[dict]) -> None:
    f = state_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(prefix="state.", suffix=".jsonl", dir=str(f.parent))
    try:
        with open(tmp_fd, "w", encoding="utf-8") as fp:
            for r in records:
                fp.write(json.dumps(r, ensure_ascii=False) + "\n")
        Path(tmp_name).replace(f)
    except Exception:
        try:
            Path(tmp_name).unlink()
        except OSError:
            pass
        raise


def add_batch(
    *,
    batch_id: str,
    backend: str,
    tier: int,
    files: list[dict],
    input_path: str | None = None,
    status: str = PENDING,
) -> dict:
    """Append a new batch record. `files` is [{slug, raw_path, custom_id}, ...]."""
    record = {
        "batch_id": batch_id,
        "backend": backend,
        "tier": tier,
        "status": status,
        "submitted_at": now_iso(),
        "updated_at": now_iso(),
        "n_files": len(files),
        "files": files,
        "input_path": input_path,
    }
    existing = _read_all()
    if any(r.get("batch_id") == batch_id for r in existing):
        raise ValueError(f"Batch already tracked: {batch_id}")
    existing.append(record)
    _write_all(existing)
    return record


def update_status(batch_id: str, status: str, **fields) -> dict | None:
    """Patch a batch record's status and merge extra fields. Returns updated record."""
    records = _read_all()
    updated = None
    for r in records:
        if r.get("batch_id") == batch_id:
            r["status"] = status
            r["updated_at"] = now_iso()
            r.update(fields)
            updated = r
            break
    if updated is None:
        return None
    _write_all(records)
    return updated


def list_batches(status: str | None = None) -> list[dict]:
    records = _read_all()
    if status is None:
        return records
    return [r for r in records if r.get("status") == status]


def get_batch(batch_id: str) -> dict | None:
    for r in _read_all():
        if r.get("batch_id") == batch_id:
            return r
    return None


def make_local_id(prefix: str = "local") -> str:
    """Generate an id for tier-1 (realtime, no provider batch_id)."""
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect A-Wiki batch state")
    parser.add_argument("--status", help="Filter by status (pending/in_progress/completed/failed/collected)")
    parser.add_argument("--id", help="Show one batch by id")
    args = parser.parse_args()

    if args.id:
        record = get_batch(args.id)
        if record is None:
            print(f"Not found: {args.id}", file=sys.stderr)
            raise SystemExit(1)
        print(json.dumps(record, indent=2, ensure_ascii=False))
    else:
        for r in list_batches(args.status):
            print(json.dumps(r, ensure_ascii=False))
