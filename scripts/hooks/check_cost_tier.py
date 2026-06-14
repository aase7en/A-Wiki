#!/usr/bin/env python3
"""
Hook: Cost-First Tier Gate
---------------------------
Blocks Edit / Write / Agent tool calls until the agent declares which cost
tier this task belongs to.  Forces conscious cost-first thinking before any
primary-model write action.

Declaration (create once per calendar day via Bash or PowerShell):
  echo "L4|implementation|reason why primary needed" > .tmp/cost-tier-YYYY-MM-DD.txt

Tier legend:
  L1 (free / local)  — grep, FTS5, read-only, knowledge-graph lookup
  L2 (cheap)         — short summary, table, light reasoning → free/cheap model
  L3 (low-scout)     — large file scan, lint, gather intel → platform-low-scout
  L4 (primary)       — write code, complex reasoning, wiki synthesis → primary model

Skip conditions:
  - Tool is Bash / PowerShell / Read / Glob / Grep  (declaration happens there)
  - File path targets .tmp/ or cost-tier itself
  - HOOK_SKIP env contains "check_cost_tier"
  - Running in CI (CI=true env)

Exit 0 = pass
Exit 2 = block (no tier declaration for today)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Allow tests to override the tmp dir without touching the real .tmp/
TMP_DIR = Path(os.environ.get("AWIKI_COST_GATE_TMP_DIR", str(REPO_ROOT / ".tmp")))

# These tools require a cost declaration before running
GATE_TOOLS = {"Edit", "Write", "MultiEdit", "Agent", "NotebookEdit"}

# These tools are exempt — declaration lives here
EXEMPT_TOOLS = {"Bash", "PowerShell", "Read", "Glob", "Grep", "ToolSearch"}


def declaration_path(today: str) -> Path:
    return TMP_DIR / f"cost-tier-{today}.txt"


def read_declaration(today: str) -> str | None:
    path = declaration_path(today)
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8").strip()
        return content if content else None
    except Exception:
        return None


def is_tmp_write(tool: str, tool_input: dict) -> bool:
    """Return True when the write targets .tmp/ — exempt so agent can declare."""
    if tool not in ("Edit", "Write"):
        return False
    fpath = tool_input.get("file_path", "")
    return ".tmp" in fpath or "cost-tier" in fpath


def main() -> None:
    # Skip in CI
    if os.environ.get("CI", "").lower() in ("true", "1"):
        sys.exit(0)

    # Skip if explicitly overridden
    if "check_cost_tier" in os.environ.get("HOOK_SKIP", ""):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")

    if tool in EXEMPT_TOOLS or tool not in GATE_TOOLS:
        sys.exit(0)

    tool_input = data.get("tool_input", {})

    # Allow writes to .tmp/ (that's where the declaration goes)
    if is_tmp_write(tool, tool_input):
        sys.exit(0)

    today = datetime.now().strftime("%Y-%m-%d")
    decl = read_declaration(today)

    if decl:
        # Declaration exists — optionally surface tier in stderr for visibility
        tier = decl.split("|")[0].strip().upper()
        if tier not in ("L1", "L2", "L3", "L4"):
            tier = "?"
        sys.stderr.write(f"💰 Cost tier: {tier}  ({decl})\n")
        sys.exit(0)

    # --- Block ---
    TMP_DIR.mkdir(exist_ok=True)
    block_msg = f"""⚠️  COST GATE: ยังไม่ได้ประกาศ tier งานนี้ ({today})

ก่อน Edit / Write / Agent ทุกครั้ง ต้อง classify task ตาม Cost-First Pyramid:

  L1  ฟรี / local  — grep, FTS5, read-only, knowledge-graph
  L2  ถูกมาก       — สรุปสั้น, table, reasoning เบา  (→ free/cheap model)
  L3  ถูก          — scan ไฟล์เยอะ, lint, gather intel  (→ platform-low-scout)
  L4  primary      — เขียนโค้ด, reasoning ซับซ้อน, wiki synthesis

สร้าง declaration ด้วย Bash หรือ PowerShell (แล้ว retry):
  Bash:       echo "L4|implementation|เหตุผล" > .tmp/cost-tier-{today}.txt
  PowerShell: [IO.File]::WriteAllText('.tmp\\cost-tier-{today}.txt','L4|implementation|เหตุผล')

Declaration มีผลตลอดวัน — ประกาศครั้งเดียวต่อ session ก็พอ
ถ้าเปลี่ยน task ให้สร้างไฟล์ใหม่ทับ

ดู: docs/protocols/cost-gate.md
"""
    sys.stderr.write(block_msg)
    sys.exit(2)


if __name__ == "__main__":
    main()
