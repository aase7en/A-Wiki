"""
poll.py — Report pending batch state (Tier 2/3 only).

Refreshes status against provider; updates state.jsonl. Does NOT auto-
download results — that is collect.py's job (idempotent, user-triggered).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from router import get_adapter  # noqa: E402
from state import (  # noqa: E402
    COLLECTED,
    COMPLETED,
    FAILED,
    IN_PROGRESS,
    PENDING,
    get_batch,
    list_batches,
    update_status,
)

ACTIVE = (PENDING, IN_PROGRESS)


def _refresh_one(record: dict) -> dict:
    batch_id = record["batch_id"]
    tier = int(record["tier"])
    if tier == 1:
        return record  # realtime has no remote status
    try:
        adapter = get_adapter(tier)
        status_info = adapter.poll(batch_id)
    except (RuntimeError, Exception) as e:  # noqa: BLE001
        return {**record, "poll_error": str(e)}

    provider_status = (status_info.get("status") or "").lower()
    mapped = {
        "in_progress": IN_PROGRESS,
        "validating": IN_PROGRESS,
        "finalizing": IN_PROGRESS,
        "completed": COMPLETED,
        "ended": COMPLETED,  # Anthropic uses "ended"
        "failed": FAILED,
        "expired": FAILED,
        "cancelled": FAILED,
        "canceled": FAILED,
    }.get(provider_status, IN_PROGRESS)

    if record["status"] != COLLECTED and mapped != record["status"]:
        update_status(batch_id, mapped, provider_status=provider_status)
        record["status"] = mapped
    record["provider_status"] = provider_status
    record["request_counts"] = status_info.get("request_counts", {})
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll pending A-Wiki batches")
    parser.add_argument("--batch", help="Poll a specific batch_id only")
    parser.add_argument("--all", action="store_true", help="Include completed/collected batches")
    args = parser.parse_args()

    if args.batch:
        rec = get_batch(args.batch)
        if rec is None:
            print(f"Not found: {args.batch}", file=sys.stderr)
            return 1
        refreshed = _refresh_one(rec)
        print(json.dumps(refreshed, indent=2, ensure_ascii=False))
        return 0

    records = list_batches() if args.all else [r for r in list_batches() if r.get("status") in ACTIVE]
    if not records:
        print("(no active batches)")
        return 0

    out = [_refresh_one(r) for r in records]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
