#!/usr/bin/env python3
"""
Hook: Machine-Path Guard (USA-1 §5.1 Layer 1)
----------------------------------------------
Blocks Write/Edit/MultiEdit tool calls that would embed machine-specific paths
(L:\\..., C:\\Users\\<user>\\, /Users/<user>/, GoogleDrive-<account>) into
repo-tracked files. These paths must resolve via the drive/ junction,
.drive-path, or A_WIKI_DRIVE_PATH instead (Hybrid Drive Rule §4.3).

Same hook-payload contract as scripts/hooks/check_secret_leak.py:
  - Reads the PreToolUse JSON on stdin (tool_name + tool_input).
  - Inspects file_path + new_string + content for machine-path patterns.
  - Emits a JSON verdict on stdout: {"hookSpecificOutput": {"hookEventName":
    "PreToolUse", "permissionDecision": "deny"|"allow", ...}} or a plain
    stderr+exit-2 fallback.

Patterns are loaded from scripts/hooks/security_patterns.yaml (single source,
shared with check_secret_leak.py and check-privacy.py — USA-1 §5.3).

Override (emergencies only): HOOK_SKIP=check_machine_path
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERNS_FILE = REPO_ROOT / "scripts" / "hooks" / "security_patterns.yaml"


def _load_machine_patterns() -> list[tuple[str, re.Pattern[str], list[str], str]]:
    """Load machine_path_patterns from the YAML (or fall back to a builtin set)."""
    builtin = [
        ("Windows user home", re.compile(r"C:\\Users\\([A-Za-z0-9._-]+)\\"), []),
        ("macOS user home", re.compile(r"/Users/([A-Za-z0-9._-]+)/"), []),
        ("Linux user home", re.compile(r"/home/([A-Za-z0-9._-]+)/"), []),
        ("Google Drive account", re.compile(r"CloudStorage/GoogleDrive-([A-Za-z0-9._-]+)"), []),
    ]
    try:
        import yaml  # type: ignore
    except ImportError:
        return builtin
    if not PATTERNS_FILE.exists():
        return builtin
    try:
        data = yaml.safe_load(PATTERNS_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return builtin
    entries = data.get("machine_path_patterns") or []
    out: list[tuple[str, re.Pattern[str], list[str], str]] = []
    for e in entries:
        try:
            out.append((
                e.get("name", "unnamed"),
                re.compile(e["regex"]),
                [s.lower() for s in e.get("allowlist", [])],
                e.get("note", ""),
            ))
        except (KeyError, re.error):
            continue
    return out or builtin


PATTERNS = _load_machine_patterns()


def _flatten(value) -> str:
    """Turn the hook JSON payload into a flat text blob for scanning."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def _scan(text: str) -> list[str]:
    """Return human-readable findings for any machine-path pattern hit."""
    findings: list[str] = []
    text_lower = text.lower()
    for name, regex, allowlist, note in PATTERNS:
        for m in regex.finditer(text):
            matched = m.group(0)
            # Allowlist: if any allowlist substring appears in a window around
            # the match, treat it as a safe placeholder/example.
            window = text_lower[max(0, m.start() - 40): m.end() + 40]
            if any(a in window for a in allowlist):
                continue
            findings.append(f"{name}: ...{matched}...")
            if note:
                findings.append(f"  note: {note}")
            break  # one hit per pattern is enough
    return findings


def main() -> int:
    if os.environ.get("HOOK_SKIP", "").split() and "check_machine_path" in os.environ["HOOK_SKIP"].split():
        return 0

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Not a hook payload — fail open (don't block non-hook invocations).
        return 0

    tool = payload.get("tool_name") or payload.get("toolName") or ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}

    # Only inspect mutating tools that write file content.
    mutating = {"Write", "Edit", "MultiEdit", "write_to_file", "replace_in_file"}
    if tool not in mutating:
        return 0

    # Gather every string field that could carry a path.
    candidates = [
        _flatten(tool_input.get("file_path") or tool_input.get("filePath")),
        _flatten(tool_input.get("content")),
        _flatten(tool_input.get("new_string") or tool_input.get("newString")),
        _flatten(tool_input.get("old_string") or tool_input.get("oldString")),
    ]
    # MultiEdit: also scan each edit's strings.
    for edit in tool_input.get("edits") or []:
        candidates.append(_flatten(edit.get("new_string") if isinstance(edit, dict) else ""))
        candidates.append(_flatten(edit.get("old_string") if isinstance(edit, dict) else ""))

    blob = "\n".join(c for c in candidates if c)
    findings = _scan(blob)

    if not findings:
        return 0

    msg = (
        "BLOCKED by check_machine_path (USA-1 §5.1): machine-specific path detected.\n"
        "Machine paths (C:\\Users\\..., L:\\..., /Users/<user>/, GoogleDrive-<acct>) "
        "must not be hardcoded into repo files.\n"
        "Resolve via drive/ junction, .drive-path, or A_WIKI_DRIVE_PATH instead.\n"
        "Findings:\n  - " + "\n  - ".join(findings) + "\n"
        "Override (emergencies only): HOOK_SKIP=check_machine_path"
    )

    # Prefer the structured hook verdict when the payload looks like a hook event.
    if payload.get("session_id") or payload.get("hook_event_name") or payload.get("tool_name"):
        verdict = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": msg,
            }
        }
        print(json.dumps(verdict, ensure_ascii=False))
        # Emit verdict JSON for agents that read stdout (Claude), AND exit 2 so
        # hooks_runner.py (which keys on exit code) registers the block.
        return 2

    # Fallback: stderr + exit 2 (hook-blocking convention).
    print(msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
