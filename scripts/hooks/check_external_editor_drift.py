#!/usr/bin/env python3
"""
Hook: External Editor Drift Protection (Iron Law #6)
----------------------------------------------------
Prevents accidental downgrade/overwrite of files whose source of truth lives
in an external editor (e.g. userscripts in Tampermonkey/Violentmonkey).

Trigger: Edit | Write | MultiEdit where file_path matches a watched pattern.

Behavior:
  1. Extract `// @version X.Y.Z` from the existing file in git.
  2. Require env var USERSCRIPT_SYNC_OK=<version> to match.
  3. Block (exit 2) with explicit instructions if mismatch.

Rationale: 2026-05-27 incident — Claude edited waste-form-ocr-fill.user.js
v0.1.0 from git, but the user's Tampermonkey copy was v0.8.0 (7 unreleased
iterations). Dragging the edited file back would have downgraded + erased work.

Bypass (emergency): HOOK_SKIP=check_external_editor_drift

See: wiki/context/session-memory.md · memory/feedback-userscript-git-sync.md
"""
import sys
import json
import os
import re
import fnmatch

# Patterns for files whose source-of-truth lives in an external editor.
# Add new entries here as more such tools join the project.
WATCHED_PATTERNS = [
    "*.user.js",   # Tampermonkey / Violentmonkey / Greasemonkey
]

VERSION_RE = re.compile(r"^//\s*@version\s+(\S+)\s*$", re.MULTILINE)


def matches_watched(path: str) -> bool:
    base = os.path.basename(path)
    return any(fnmatch.fnmatch(base, pat) for pat in WATCHED_PATTERNS)


def extract_version(abs_path: str):
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            header = f.read(4096)  # @version lives in userscript header
    except OSError:
        return None
    m = VERSION_RE.search(header)
    return m.group(1) if m else None


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not matches_watched(file_path):
        sys.exit(0)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    abs_path = (
        os.path.abspath(file_path)
        if os.path.isabs(file_path)
        else os.path.abspath(os.path.join(repo_root, file_path))
    )

    # New file (creating) — nothing to drift from
    if not os.path.isfile(abs_path):
        sys.exit(0)

    git_version = extract_version(abs_path)
    if not git_version:
        sys.stderr.write(
            f"⚠️ external-editor-drift: {os.path.basename(file_path)} ไม่มี @version header — "
            f"ข้ามการตรวจ (เพิ่ม `// @version X.Y.Z` ใน header เพื่อให้ Iron Law #6 ทำงาน)\n"
        )
        sys.exit(0)

    sync_ok = os.environ.get("USERSCRIPT_SYNC_OK", "").strip()
    if sync_ok == git_version:
        sys.exit(0)

    sys.stderr.write(
        f"🔒 External-editor drift guard (Iron Law #6)\n\n"
        f"  ไฟล์: {file_path}\n"
        f"  git มี @version {git_version}\n"
        f"  USERSCRIPT_SYNC_OK = {sync_ok or '(ไม่ได้ตั้ง)'}\n\n"
        f"ไฟล์นี้แก้ใน external editor ได้ (Tampermonkey ฯลฯ) — git อาจ stale\n\n"
        f"ขั้นตอน:\n"
        f"  1. เปิด Tampermonkey/external editor → ดู `// @version` ปัจจุบัน\n"
        f"  2. ถ้าตรงกับ git ({git_version}) → run:\n"
        f"       export USERSCRIPT_SYNC_OK={git_version}\n"
        f"     แล้วลองอีกครั้ง\n"
        f"  3. ถ้าไม่ตรง → paste source ปัจจุบันให้ Claude ก่อน update git baseline\n\n"
        f"Bypass (ฉุกเฉิน): HOOK_SKIP=check_external_editor_drift\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
