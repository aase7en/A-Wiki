#!/usr/bin/env python3
"""
Hook: Raw Directory Immutability
--------------------------------
Blocks edits/writes/deletes to any file under raw/ directory.
raw/ stores original source documents — never modify in place.

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

    if not file_path:
        sys.exit(0)

    # Locate repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    # Use realpath (not abspath) to resolve junctions/symlinks on Windows and Mac.
    # This ensures drive/raw/ (alias) is treated identically to raw/ (canonical).
    raw_dir = os.path.realpath(os.path.join(repo_root, "raw"))

    # Normalize path — realpath resolves any junction/symlink in the path
    if os.path.isabs(file_path):
        abs_file_path = os.path.realpath(file_path)
    else:
        abs_file_path = os.path.realpath(os.path.join(repo_root, file_path))

    # Check if file path is under raw/ (works for both raw/ and drive/raw/ aliases)
    try:
        # If raw_dir is a common path prefix, it means abs_file_path is inside it
        if os.path.commonpath([raw_dir, abs_file_path]) == raw_dir:
            sys.stderr.write(f"🔒 raw/ is immutable (CLAUDE.md rule #1)\n\n"
                             f"ไฟล์: {file_path}\n\n"
                             f"raw/ เก็บ source document ต้นฉบับ — ห้ามแก้ไขหรือลบ\n"
                             f"ถ้าจำเป็นต้อง sanitize → copy ออกมา edit นอก raw/\n"
                             f"ถ้าต้อง re-ingest → ingest source ใหม่แทนที่จะแก้ของเก่า\n")
            sys.exit(2)
    except ValueError:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()