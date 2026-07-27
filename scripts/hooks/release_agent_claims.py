#!/usr/bin/env python3
"""release_agent_claims.py — Stop hook: hand back this session's work claims.

Claims carry a TTL lease and self-reap, so this is not strictly required for
correctness — but without it a finished session keeps its scope locked for up to
an hour, and the next agent gets a collision block for work nobody is doing.

Wired DIRECTLY on Stop (not through hooks_runner, which swallows the stdout of
an exit-0 hook). Always exits 0.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))


def _utf8() -> None:
    for s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> int:
    _utf8()
    if "release_agent_claims" in os.environ.get("HOOK_SKIP", ""):
        return 0
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    sid = (
        os.environ.get("ZCODE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or ""
    )
    if not sid:
        return 0
    try:
        import agent_claims as ac
        n = ac.release_session(sid)
        if n:
            print(f"🤝 ปล่อย {n} claim ของ session นี้แล้ว — agent อื่นแก้ไฟล์เหล่านั้นได้")
        remaining = ac.live()
        if remaining:
            print("🤝 agent อื่นที่ยังทำงานอยู่:\n" + ac.describe(remaining))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
