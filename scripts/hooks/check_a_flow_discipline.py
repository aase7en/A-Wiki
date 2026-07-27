"""check_a_flow_discipline.py — PreToolUse hook enforcing A-Flow stage gates.

When A-Flow / category pack is active (focus_set called), this hook blocks
Edit/Write/MultiEdit if:
  - Current phase is in {ask, design, plan} (PRE-IMPLEMENT — must finish PLAN first)
  - Phase is implement+ but target file is not in state.allowed_files

Allow (auto-skip):
  - HOOK_SKIP=check_a_flow_discipline (opt-out)
  - Non-edit tools (Bash, Read, Glob, Grep, TodoWrite, WebFetch, WebSearch)
  - Trivial edits (typo, comment-only, whitespace-only, <5 char change)
  - Files under .tmp/* (state writes)
  - A-Flow not active (state.active == False)

Block message includes:
  - Current phase + what's missing
  - 1-line remedy (advance to next phase)
  - Override hint

Exit codes (per hooks_runner convention):
  0 = pass
  2 = BLOCK
  other = error (reported but not blocking)

Iron Law: NO IMPLEMENTATION WITHOUT PLAN APPROVED FIRST.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Windows console UTF-8 (Thai messages render correctly)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import a_flow_state  # noqa: E402

# Tools that are NEVER blocked (navigation/read/state-mgmt)
EXEMPT_TOOLS = {
    "Bash", "Read", "Glob", "Grep", "TodoWrite", "WebFetch", "WebSearch",
    "Task", "Agent",  # subagent dispatch — let it through, discipline is on the edits
}

# Tools that ARE subject to discipline
GATE_TOOLS = {"Edit", "Write", "MultiEdit"}

# Trivial edit patterns — auto-skip (don't block)
TRIVIAL_PATTERNS = [
    # Whitespace-only change
    (re.compile(r"^[\s\n]+$", re.MULTILINE), "whitespace-only"),
    # Comment-only (line starts with //, #, --, /* */, depending on lang)
    (re.compile(r"^(//|#|--|;\s*\*).*$", re.MULTILINE), "comment-only"),
]

# Diff size threshold for "trivial" (< N chars changed)
TRIVIAL_DIFF_CHARS = 5


def _is_trivial_edit(tool_name: str, tool_input: dict) -> bool:
    """Classify whether this edit is too small to enforce stage gate on."""
    try:
        if tool_name == "Write":
            content = tool_input.get("content", "")
            return len(content.strip()) < TRIVIAL_DIFF_CHARS
        elif tool_name == "Edit":
            new_str = tool_input.get("new_string", "")
            old_str = tool_input.get("old_string", "")
            # Pure whitespace / single-line comment
            for pattern, label in TRIVIAL_PATTERNS:
                if pattern.match(new_str) and pattern.match(old_str):
                    return True
            # Diff < N chars (typo fix)
            diff_size = abs(len(new_str) - len(old_str))
            return diff_size < TRIVIAL_DIFF_CHARS and len(new_str) < 30
        elif tool_name == "MultiEdit":
            edits = tool_input.get("edits", [])
            if not edits:
                return True
            # Trivial only if ALL edits are trivial
            return all(
                _is_trivial_edit("Edit", {"new_string": e.get("new_string", ""),
                                          "old_string": e.get("old_string", "")})
                for e in edits
            )
    except Exception:
        return False  # fail-safe: not trivial = subject to gate
    return False


def _block_message(phase: str, file_path: str, allowed_files: list[str]) -> str:
    """Build user-facing block message (Thai + English mix per repo convention)."""
    next_steps = []
    if phase == "ask":
        next_steps.append("1. จบ ASK: restate + grill-with-docs ≥3 Qs + ได้ done-criteria")
        next_steps.append("2. ไป DESIGN และ PLAN ก่อน implement")
    elif phase == "design":
        next_steps.append("1. จบ DESIGN: ≥2 approaches + user อนุมัติ + ADR")
        next_steps.append("2. ไป PLAN ก่อน implement")
    elif phase == "plan":
        next_steps.append("1. จบ PLAN: spec + task list + allowed_files[]")
        next_steps.append('2. advance ไป IMPLEMENT: python scripts/lib/a_flow_state.py advance implement')
    elif phase in {"implement", "review", "debug", "test"}:
        # File not in allowed_files
        if allowed_files:
            sample = ", ".join(allowed_files[:3])
            next_steps.append(f'ไฟล์นี้ไม่อยู่ใน allowed_files (ตอนนี้: {sample}...)')
            next_steps.append("ระหว่าง PLAN แต่ไม่ได้ขออนุญาตไฟล์นี้ → กลับไป PLAN เพิ่ม")
        else:
            next_steps.append("allowed_files ว่าง — focus_set ใหม่พร้อม allowed_files")
    next_steps.append("")
    next_steps.append("override (emergency): HOOK_SKIP=check_a_flow_discipline")
    return (
        f"\n🛑 A-Flow discipline: อยู่ใน phase '{phase}' ห้าม Edit '{file_path}'\n\n"
        + "\n".join(next_steps)
        + "\n"
    )


def main() -> int:
    """PreToolUse hook entry point."""
    # Opt-out (Layer B pattern — surface the bypass)
    if "check_a_flow_discipline" in os.environ.get("HOOK_SKIP", ""):
        return 0

    # Read stdin (Claude Code PreToolUse payload)
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open on parse error

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only gate edit tools
    if tool_name not in GATE_TOOLS:
        return 0

    # If A-Flow not active, allow everything
    if not a_flow_state.is_active():
        return 0

    # Get target file path (different tools use different field names)
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or "<unknown>"
    )

    # Trivial edit auto-skip
    if _is_trivial_edit(tool_name, tool_input):
        return 0

    # Use lib's gate logic
    if a_flow_state.is_edit_allowed(file_path):
        return 0

    # BLOCK
    state = a_flow_state.get_state()
    phase = state.get("phase", "?")
    allowed = state.get("allowed_files", [])
    sys.stderr.write(_block_message(phase, file_path, allowed))
    return 2  # block


if __name__ == "__main__":
    sys.exit(main())
