#!/usr/bin/env python3
"""check_a_focus.py — PreToolUse focus guard for the A-Suite (ADVISORY).

Warns when a write happens outside the phase the session declared via the MCP
`focus_set` tool. Exits 0 — it nudges, it does not block.

Why advisory and not a hard gate like check_cost_tier
-----------------------------------------------------
1. There is no safe allowlist. The DESIGN and ASK phases legitimately write
   files — ADRs, specs, plan documents. A gate that blocks writes during those
   phases fails on exactly the work it exists to protect. check_cost_tier can
   get away with blocking because its remediation is a single Bash command and
   Bash is exempt; there is no equivalent one-liner here.

2. .gemini/settings.json wires BeforeTool with matcher "*" to a bare
   `hooks_runner.py` with no hook name, which runs EVERY file in scripts/hooks/
   on EVERY Gemini tool call. A new hook with an unguarded exit-2 path would be
   a repo-wide hazard, not a local one.

Enforcement is opt-in: AWIKI_FOCUS_ENFORCE=1 upgrades the warning to exit 2.
The real backstop is a_focus_stop.py, which reports unfinished phases when the
session ends — cheap, once per session, and impossible to false-positive into a
blocked edit.

Fails open on every unexpected condition.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Only writes are interesting. Read/Grep/Glob/Bash are how you investigate, and
# investigation is legal in every phase.
GATE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Phases in which writing production code is the point.
CODE_PHASES = {"implement", "debug", "test", "review"}

# Paths that are legitimate output of ANY phase — docs, notes, scratch state.
# Without this, ASK/DESIGN would warn on the ADR the agent was told to write.
ALWAYS_OK_SUFFIXES = (".md", ".txt", ".rst")
ALWAYS_OK_PREFIXES = ("docs/", "wiki/", ".tmp/", "decisions/", "journal/", "exports/")


def _utf8_streams() -> None:
    """Windows consoles default to cp874/cp1252 — mandatory before Thai output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _focus_dir() -> Path:
    override = os.environ.get("AWIKI_FOCUS_DIR")
    return Path(override) if override else REPO_ROOT / ".tmp"


def _session_id() -> str:
    return (
        os.environ.get("ZCODE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or "mcp"
    )


def read_focus() -> dict | None:
    path = _focus_dir() / f"a-focus-{re.sub(r'[^A-Za-z0-9_-]', '_', _session_id())}.json"
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else None
    except (OSError, ValueError):
        return None   # corrupt state must not wedge the session


def is_always_ok(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    # NOT lstrip("./") — that strips a CHARACTER SET, so ".tmp/x.json" would
    # lose its leading dot and stop matching the ".tmp/" prefix.
    if norm.startswith("./"):
        norm = norm[2:]
    if norm.startswith(ALWAYS_OK_PREFIXES):
        return True
    return norm.lower().endswith(ALWAYS_OK_SUFFIXES)


def main() -> int:
    _utf8_streams()

    if "check_a_focus" in os.environ.get("HOOK_SKIP", ""):
        return 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name", "") not in GATE_TOOLS:
        return 0

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path or is_always_ok(file_path):
        return 0

    state = read_focus()
    if not state:
        return 0

    phase = state.get("phase")
    if not phase or phase in CODE_PHASES:
        return 0

    goal = state.get("goal") or "(no goal recorded)"
    skill = state.get("skill") or "?"
    enforce = os.environ.get("AWIKI_FOCUS_ENFORCE", "") == "1"

    sys.stderr.write(
        f"🎯 FOCUS: กำลังอยู่ phase '{phase}' ({skill}) แต่เขียนโค้ดแล้ว — {file_path}\n"
        f"   goal: {goal}\n"
        f"   phase '{phase}' คือขั้นถาม/ออกแบบ ยังไม่ใช่ขั้นลงมือ\n"
        f"   ถ้าจบขั้นนี้แล้ว → เรียก MCP `focus_advance` ก่อนเขียนต่อ\n"
        f"   ถ้าตั้งใจเขียนตอนนี้ → เขียนได้เลย (นี่เป็นแค่คำเตือน)\n"
    )
    if enforce:
        sys.stderr.write("   ⛔ AWIKI_FOCUS_ENFORCE=1 — blocked\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
