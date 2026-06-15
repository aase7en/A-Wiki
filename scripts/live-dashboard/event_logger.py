#!/usr/bin/env python3
"""
event_logger.py — Append a JSON event to .tmp/live-events.jsonl
Used by hooks and delegate.sh to feed the A-Wiki Live Dashboard.

CLI: python3 scripts/live-dashboard/event_logger.py <type> [key=value ...]

Examples:
  python3 event_logger.py session_start
  python3 event_logger.py delegate_start model=gemini-2.5-flash task=lookup
  python3 event_logger.py hook_check hook=check_cost_tier tool=Edit result=pass tier=L4
"""
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
MAX_LINES = 1000


def log(event_type: str, **kwargs) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": round(time.time(), 3), "type": event_type, **kwargs}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Rotate to keep file bounded
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_LINES:
            LOG_FILE.write_text("\n".join(lines[-MAX_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(0)
    evt_type = sys.argv[1]
    kwargs: dict = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        else:
            kwargs.setdefault("value", arg)
    log(evt_type, **kwargs)
