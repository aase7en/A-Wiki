#!/usr/bin/env python3
"""
Drive-backed secret reader for A-Wiki.

Secrets live in the external Google Drive `A-Wiki-Data/.secrets` file and are
fetched on demand. This module deliberately avoids printing secret values in
health/list modes.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from drive_path import get_drive_root
except Exception:  # pragma: no cover - defensive fallback for standalone use
    get_drive_root = None


def candidate_secret_paths() -> list[Path]:
    """Return likely `.secrets` file locations, cheapest/local first."""
    paths: list[Path] = []

    if get_drive_root is not None:
        try:
            paths.append(get_drive_root() / ".secrets")
        except Exception:
            pass

    paths.extend(
        [
            REPO_ROOT / "drive" / ".secrets",
            Path("L:/My Drive/A-Wiki-Data/.secrets"),
            Path.home()
            / "Library"
            / "CloudStorage"
            / "GoogleDrive-aase7en@sunday-estate.com"
            / "My Drive"
            / "A-Wiki-Data"
            / ".secrets",
            Path.home()
            / "Library"
            / "CloudStorage"
            / "GoogleDrive-a.richbusinessman@gmail.com"
            / "My Drive"
            / "A-Wiki-Data"
            / ".secrets",
        ]
    )

    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def find_secrets_file() -> Path | None:
    """Find the first readable KEY=VALUE `.secrets` file."""
    for path in candidate_secret_paths():
        try:
            if path.is_file():
                return path
        except OSError:
            continue
    return None


def parse_secrets_file(path: Path) -> dict[str, str]:
    """Parse shell-ish KEY=VALUE lines without evaluating shell syntax."""
    values: dict[str, str] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_secrets() -> dict[str, str]:
    path = find_secrets_file()
    if path is None:
        return {}
    try:
        return parse_secrets_file(path)
    except OSError:
        return {}


def fetch_secret(name: str) -> str | None:
    """Return a secret value by name, or None if unavailable."""
    return load_secrets().get(name)


def list_secret_names() -> list[str]:
    """Return secret names only. Never return values."""
    return sorted(load_secrets())


def health_check() -> tuple[bool, str]:
    path = find_secrets_file()
    if path is None:
        return False, "Drive .secrets file not found"
    names = list_secret_names()
    return True, f"Drive .secrets readable: {len(names)} key name(s)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read A-Wiki secrets from Drive .secrets")
    parser.add_argument("key", nargs="?", help="Secret key name to print")
    parser.add_argument("--list", action="store_true", help="List secret names only")
    parser.add_argument("--check", action="store_true", help="Check availability without printing values")
    args = parser.parse_args()

    if args.check:
        ok, message = health_check()
        print(message)
        return 0 if ok else 1

    if args.list:
        for name in list_secret_names():
            print(name)
        return 0

    if args.key:
        value = fetch_secret(args.key)
        if value is None:
            print(f"ERROR: secret not found: {args.key}", file=sys.stderr)
            return 1
        print(value)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
