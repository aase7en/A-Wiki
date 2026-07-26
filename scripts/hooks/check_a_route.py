#!/usr/bin/env python3
"""check_a_route.py — UserPromptSubmit: suggest the right A-Suite skill.

Matches the user's prompt against the machine-readable `triggers` in
skills-registry.json and, when something clears threshold, prints a one-line
suggestion into the session context.

WIRED DIRECTLY in .claude/settings.json — NOT through hooks_runner.py.
    hooks_runner.run_hook() calls subprocess.run(capture_output=True) and
    re-emits only stderr, and only on exit 2. A suggestion printed to stdout
    through the runner would be discarded silently. check_compaction_suggest.py
    is wired the same way for the same reason.

Claude-only by necessity: Codex has no UserPromptSubmit event, Gemini has two
events total, and Cline/Windsurf/Cursor/Aider have no hooks at all. Those
agents reach the same data through the MCP `skill_route` tool or by reading
wiki/A-ROUTER.md. This hook is a convenience layer, never the source of truth.

Always exits 0. Never blocks a prompt.
Opt out with AWIKI_A_ROUTE=0 or HOOK_SKIP=check_a_route.
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
    """Force UTF-8 on all three streams. Windows here defaults to cp874.

    STDIN MATTERS AS MUCH AS STDOUT. The hook payload is JSON containing the
    user's raw prompt, and a Thai prompt decoded as cp874 arrives as mojibake
    ('ช่วยแก้บั๊ก' -> '\\udc8a\\udc88วย...'), which matches no trigger and makes the
    hook silently useless in exactly the language it is most needed for. Only
    stdout/stderr were reconfigured at first, and the unit tests missed it
    because subprocess.run(encoding="utf-8") hid the difference.
    """
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _state_path(session_id: str) -> Path:
    """Anti-spam ladder file. Session id is sanitised — it becomes a filename."""
    base = os.environ.get("AWIKI_ROUTE_STATE_DIR")
    root = Path(base) if base else REPO_ROOT / ".tmp"
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
    return root / f"a-route-{safe}.txt"


def _last_suggested(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _remember(path: Path, value: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    _utf8_streams()

    if os.environ.get("AWIKI_A_ROUTE", "1") == "0":
        return 0
    if "check_a_route" in os.environ.get("HOOK_SKIP", ""):
        return 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return 0

    # Import after the cheap exits: the registry is 810 KB but loads in ~6 ms,
    # so no cached index is needed to stay inside the 5s hook budget.
    try:
        from skills_registry import Registry, routing
        reg = Registry.load(REPO_ROOT / "skills-registry.json")
        hits = routing.route(reg, prompt)
    except Exception:
        return 0        # a routing failure must never disturb the prompt

    if not hits:
        return 0        # nothing matched — stay silent, do NOT guess

    state = _state_path(str(data.get("session_id", "")))
    top = hits[0][0]
    if _last_suggested(state) == top:
        return 0        # already suggested this one; don't nag
    _remember(state, top)

    parts = []
    for name, _score in hits:
        skill = reg.get(name) or {}
        parts.append(skill.get("invocation_hint") or f"/{name}")

    primary, *rest = parts
    line = f"🎯 น่าจะใช้ `{primary}`"
    if rest:
        line += f" (หรือ {', '.join(f'`{p}`' for p in rest)})"
    print(f"{line} — ถ้าไม่ตรง ทำต่อได้ตามปกติ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
