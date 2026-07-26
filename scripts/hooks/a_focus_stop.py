#!/usr/bin/env python3
"""a_focus_stop.py — Stop hook: report an unfinished A-Suite focus.

This is the real backstop of the focus system. The PreToolUse guard is advisory
(see check_a_focus.py for why), so the enforcement that actually matters happens
here: a session should not end quietly while a declared goal is mid-chain.

WIRED DIRECTLY in .claude/settings.json — NOT through hooks_runner.py.
    hooks_runner.run_hook() uses subprocess.run(capture_output=True) and only
    forwards the child's stderr when it exits 2. A hook that always exits 0 is
    therefore completely invisible through the runner. That is not theoretical:
    scripts/hooks/self_audit.py always returns 0 and runs through the runner, so
    every warning it has ever produced has been swallowed. Do not re-wire this
    one through the runner.

Always exits 0. Ending a session is the user's call, never a hook's.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _focus_path() -> Path:
    override = os.environ.get("AWIKI_FOCUS_DIR")
    base = Path(override) if override else REPO_ROOT / ".tmp"
    sid = (
        os.environ.get("ZCODE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or "mcp"
    )
    return base / f"a-focus-{re.sub(r'[^A-Za-z0-9_-]', '_', sid)}.json"


def main() -> int:
    _utf8_streams()

    if "a_focus_stop" in os.environ.get("HOOK_SKIP", ""):
        return 0

    try:
        json.load(sys.stdin)          # payload unused; drain so we never block
    except Exception:
        pass

    path = _focus_path()
    if not path.exists():
        return 0
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not isinstance(state, dict):
        return 0

    phase = state.get("phase")
    if not phase or state.get("complete"):
        return 0

    try:
        from skills_registry.routing import A_PHASE_CHAIN
        chain = list(A_PHASE_CHAIN)
    except Exception:
        chain = ["ask", "design", "plan", "implement", "review", "debug", "test"]

    done = state.get("phases_done") or []
    remaining = chain[chain.index(phase):] if phase in chain else [phase]

    # stdout, because this hook is direct-wired and stdout is what reaches the user.
    print(
        f"🎯 A-FOCUS ยังไม่จบ — `{state.get('skill', '?')}` ค้างที่ phase **{phase}**\n"
        f"   goal      : {state.get('goal') or '(ไม่ได้บันทึก)'}\n"
        f"   ทำแล้ว    : {' → '.join(done) if done else '(ยังไม่มี)'}\n"
        f"   เหลือ     : {' → '.join(remaining)}\n"
        f"   เดินต่อ → MCP `focus_advance` · จบงานแล้ว → `focus_clear`"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
