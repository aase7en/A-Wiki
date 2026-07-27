"""a_flow_state.py — state manager for A-Flow pipeline + A-Router focus_set API.

This is the foundation lib that connects:
  - Opus5's category bundles (a-web, a-content, a-invest, a-research, a-router)
    which all call `focus_set` / `focus_advance` / `focus_clear`.
  - A-Flow pipeline (7-stage: ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST).
  - check_a_flow_discipline hook (reads state to enforce stage gates).
  - check_a_route hook (reads category dispatch table).

State file: .tmp/a-flow.json (atomic write, survives context compaction).

Schema:
    {
        "active": bool,           # is A-Flow / category pack running?
        "skill": "a-web"|"a-doc"|...,   # which category bundle owns this run
        "goal": "<one-line done criteria>",
        "phase": "ask"|"design"|"plan"|"implement"|"review"|"debug"|"test",
        "allowed_files": ["src/auth.ts", "tests/auth.test.ts"],
        "started_ts": 1784955460,
        "completed_phases": ["ask", "design"],
        "notes": [
            "ADR-001: chose JWT over session",
            "grill Q3 answer: refresh rate = real-time"
        ]
    }

API (deliberately matches Opus5's spec):
    focus_set(skill, goal, phase="ask", allowed_files=None) → None
    focus_advance(to_phase=None) → None    # auto-next if None
    focus_clear() → None                   # end run
    get_state() → dict                     # read current
    is_active() → bool
    current_phase() → str | None
    is_edit_allowed(file_path) → bool      # gate check
    add_note(text) → None
    allow_file(file_path) → None           # add to allowed_files mid-run

All operations are fail-safe: any exception returns a safe default (no-op or
empty state), never raises. This is critical because the lib is called from
hooks that must never crash a tool call.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = REPO_ROOT / ".tmp" / "a-flow.json"

# 7-stage spine (lowercase — phase field uses lowercase)
PHASES = ["ask", "design", "plan", "implement", "review", "debug", "test"]

# Phases where Edit/Write is FORBIDDEN (must finish PLAN first)
PRE_IMPLEMENT_PHASES = {"ask", "design", "plan"}


# ── internal helpers ──────────────────────────────────────────────────────

def _empty_state() -> dict[str, Any]:
    return {
        "active": False,
        "skill": None,
        "goal": None,
        "phase": None,
        "allowed_files": [],
        "started_ts": None,
        "completed_phases": [],
        "notes": [],
    }


def _atomic_write(path: Path, content: str) -> None:
    """Atomic write: temp file + os.replace (crash-safe)."""
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".a-flow-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _validate_phase(phase: str) -> str:
    """Raise ValueError if phase is invalid (caller must catch)."""
    if phase not in PHASES:
        raise ValueError(
            f"invalid phase '{phase}'; valid: {PHASES}"
        )
    return phase


# ── public API ────────────────────────────────────────────────────────────

def get_state() -> dict[str, Any]:
    """Read current state. Fail-safe: returns empty state on any error."""
    try:
        if not STATE_FILE.is_file():
            return _empty_state()
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # Migrate missing fields (forward-compat)
        empty = _empty_state()
        for k, v in empty.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _empty_state()


def is_active() -> bool:
    """Is A-Flow / category pack currently running?"""
    return bool(get_state().get("active"))


def current_phase() -> str | None:
    """Current phase (lowercase) or None if inactive."""
    s = get_state()
    if not s.get("active"):
        return None
    return s.get("phase")


def focus_set(
    *,
    skill: str,
    goal: str,
    phase: str = "ask",
    allowed_files: list[str] | None = None,
) -> None:
    """Start a new A-Flow / category run.

    Args:
        skill: bundle name (e.g. "a-web", "a-doc", "a-flow" for generic)
        goal: one-line done criteria (what success looks like)
        phase: starting phase (default "ask")
        allowed_files: files the run is allowed to edit (PLAN+ phases enforce)
    """
    try:
        _validate_phase(phase)
        state = {
            "active": True,
            "skill": skill,
            "goal": goal,
            "phase": phase,
            "allowed_files": list(allowed_files or []),
            "started_ts": int(time.time()),
            "completed_phases": [],
            "notes": [],
        }
        _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        # Best-effort: write error to stderr but never raise (called from hooks)
        import sys
        sys.stderr.write(f"[a_flow_state.focus_set] error: {e}\n")


def focus_advance(to_phase: str | None = None) -> None:
    """Advance to next phase. If to_phase is None, picks the next in PHASES order.

    Records completed phase + updates state.
    """
    try:
        state = get_state()
        if not state.get("active"):
            return
        current = state.get("phase")
        if to_phase is None:
            if current is None or current not in PHASES:
                return
            idx = PHASES.index(current)
            if idx + 1 >= len(PHASES):
                # Last phase — auto-clear
                focus_clear()
                return
            to_phase = PHASES[idx + 1]
        _validate_phase(to_phase)
        # Mark current as completed
        if current and current not in state.get("completed_phases", []):
            state.setdefault("completed_phases", []).append(current)
        state["phase"] = to_phase
        _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        import sys
        sys.stderr.write(f"[a_flow_state.focus_advance] error: {e}\n")


def focus_clear() -> None:
    """End the current run — deactivate state."""
    try:
        state = get_state()
        if state.get("phase") and state["phase"] not in state.get("completed_phases", []):
            state.setdefault("completed_phases", []).append(state["phase"])
        state["active"] = False
        state["phase"] = None
        _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        import sys
        sys.stderr.write(f"[a_flow_state.focus_clear] error: {e}\n")


def is_edit_allowed(file_path: str) -> bool:
    """Hook gate check: is editing this file allowed at current phase?

    Rules:
      - If not active → allow (A-Flow not running)
      - If phase in PRE_IMPLEMENT_PHASES (ask/design/plan) → DENY (hook will block)
      - If allowed_files is non-empty → must contain file_path
      - If allowed_files is empty (PLAN didn't enumerate) → allow all (best-effort)
      - Files under .tmp/ always allowed (state file writes)
    """
    try:
        # Normalize path — strip only "./" prefix (NOT lstrip which is char-based)
        norm = file_path.replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        # .tmp/ always allowed (state writes, scratch)
        if norm.startswith(".tmp/") or norm == ".tmp":
            return True

        state = get_state()
        if not state.get("active"):
            return True

        phase = state.get("phase")
        if phase in PRE_IMPLEMENT_PHASES:
            return False  # hook will block with explanation

        allowed = state.get("allowed_files", [])
        if not allowed:
            return True  # PLAN didn't enumerate — be permissive

        # Match (prefix-aware so "src/" allows "src/auth.ts")
        for a in allowed:
            a_norm = a.replace("\\", "/")
            while a_norm.startswith("./"):
                a_norm = a_norm[2:]
            if norm == a_norm:
                return True
            # prefix match: "src/" matches "src/auth.ts"
            stripped = a_norm.rstrip("/")
            if stripped and norm.startswith(stripped + "/"):
                return True
        return False
    except Exception:
        return True  # fail-open


def add_note(text: str) -> None:
    """Append a note (ADR, decision, grill answer) to state."""
    try:
        state = get_state()
        state.setdefault("notes", []).append(text)
        _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        import sys
        sys.stderr.write(f"[a_flow_state.add_note] error: {e}\n")


def allow_file(file_path: str) -> None:
    """Add a file to allowed_files (mid-run expansion)."""
    try:
        state = get_state()
        allowed = state.setdefault("allowed_files", [])
        if file_path not in allowed:
            allowed.append(file_path)
        _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        import sys
        sys.stderr.write(f"[a_flow_state.allow_file] error: {e}\n")


# ── CLI (for testing + manual ops) ────────────────────────────────────────

def _cli() -> int:
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "status":
        s = get_state()
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    elif cmd == "set" and len(sys.argv) >= 4:
        focus_set(skill=sys.argv[2], goal=sys.argv[3])
        print(f"✓ focus_set: skill={sys.argv[2]} goal={sys.argv[3]}")
        return 0
    elif cmd == "advance":
        to = sys.argv[2] if len(sys.argv) > 2 else None
        focus_advance(to)
        print(f"✓ focus_advance → {to or 'next'}")
        return 0
    elif cmd == "clear":
        focus_clear()
        print("✓ focus_clear")
        return 0
    else:
        print(f"unknown command: {cmd}")
        print("commands: status, set <skill> <goal>, advance [phase], clear")
        return 2


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
