#!/usr/bin/env python3
"""
Hook: Git Rebase Safety (Z3 — PreToolUse, warn-only)
----------------------------------------------------
PreToolUse hook บน `Bash` tool. ตรวจว่า command มี `git pull --rebase` หรือ
`git rebase` ไหม. ถ้าใช่:
  1. auto-backup HEAD (safety net — กัน commit หาย)
  2. นับ unpushed commits → เตือนถ้ามี

ไม่บล็อก — แค่ backup + เตือน (อนุญาตให้ rebase ผ่านแต่มี safety net).

Override: HOOK_SKIP=check_git_rebase_safety

Rationale: 2026-07-16 incident — concurrent session ran `git pull --rebase`
which dropped 14 commits from another session. Manual reflog recovery needed.
This hook auto-backs-up before rebase so recovery is 1 command.
"""
import json
import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent

# Import safety backup functions (same directory)
sys.path.insert(0, str(HOOKS_DIR))
try:
    import git_safety_backup as gsb
    _GSB_OK = True
except Exception:
    _GSB_OK = False


def main() -> int:
    if os.environ.get("HOOK_SKIP") == "check_git_rebase_safety":
        return 0
    if not _GSB_OK:
        return 0  # can't import safety module — don't block

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return 0

    if not gsb.is_rebase_command(command):
        return 0

    warnings = []

    # 1. Auto-backup HEAD before rebase
    try:
        head = gsb.backup_head(REPO_ROOT)
        if head:
            warnings.append(f"[git-safety] ✓ Backed up HEAD ({head[:12]}) → .tmp/git-head-backup.jsonl")
    except Exception:
        pass  # backup failure ไม่ block

    # 2. Count unpushed commits
    try:
        unpushed = gsb.count_unpushed_commits(REPO_ROOT)
        if unpushed > 0:
            warnings.append(
                f"[git-safety] ⚠️ {unpushed} unpushed commit(s) on local — "
                f"rebase may drop them. Backup saved. "
                f"Recover: python scripts/hooks/git_safety_backup.py --recover"
            )
    except Exception:
        pass

    if warnings:
        sys.stderr.write("\n".join(warnings) + "\n")

    return 0  # never block — warn + backup only


if __name__ == "__main__":
    sys.exit(main())
