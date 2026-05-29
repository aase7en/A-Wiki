#!/usr/bin/env python3
"""
Passive SessionStart checker for A-Wiki external data links.

Supports POSIX symlinks, Windows Junction/ReparsePoint directories, and
`.drive-path` fallback files. This hook is warn-only and never blocks startup.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DRIVE_LINK = REPO_ROOT / "drive"
RAW_LINK = REPO_ROOT / "raw"
ENV_LINK = REPO_ROOT / ".env"
DRIVE_PATH_FILE = REPO_ROOT / ".drive-path"

SETUP_HINT = "-> Run: bash scripts/setup-cloud-link.sh"
EXPECTED_DRIVE_FOLDERS = [
    "raw",
    "waste-reports",
    "personal-tools",
    "ocr-feedback",
    "individual-tasks",
]


def emit(msg: str) -> None:
    """Match other SessionStart hooks' output style."""
    sys.stderr.write(f"SessionStart:startup hook success: {msg}\n")


def is_reparse_point(path: Path) -> bool:
    """Return True for Windows junctions/symlinks without target access."""
    try:
        attrs = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def is_linked_dir(path: Path) -> bool:
    return path.is_symlink() or is_reparse_point(path)


def link_label(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if is_reparse_point(path):
        return "junction"
    return "link"


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def path_is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except OSError:
        return False


def resolve_link_target(path: Path) -> Path:
    """Resolve symlinks and Windows junctions with a safe fallback."""
    try:
        return Path(os.path.realpath(str(path)))
    except OSError:
        return path


def count_files(path: Path) -> int | None:
    try:
        return sum(1 for item in path.rglob("*") if item.is_file())
    except OSError:
        return None


def check_drive() -> tuple[bool, str]:
    """Return (ok, message) for the external data root."""
    if is_linked_dir(DRIVE_LINK):
        target = resolve_link_target(DRIVE_LINK)
        if path_is_dir(target):
            missing = [name for name in EXPECTED_DRIVE_FOLDERS if not path_exists(target / name)]
            suffix = f" (missing optional folders: {', '.join(missing)})" if missing else ""
            return True, f"drive/ -> {target} ({link_label(DRIVE_LINK)}, active){suffix}"
        return False, f"drive/ {link_label(DRIVE_LINK)} target missing: {target} (cloud drive not mounted?)"

    if path_is_dir(DRIVE_LINK):
        return False, "drive/ is a real directory, not a link"

    if path_exists(DRIVE_PATH_FILE):
        try:
            target = Path(DRIVE_PATH_FILE.read_text(encoding="utf-8").strip())
        except OSError as exc:
            return False, f".drive-path read failed: {exc}"
        if path_is_dir(target):
            return True, f".drive-path -> {target} (config fallback)"
        return False, f".drive-path -> {target} (target missing)"

    return False, "drive/ not configured"


def check_raw() -> tuple[bool, str]:
    """Return (ok, message) for immutable source data."""
    if is_linked_dir(RAW_LINK):
        target = resolve_link_target(RAW_LINK)
        if not path_is_dir(target):
            return False, f"raw/ {link_label(RAW_LINK)} target missing: {target}"

        try:
            drive_target = resolve_link_target(DRIVE_LINK) if is_linked_dir(DRIVE_LINK) else None
            if drive_target and str(target).startswith(str(drive_target)):
                file_count = count_files(target)
                count_msg = f", {file_count} file(s)" if file_count is not None else ""
                return True, f"raw/ -> {target} ({link_label(RAW_LINK)}, inside drive/{count_msg})"
        except OSError:
            pass

        return True, f"raw/ -> {target} ({link_label(RAW_LINK)})"

    if path_is_dir(RAW_LINK):
        file_count = count_files(RAW_LINK)
        file_count = 0 if file_count is None else file_count
        if file_count == 0:
            return False, "raw/ is an empty real directory (run setup to link drive/raw)"
        return False, f"raw/ is a real directory with {file_count} file(s); expected link to drive/raw"

    return False, "raw/ not configured"


def check_env() -> tuple[bool, str]:
    """Best-effort check; .env is optional because env vars may be injected."""
    if ENV_LINK.is_symlink() or is_reparse_point(ENV_LINK):
        target = resolve_link_target(ENV_LINK)
        if path_exists(target):
            return True, ".env linked"
        return False, f".env link target missing: {target}"

    try:
        is_file = ENV_LINK.is_file()
    except OSError:
        is_file = False
    if is_file:
        return True, ".env present (real file)"

    return True, ".env not present (using env vars only)"


def main() -> int:
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass

    drive_ok, drive_msg = check_drive()
    raw_ok, raw_msg = check_raw()
    env_ok, env_msg = check_env()

    if drive_ok and raw_ok and env_ok:
        emit("cloud links OK")
    else:
        if not drive_ok:
            emit(drive_msg)
        if not raw_ok:
            emit(raw_msg)
        if not env_ok:
            emit(env_msg)
        emit(SETUP_HINT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
