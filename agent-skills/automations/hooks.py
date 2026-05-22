#!/usr/bin/env python3
"""
Automation Hooks — Routine Pattern Execution for A-Wiki Agent Swarm.

These hooks enforce the Iron Laws and automate routine workflows.
Execution order: PRE_HOOKS → MAIN → POST_HOOKS
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_LOG = REPO_ROOT / ".local" / "hooks-log.json"
SESSION_MEMO = REPO_ROOT / ".local" / "session-memory.md"

# ──────────────────────────────────────────────
# PRE-EXECUTION HOOKS (Iron Law Enforcement)
# ──────────────────────────────────────────────

def pre_hook_validate_git_origin():
    """IRON LAW: Validate git remote origin before any execution."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        if "origin" not in result.stdout:
            print("[HOOK] ⚠️  No 'origin' remote configured. Stopping.")
            sys.exit(1)
        print(f"[HOOK] ✅ Git origin validated\n{result.stdout.strip()}")
    except Exception as e:
        print(f"[HOOK] ❌ Git validation failed: {e}")
        sys.exit(1)


def pre_hook_check_main_branch():
    """IRON LAW: Ensure we are on main branch — no branching allowed."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        branch = result.stdout.strip()
        if branch != "main":
            print(f"[HOOK] ❌ On branch '{branch}'. Must be on 'main'. Stopping.")
            sys.exit(1)
        print(f"[HOOK] ✅ On main branch")
    except Exception as e:
        print(f"[HOOK] ❌ Branch check failed: {e}")
        sys.exit(1)


# ──────────────────────────────────────────────
# POST-EXECUTION HOOKS (Session Continuity)
# ──────────────────────────────────────────────

def post_hook_write_session_summary(title: str, status: str, context: str, next_action: str):
    """Write a session summary to session-memory.md for cross-device carry-over."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"""
## [{timestamp}] — {title}
**Status:** {status}
**Context:** {context}
**Next:** {next_action}
---
"""
    SESSION_MEMO.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_MEMO, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[HOOK] ✅ Session summary written to {SESSION_MEMO}")


def post_hook_verify_no_debug_prints(file_patterns=None):
    """POST-HOOK: Scan changed files for leftover debug prints."""
    if file_patterns is None:
        file_patterns = ["*.py", "*.js", "*.ts", "*.sh", "*.md"]

    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

    flagged = []
    for f in staged_files:
        ext = os.path.splitext(f)[1]
        if not any(f.endswith(p.replace("*", "")) for p in file_patterns):
            continue
        filepath = REPO_ROOT / f
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        if "print(" in content and "def " not in content.split("print(")[0][-200:]:
            # Flag only suspicious debug prints (not legitimate logging)
            for lineno, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("print(") and (
                    "debug" in stripped.lower() or
                    "dbg" in stripped.lower() or
                    "temp" in stripped.lower() or
                    stripped.startswith("print(") and len(stripped) < 80
                ):
                    flagged.append(f"  {f}:{lineno}  {stripped[:60]}")

    if flagged:
        print(f"[HOOK] ⚠️  Suspicious debug prints found:\n" + "\n".join(flagged))
        print("[HOOK] Review and remove before committing.")
    else:
        print("[HOOK] ✅ No suspicious debug prints detected.")


def post_hook_generate_commit_summary():
    """Generate a smart commit summary from staged changes."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if result.stdout.strip():
        print(f"[HOOK] 📊 Staged changes summary:\n{result.stdout}")


# ──────────────────────────────────────────────
# ROUTINE EXECUTORS
# ──────────────────────────────────────────────

def run_routine(routine_name: str):
    """Execute a named routine pattern."""
    routines = {
        "daily-update": lambda: print("[ROUTINE] Daily wiki update — scanning sources..."),
        "session-start": lambda: (
            pre_hook_validate_git_origin(),
            pre_hook_check_main_branch(),
            print("[ROUTINE] ✅ Session start hooks passed.")
        ),
        "session-end": lambda: (
            post_hook_verify_no_debug_prints(),
            post_hook_generate_commit_summary(),
            print("[ROUTINE] ✅ Session end hooks passed.")
        ),
    }
    routine = routines.get(routine_name)
    if routine:
        routine()
    else:
        print(f"[HOOK] ❌ Unknown routine: {routine_name}")
        sys.exit(1)


# ──────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hooks.py <command> [args...]")
        print("Commands: pre-flight, session-start, session-end, daily-update, summary")
        sys.exit(1)

    command = sys.argv[1]

    if command == "pre-flight":
        pre_hook_validate_git_origin()
        pre_hook_check_main_branch()
        print("[HOOK] ✅ All pre-flight checks passed.")
    elif command == "session-start":
        run_routine("session-start")
    elif command == "session-end":
        run_routine("session-end")
    elif command == "summary":
        if len(sys.argv) >= 5:
            post_hook_write_session_summary(
                title=sys.argv[2],
                status=sys.argv[3],
                context=sys.argv[4],
                next_action=sys.argv[5] if len(sys.argv) > 5 else ""
            )
        else:
            print("Usage: hooks.py summary <title> <status> <context> [next_action]")
    elif command == "daily-update":
        run_routine("daily-update")
    else:
        print(f"[HOOK] ❌ Unknown command: {command}")
        sys.exit(1)
