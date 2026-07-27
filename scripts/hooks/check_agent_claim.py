#!/usr/bin/env python3
"""check_agent_claim.py — PreToolUse: stop two agents building the same thing.

MANDATORY GATE. Blocks (exit 2) an Edit/Write that lands inside ANOTHER agent's
live work claim, and tells you who holds it, what they are building, which phase
they are in, and how to reach them.

Why it is a hard block and check_a_focus is only advisory
--------------------------------------------------------
check_a_focus guesses at intent ("you are in DESIGN but writing code") and can be
wrong, so it warns. This one asserts a fact ("zcode registered skills/awiki/** 20
minutes ago and is in IMPLEMENT"), and the cost of ignoring it is two agents
silently duplicating hours of work — which is exactly what happened on
2026-07-27 and is why this file exists.

Unclaimed work on a SHARED surface is a warning, not a block: claiming is the
habit being built, and blocking every first edit of a session would deadlock the
very tool needed to create the claim.

Escape hatches, all loud:
  HOOK_SKIP=check_agent_claim
  AWIKI_CLAIM_GATE=0
  AWIKI_AGENT=<name>          override the detected agent identity
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

GATE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Surfaces where two agents colliding is expensive and has actually happened.
# Editing these without a claim earns a warning; editing them inside someone
# else's claim is blocked.
SHARED_SURFACES = (
    "skills/", "scripts/skills_registry/", "scripts/hooks/", "scripts/lib/",
    "commands/", "agents/", "skills-registry.json", "AGENTS.md",
    ".claude/settings.json", ".codex/hooks.json",
)


def _utf8_streams() -> None:
    for s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def detect_agent() -> str:
    """Best-effort agent identity. Explicit override always wins."""
    explicit = os.environ.get("AWIKI_AGENT", "").strip()
    if explicit:
        return explicit
    for env, name in (
        ("ZCODE_SESSION_ID", "zcode"),
        ("CLAUDE_SESSION_ID", "claude"),
        ("CODEX_SESSION_ID", "codex"),
        ("GEMINI_SESSION_ID", "gemini"),
    ):
        if os.environ.get(env):
            return name
    return "unknown"


def is_shared_surface(path: str) -> bool:
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p.startswith(SHARED_SURFACES)


def main() -> int:
    _utf8_streams()

    if os.environ.get("AWIKI_CLAIM_GATE", "1") == "0":
        sys.stderr.write("🤝 Claim gate: BYPASSED (AWIKI_CLAIM_GATE=0)\n")
        return 0
    if "check_agent_claim" in os.environ.get("HOOK_SKIP", ""):
        sys.stderr.write("🤝 Claim gate: BYPASSED (HOOK_SKIP)\n")
        return 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name", "") not in GATE_TOOLS:
        return 0
    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return 0

    try:
        import agent_claims as ac
    except Exception:
        return 0  # fail open — a broken store must never wedge the repo

    me = detect_agent()

    try:
        other = ac.collision(file_path, agent=me)
    except Exception:
        return 0

    if other:
        mins = max(0, int((other["lease_until"] - __import__("time").time()) / 60))
        sys.stderr.write(
            f"🛑 CLAIM COLLISION — `{other['agent']}` กำลังทำงานบนไฟล์นี้อยู่\n\n"
            f"  ไฟล์ที่จะแก้ : {file_path}\n"
            f"  ผู้ถือ claim : {other['agent']}  (phase: {other['phase']}, เหลือ {mins} นาที)\n"
            f"  เขากำลังทำ  : {other['goal']}\n"
            f"  scope       : {', '.join(other['scope'])}\n\n"
            f"ทางเลือก:\n"
            f"  1. คุยก่อน  → MCP `bb_post` to=\"{other['agent']}\" บอกว่าจะแตะอะไร\n"
            f"  2. รอ       → MCP `claim_list` ดูว่าปล่อยหรือยัง\n"
            f"  3. แก้ที่อื่น → เลือกไฟล์ที่ไม่อยู่ใน scope เขา\n"
            f"  4. ถ้าแน่ใจว่าไม่ชน → HOOK_SKIP=check_agent_claim (บันทึกเหตุผลด้วย)\n\n"
            f"เหตุผลที่ block: 2026-07-27 มี agent 2 ตัวสร้าง intent-router ตัวเดียวกัน\n"
            f"พร้อมกันหลายชั่วโมงโดยไม่รู้ตัว — gate นี้มีไว้กันเรื่องนั้นซ้ำ\n"
        )
        return 2

    # Unclaimed work on a shared surface — nudge, do not block.
    if is_shared_surface(file_path):
        try:
            mine = [c for c in ac.live() if c.get("agent") == me]
        except Exception:
            mine = []
        if not mine:
            sys.stderr.write(
                f"🤝 ยังไม่ได้ประกาศ claim — กำลังแก้ shared surface ({file_path})\n"
                f"   agent อื่นจะไม่รู้ว่าคุณทำอะไรอยู่ และอาจทำซ้ำ\n"
                f"   ประกาศ: MCP `claim_acquire` agent=\"{me}\" "
                f"scope=[...] goal=\"<done criteria>\"\n"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
