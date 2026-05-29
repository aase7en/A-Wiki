#!/usr/bin/env python3
"""
External data health report for A-Wiki.

Checks the Google Drive-backed `A-Wiki-Data` layer without printing any secret
values. Intended for all platforms and agents as a quick confidence check.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from drive_path import get_drive_root

EXPECTED_FOLDERS = [
    "raw",
    "waste-reports",
    "personal-tools",
    "ocr-feedback",
    "individual-tasks",
]


def count_files(path: Path) -> int | None:
    if not path.is_dir():
        return None
    try:
        return sum(1 for item in path.rglob("*") if item.is_file())
    except OSError:
        return None


def status_line(ok: bool, label: str, detail: str = "") -> str:
    prefix = "OK" if ok else "WARN"
    suffix = f" - {detail}" if detail else ""
    return f"[{prefix}] {label}{suffix}"


def main() -> int:
    drive_root = get_drive_root()
    print("A-Wiki External Data Health")
    print("===========================")
    print(f"Drive root: {drive_root}")

    overall_ok = True

    for folder in EXPECTED_FOLDERS:
        path = drive_root / folder
        ok = path.is_dir()
        overall_ok = overall_ok and ok
        print(status_line(ok, folder, str(path)))

    raw_dir = drive_root / "raw"
    raw_count = count_files(raw_dir) if raw_dir.is_dir() else None
    if raw_count is None:
        overall_ok = False
        print(status_line(False, "raw file count", "unavailable"))
    else:
        print(status_line(raw_count > 0, "raw file count", str(raw_count)))
        overall_ok = overall_ok and raw_count > 0

    secrets = drive_root / ".secrets"
    secrets_ok = secrets.is_file()
    overall_ok = overall_ok and secrets_ok
    print(status_line(secrets_ok, ".secrets", "present; values not printed" if secrets_ok else "missing"))

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
