#!/usr/bin/env python3
"""
event_logger.py — Append a JSON event to .tmp/live-events.jsonl
Used by hooks and delegate.sh to feed the A-Wiki Live Dashboard.

Every event now carries session/task/agent IDs for the workflow graph feature
(Step 1 of dashboard-v2 — see handoff.md).

CLI: python3 scripts/live-dashboard/event_logger.py <type> [key=value ...]

Examples:
  python3 event_logger.py session_start
  python3 event_logger.py delegate_start model=gemini-2.5-flash task=lookup
  python3 event_logger.py hook_check hook=check_cost_tier tool=Edit result=pass tier=L4
  python3 event_logger.py agent_spawn agent_role=architect model=deepseek-v4-flash:free
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
MAX_LINES = 1000

# ── Session ID cache ──────────────────────────────────────────────
_SESSION_ID_FILE = REPO_ROOT / ".tmp" / ".live-dashboard-session-id"
_session_id_cache: str | None = None


def _get_session_id() -> str:
    """Return a stable session_id for this process lifetime.
    Persisted to .tmp/.live-dashboard-session-id for cross-process sharing."""
    global _session_id_cache
    if _session_id_cache is not None:
        return _session_id_cache

    # Try persisted file first (cross-process: Cline hooks → subprocess)
    try:
        if _SESSION_ID_FILE.exists():
            sid = _SESSION_ID_FILE.read_text().strip()
            if sid:
                _session_id_cache = sid
                return sid
    except Exception:
        pass

    # Generate new
    sid = f"sess-{uuid.uuid4().hex[:12]}"
    try:
        _SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SESSION_ID_FILE.write_text(sid)
    except Exception:
        pass
    _session_id_cache = sid
    return sid


# ── Agent ID cache ────────────────────────────────────────────────
_agent_id_cache: str | None = None


def _get_agent_id() -> str:
    """Return a stable agent_id for this process."""
    global _agent_id_cache
    if _agent_id_cache is None:
        _agent_id_cache = f"agent-{uuid.uuid4().hex[:8]}"
    return _agent_id_cache


# ── Task tracking ─────────────────────────────────────────────────
_TASK_STACK: list[str] = []


def push_task(task_id: str) -> None:
    """Push a task onto the stack (call from TaskStart hook)."""
    _TASK_STACK.append(task_id)


def pop_task() -> str | None:
    """Pop a completed task (call from TaskComplete hook)."""
    if _TASK_STACK:
        return _TASK_STACK.pop()
    return None


def _current_task_id() -> str | None:
    """Return the innermost active task_id, or None."""
    if _TASK_STACK:
        return _TASK_STACK[-1]
    return None


def _parent_task_id() -> str | None:
    """Return the parent task_id (second from top), or None."""
    if len(_TASK_STACK) >= 2:
        return _TASK_STACK[-2]
    return None


# ── Default agent role ────────────────────────────────────────────
_DEFAULT_AGENT_ROLE = os.environ.get("AWIKI_AGENT_ROLE", "primary")


# ── Core log function ─────────────────────────────────────────────

def log(event_type: str, **kwargs: str) -> None:
    """Append one JSON event to the event log.

    Injects session_id, agent_id, agent_role, task_id, and parent_task_id
    automatically unless the caller overrides them explicitly.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Auto-inject IDs if not provided by caller
    kwargs.setdefault("session_id", _get_session_id())
    kwargs.setdefault("agent_id", _get_agent_id())
    kwargs.setdefault("agent_role", _DEFAULT_AGENT_ROLE)
    kwargs.setdefault("task_id", _current_task_id())
    kwargs.setdefault("parent_task_id", _parent_task_id())

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
    kwargs: dict[str, str] = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        else:
            kwargs.setdefault("value", arg)
    log(evt_type, **kwargs)