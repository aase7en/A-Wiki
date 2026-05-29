#!/usr/bin/env python3
"""
Hook: Delegation Gate
----------------------
Blocks `git push` if it appears the session did NOT go through
the SESSION END PROTOCOL (log.md update, session-memory.md update).

This prevents accidental pushes where the user forgot to log what
was done, which breaks cross-session memory and wiki accountability.

Logic:
  - Only activates on Bash commands containing `git push`
  - Checks if `log.md` or `wiki/context/session-memory.md` were
    recently modified (within last 5 minutes via git diff --cached)
  - If those files are NOT staged AND no commit message contains
    "session(" pattern → block with instructions to run session_end first

Exit 0 = pass (session protocol followed or not a push)
Exit 2 = block (push without session end)
"""
import sys
import json
import os
import re
import subprocess
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HOOKS_DIR, "..", ".."))

SESSION_FILES = [
    "log.md",
    "wiki/context/session-memory.md",
    "session-memory.md",
]

# If a commit message contains this pattern, session is considered logged
SESSION_COMMIT_PATTERN = re.compile(r"session\(", re.IGNORECASE)


def is_push_command(tokens: list) -> bool:
    """Check if the bash tokens represent a git push."""
    separators = {";", "&&", "||", "|", "&"}
    current = []
    for t in tokens + [";"]:
        if t in separators:
            if current and current[0] == "git":
                i = 1
                while i < len(current) and current[i].startswith("-"):
                    i += 1
                if i < len(current) and current[i] == "push":
                    return True
            current = []
        else:
            current.append(t)
    return False


def command_has_session_commit(tokens: list) -> bool:
    """Return True when the same Bash command includes a session commit."""
    separators = {";", "&&", "||", "|", "&"}
    current = []
    for t in tokens + [";"]:
        if t in separators:
            if current and current[0] == "git":
                i = 1
                while i < len(current) and current[i].startswith("-"):
                    i += 1
                if i < len(current) and current[i] == "commit":
                    message_parts: list[str] = []
                    j = i + 1
                    while j < len(current):
                        if current[j] in {"-m", "--message"} and j + 1 < len(current):
                            message_parts.append(current[j + 1])
                            j += 2
                            continue
                        if current[j].startswith("--message="):
                            message_parts.append(current[j].split("=", 1)[1])
                        j += 1
                    if any(SESSION_COMMIT_PATTERN.search(part) for part in message_parts):
                        return True
            current = []
        else:
            current.append(t)
    return False


def get_staged_files() -> set:
    """Return set of staged file paths."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=10,
        )
        if result.returncode == 0:
            return set(f.strip() for f in result.stdout.splitlines() if f.strip())
    except Exception:
        pass
    return set()


def get_most_recent_commit_message() -> str:
    """Return most recent commit message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = input_data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    # Parse tokens
    import shlex
    try:
        tokens = shlex.split(cmd, comments=False, posix=os.name != "nt")
    except ValueError:
        sys.exit(0)

    if not is_push_command(tokens):
        sys.exit(0)

    # It's a push — check if session protocol was followed
    staged = get_staged_files()
    session_files_staged = any(f in staged for f in SESSION_FILES)
    last_commit_msg = get_most_recent_commit_message()
    has_session_commit = bool(SESSION_COMMIT_PATTERN.search(last_commit_msg))
    current_command_has_session_commit = command_has_session_commit(tokens)

    # A compound command that commits and pushes in one shot must carry a
    # session(...) commit message. Do not infer safety from dirty working-tree
    # session files because the commit may omit them.
    if "commit" in tokens and not current_command_has_session_commit and not session_files_staged:
        block_msg = (
            "🛑 BLOCKED: git commit + push without session(...) commit message\n\n"
            "ใช้ commit message รูปแบบ `session(YYYY-MM-DD): ...` หรือ stage "
            "log/session-memory ก่อน push\n"
        )
        sys.stderr.write(block_msg)
        sys.exit(2)

    # Allow if session files are staged OR last commit was a session commit
    if session_files_staged or has_session_commit or current_command_has_session_commit:
        sys.exit(0)

    # Also check if log.md or session-memory.md was modified recently via status
    try:
        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=5,
        )
        status_lines = status_result.stdout.splitlines() if status_result.returncode == 0 else []
    except Exception:
        status_lines = []

    # Check if any session files show as modified (M) or added (A) in working tree
    session_modified = False
    for line in status_lines:
        line = line.strip()
        if len(line) < 3:
            continue
        # Status format: XY filename
        status_code = line[:2].strip()
        fname = line[2:].strip()
        if fname in SESSION_FILES and status_code in ("M", "A", "??"):
            session_modified = True
            break

    if session_modified:
        sys.exit(0)

    # Block: no session protocol detected
    block_msg = (
        f"🛑 BLOCKED: git push without session end protocol\n\n"
        f"ตรวจพบ `git push` แต่ไฟล์ session/log ยังไม่ถูกอัปเดต:\n\n"
        f"  Staged files: {', '.join(staged) if staged else '(none)'}\n"
        f"  Last commit: {last_commit_msg or '(none)'}\n\n"
        f"ก่อน push ต้องทำ SESSION END PROTOCOL ก่อน:\n"
        f"  1. สรุปสิ่งที่ทำใน session นี้\n"
        f"  2. บันทึกลง log.md (format: ## [YYYY-MM-DD] session | <หัวข้อ>)\n"
        f"  3. อัปเดต wiki/context/session-memory.md\n"
        f"  4. รัน: git add . && git commit -m \"session(DATE): ...\" && git push\n\n"
        f"ดู CLAUDE.md §SESSION END PROTOCOL สำหรับรายละเอียด\n"
    )
    sys.stderr.write(block_msg)
    sys.exit(2)


if __name__ == "__main__":
    main()
