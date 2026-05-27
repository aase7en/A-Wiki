#!/usr/bin/env python3
"""
Hook: Check Drive Link
======================
Passive SessionStart checker — verifies cloud-drive symlinks are intact.

Checks:
  1. drive/  is a symlink (or .drive-path config) → target exists
  2. raw/    is a symlink resolving into drive/ (or own valid target)
  3. .env    resolves (symlink target exists OR env vars set)

Exit code: always 0 (warn-only, never block session)
Output:    stderr-only, matches SessionStart hook output style

Source: A-Wiki Phase 2 — Auto Cloud-Drive Linking System
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DRIVE_LINK = REPO_ROOT / "drive"
RAW_LINK = REPO_ROOT / "raw"
ENV_LINK = REPO_ROOT / ".env"
DRIVE_PATH_FILE = REPO_ROOT / ".drive-path"

SETUP_HINT = "→ Run: bash scripts/setup-cloud-link.sh"


def emit(msg: str) -> None:
    """Match other SessionStart hooks' output style."""
    sys.stderr.write(f"SessionStart:startup hook success: {msg}\n")


def check_drive() -> tuple[bool, str]:
    """Returns (ok, message)."""
    if DRIVE_LINK.is_symlink():
        target = DRIVE_LINK.resolve()
        if target.exists() and target.is_dir():
            return True, f"drive/ → {target}"
        return False, f"❌ drive/ symlink target missing: {target} (cloud drive not mounted?)"
    if DRIVE_LINK.is_dir():
        return False, "❌ drive/ is a real directory, not a symlink"
    if DRIVE_PATH_FILE.exists():
        try:
            target = Path(DRIVE_PATH_FILE.read_text(encoding="utf-8").strip())
            if target.is_dir():
                return True, f".drive-path → {target} (config fallback)"
            return False, f"❌ .drive-path → {target} (TARGET MISSING)"
        except OSError as e:
            return False, f"❌ .drive-path read failed: {e}"
    return False, "❌ drive/ not configured"


def check_raw() -> tuple[bool, str]:
    if RAW_LINK.is_symlink():
        target = RAW_LINK.resolve()
        if target.exists() and target.is_dir():
            # Bonus: confirm it's actually inside drive/
            try:
                drive_target = DRIVE_LINK.resolve() if DRIVE_LINK.is_symlink() else None
                if drive_target and str(target).startswith(str(drive_target)):
                    return True, f"raw/ → {target} (inside drive/)"
            except OSError:
                pass
            return True, f"raw/ → {target}"
        return False, f"❌ raw/ symlink target missing: {target}"
    if RAW_LINK.is_dir():
        # Real directory — has it any files?
        try:
            file_count = sum(1 for _ in RAW_LINK.rglob("*") if _.is_file())
        except OSError:
            file_count = 0
        if file_count == 0:
            return False, "❌ raw/ is empty real directory (run setup to migrate to drive/raw)"
        return False, f"❌ raw/ is real directory with {file_count} files (use --migrate)"
    return False, "❌ raw/ not configured"


def check_env() -> tuple[bool, str]:
    """Best-effort check — .env may be optional."""
    if ENV_LINK.is_symlink():
        target = ENV_LINK.resolve()
        if target.exists():
            return True, ".env linked"
        return False, f"⚠️  .env symlink target missing: {target}"
    if ENV_LINK.is_file():
        return True, ".env present (real file)"
    return True, ".env not present (using env vars only)"  # not fatal


def main() -> int:
    # Drain stdin if hook system sends JSON (we don't need it, but must not block)
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass

    drive_ok, drive_msg = check_drive()
    raw_ok, raw_msg = check_raw()
    env_ok, env_msg = check_env()

    if drive_ok and raw_ok and env_ok:
        emit("✅ cloud links OK")
    else:
        if not drive_ok:
            emit(drive_msg)
        if not raw_ok:
            emit(raw_msg)
        if not env_ok:
            emit(env_msg)
        emit(SETUP_HINT)

    return 0  # always non-blocking


if __name__ == "__main__":
    sys.exit(main())
