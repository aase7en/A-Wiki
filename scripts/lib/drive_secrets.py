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


def _glob_cloudstorage_drive() -> list[Path]:
    """Auto-detect Google Drive / iCloud / OneDrive / Dropbox roots holding
    `A-Wiki-Data/.secrets`. No hardcoded account names — works for any user.

    Searched cloud provider patterns (per platform):
      macOS:   ~/Library/CloudStorage/{GoogleDrive,OneDrive,Dropbox}-*/My Drive/A-Wiki-Data
               ~/Library/Mobile Documents/com~apple~CloudDocs/A-Wiki-Data  (iCloud)
      Linux:   ~/GoogleDrive/A-Wiki-Data, ~/OneDrive/A-Wiki-Data, ~/Dropbox/A-Wiki-Data
      Windows: %USERPROFILE%/{Google Drive,OneDrive,Dropbox}/A-Wiki-Data
    """
    home = Path.home()
    hits: list[Path] = []

    # macOS CloudStorage (any GoogleDrive-* / OneDrive-* / Dropbox-* account)
    cloudstorage = home / "Library" / "CloudStorage"
    if cloudstorage.is_dir():
        for provider in ("GoogleDrive-*", "OneDrive-*", "Dropbox-*"):
            for acct in cloudstorage.glob(provider):
                # Google Drive root nests under "My Drive"; others typically at acct root
                for sub in (acct / "My Drive" / "A-Wiki-Data", acct / "A-Wiki-Data"):
                    if sub.is_dir():
                        hits.append(sub / ".secrets")

    # macOS iCloud
    icloud = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "A-Wiki-Data"
    if icloud.is_dir():
        hits.append(icloud / ".secrets")

    # Linux / WSL conventional paths
    for rel in ("GoogleDrive", "OneDrive", "Dropbox"):
        cand = home / rel / "A-Wiki-Data" / ".secrets"
        if cand.parent.is_dir():
            hits.append(cand)

    # Windows USERPROFILE conventional paths (Git Bash / WSL using $USERPROFILE)
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        wp = Path(userprofile)
        for rel in ("Google Drive", "OneDrive", "Dropbox"):
            cand = wp / rel / "A-Wiki-Data" / ".secrets"
            if cand.parent.is_dir():
                hits.append(cand)

    return hits


def candidate_secret_paths() -> list[Path]:
    """Return likely `.secrets` file locations, cheapest/local first.

    Resolution order (cheapest → most expensive scan):
      1. `A_WIKI_DRIVE_PATH` env var — explicit user override (highest priority)
      2. `<repo>/drive/.secrets` via `get_drive_root()` — the configured symlink
      3. `<repo>/drive/.secrets` direct (in case symlink helper unavailable)
      4. Glob auto-detect across known cloud providers (no hardcoded accounts)
      5. Windows mapped-drive fallback (`L:/My Drive/A-Wiki-Data/.secrets`)
    """
    paths: list[Path] = []

    # 1. Explicit override — for users with non-standard layouts
    override = os.environ.get("A_WIKI_DRIVE_PATH")
    if override:
        paths.append(Path(override) / ".secrets")

    # 2. Configured drive/ symlink — fast path for properly-set-up machines
    if get_drive_root is not None:
        try:
            paths.append(get_drive_root() / ".secrets")
        except Exception:
            pass

    # 3. Direct drive/ probe (helper-less fallback)
    paths.append(REPO_ROOT / "drive" / ".secrets")

    # 4. Auto-detect across cloud providers (no hardcoded user accounts)
    paths.extend(_glob_cloudstorage_drive())

    # 5. Windows mapped-drive convention (kept for back-compat; not user-specific)
    paths.append(Path("L:/My Drive/A-Wiki-Data/.secrets"))

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
