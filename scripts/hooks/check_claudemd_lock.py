#!/usr/bin/env python3
"""
Hook: CLAUDE.md Lock Protection (Drive-First, On-Demand)
=========================================================
Blocks edits/writes to CLAUDE.md unless authorization is verified.

Authorization sources (checked in order):
  1. Drive .secrets WIKI_UNLOCK — fetched on-demand via drive_secrets.fetch_secret()
     - Compared against WIKI_UNLOCK env var (if set) OR AUTH_BY_DRIVE_MOUNT=1
  2. .claude/lock.txt — offline fallback (compared against WIKI_UNLOCK env var)

Strategic principle: secrets live in Drive, fetched per-use, never permanently
cached in repo files or settings.local.json.

Source: A-Wiki Phase 3 — Secrets-on-Demand System (refactored from InW-Wiki port)
"""
import sys
import json
import os

# Bootstrap path so we can import drive_secrets from scripts/lib/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_SCRIPTS_LIB = os.path.join(_REPO_ROOT, "scripts", "lib")
if _SCRIPTS_LIB not in sys.path:
    sys.path.insert(0, _SCRIPTS_LIB)

try:
    from drive_secrets import fetch_secret
    _HAS_DRIVE_SECRETS = True
except ImportError:
    _HAS_DRIVE_SECRETS = False


def _emit(msg: str) -> None:
    sys.stderr.write(msg if msg.endswith("\n") else msg + "\n")


def _get_expected_password(repo_root: str) -> tuple[str | None, str]:
    """Return (expected_value, source_label) or (None, label) if both fail."""
    # Source 1: Drive .secrets (preferred — Drive-first principle)
    if _HAS_DRIVE_SECRETS:
        drive_val = fetch_secret("WIKI_UNLOCK")
        if drive_val:
            return drive_val, "drive .secrets"

    # Source 2: local .claude/lock.txt (offline fallback)
    lock_file = os.path.join(repo_root, ".claude", "lock.txt")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                val = f.read().strip()
            if val:
                return val, ".claude/lock.txt (offline fallback)"
        except OSError:
            pass

    return None, "no source available"


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    repo_root = _REPO_ROOT
    root_claudemd = os.path.join(repo_root, "CLAUDE.md")

    # Normalize paths
    if os.path.isabs(file_path):
        abs_file_path = os.path.abspath(file_path)
    else:
        abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

    if abs_file_path != root_claudemd and file_path != "CLAUDE.md":
        sys.exit(0)

    # Resolve expected password
    expected, source = _get_expected_password(repo_root)
    if expected is None:
        _emit("🔒 CLAUDE.md is protected — no authorization source available.\n"
              "Either:\n"
              "  1. Mount your cloud drive (so Drive .secrets is reachable), OR\n"
              "  2. Create .claude/lock.txt locally as offline fallback\n"
              "Setup: bash scripts/setup-cloud-link.sh")
        sys.exit(2)

    # Mode A: AUTH_BY_DRIVE_MOUNT — trust Drive presence as authorization
    # (useful for trusted local machines; opt-in via env)
    if os.environ.get("AUTH_BY_DRIVE_MOUNT") == "1" and source == "drive .secrets":
        sys.exit(0)

    # Mode B: explicit WIKI_UNLOCK env var must match expected
    wiki_unlock = os.environ.get("WIKI_UNLOCK", "")
    if not wiki_unlock:
        _emit("🔒 CLAUDE.md is protected.\n\n"
              f"Expected password source: {source}\n\n"
              "Unlock options:\n"
              "  A) export WIKI_UNLOCK=\"$(python3 scripts/lib/drive_secrets.py WIKI_UNLOCK)\"\n"
              "  B) export AUTH_BY_DRIVE_MOUNT=1   (trust Drive mount as auth)\n"
              "  C) export WIKI_UNLOCK=\"$(cat .claude/lock.txt)\"   (offline fallback)\n\n"
              "(env vars are ephemeral — close terminal = lost — secure)")
        sys.exit(2)

    if wiki_unlock.strip() == expected.strip():
        sys.exit(0)

    _emit(f"🔒 WIKI_UNLOCK does not match expected value from {source} — "
          "cannot edit CLAUDE.md\n"
          "If you rotated the password, re-fetch: "
          "export WIKI_UNLOCK=\"$(python3 scripts/lib/drive_secrets.py WIKI_UNLOCK)\"")
    sys.exit(2)


if __name__ == "__main__":
    main()
