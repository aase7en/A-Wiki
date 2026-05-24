#!/usr/bin/env python3
"""
Hook: CLAUDE.md Lock Protection
--------------------------------
Blocks edits/writes to CLAUDE.md unless WIKI_UNLOCK environment variable
matches the password stored in .claude/lock.txt.

Source: InW-Wiki (ported with A-Wiki path adjustments)
"""
import sys
import json
import os

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    # Locate repo root (scripts/hooks/ -> repo root)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    root_claudemd = os.path.join(repo_root, "CLAUDE.md")

    # Normalize paths
    if os.path.isabs(file_path):
        abs_file_path = os.path.abspath(file_path)
    else:
        abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

    if abs_file_path != root_claudemd and file_path != "CLAUDE.md":
        sys.exit(0)

    # Check lock file
    lock_file = os.path.join(repo_root, ".claude", "lock.txt")
    if not os.path.exists(lock_file):
        sys.stderr.write("🔒 CLAUDE.md is protected.\n\n"
                         "Setup needed on this device (one-time):\n"
                         "  1. cp .claude/lock.example .claude/lock.txt\n"
                         "  2. แก้ .claude/lock.txt → ใส่ password จริง\n"
                         "  3. chmod 600 .claude/lock.txt\n\n"
                         "แล้ว unlock ด้วย:\n"
                         "  export WIKI_UNLOCK=\"$(cat .claude/lock.txt)\"\n")
        sys.exit(2)

    # Check environment variable
    wiki_unlock = os.environ.get("WIKI_UNLOCK", "")
    if not wiki_unlock:
        sys.stderr.write("🔒 CLAUDE.md is protected.\n\n"
                         "ต้อง unlock ก่อนแก้ — รันคำสั่งนี้แล้วลองอีกครั้ง:\n"
                         "  export WIKI_UNLOCK=\"$(cat .claude/lock.txt)\"\n\n"
                         "(env var หายอัตโนมัติเมื่อปิด terminal — ปลอดภัย)\n")
        sys.exit(2)

    with open(lock_file, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    if wiki_unlock.strip() != expected:
        sys.stderr.write("🔒 WIKI_UNLOCK ไม่ตรงกับ password ใน .claude/lock.txt — แก้ CLAUDE.md ไม่ได้\n")
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()