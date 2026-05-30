#!/usr/bin/env python3
"""Load cacheable API keys from Drive `.secrets` into settings.local.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Reuse drive_secrets.py auto-detection so there's exactly one place that knows
# how to find .secrets across Google Drive / OneDrive / Dropbox / iCloud on
# macOS / Linux / WSL / Windows. No hardcoded account names.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
from drive_secrets import candidate_secret_paths  # noqa: E402

SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.local.json"

# Secrets that MUST NEVER be cached in settings.local.json — always fetched
# on-demand via scripts/lib/drive_secrets.py::fetch_secret(). High-sensitivity
# values (master passwords, unlock tokens) live ONLY in Drive .secrets.
# See: cloud-link-system memory, secrets-policy memory
NEVER_CACHE = {"WIKI_UNLOCK"}


def find_secrets_file():
    for p in candidate_secret_paths():
        if p.exists():
            return p
    return None


def parse_secrets(path: Path) -> dict[str, str]:
    keys = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # strip shell "export " prefix
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")  # strip optional quotes
        if k and k not in NEVER_CACHE:
            keys[k] = v
    return keys


def load_settings(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def redact_path(path: Path) -> str:
    """Return a non-personal path label for status output."""
    try:
        rel = path.relative_to(REPO_ROOT)
        return str(rel)
    except ValueError:
        return "Drive .secrets"


def sync_settings(secrets_path: Path, *, dry_run: bool = False) -> tuple[int, list[str]]:
    secrets = parse_secrets(secrets_path)
    if not secrets:
        raise ValueError("No cacheable KEY=VALUE entries found")

    if dry_run:
        return len(secrets), sorted(secrets)

    settings = load_settings(SETTINGS_PATH)
    existing_env = settings.get("env", {})
    settings["env"] = {**existing_env, **secrets}
    save_settings(SETTINGS_PATH, settings)
    return len(secrets), sorted(secrets)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync cacheable A-Wiki API keys from Drive .secrets into local settings."
    )
    parser.add_argument("--check", action="store_true", help="check availability without writing settings")
    parser.add_argument("--list", action="store_true", help="list cacheable key names only")
    parser.add_argument("--dry-run", action="store_true", help="parse and report key count without writing")
    args = parser.parse_args()

    secrets_path = find_secrets_file()
    if not secrets_path:
        print("ERROR: .secrets file not found")
        print("Searched:")
        for p in candidate_secret_paths():
            print(f"  {redact_path(p)}")
        return 1

    try:
        count, names = sync_settings(secrets_path, dry_run=args.check or args.list or args.dry_run)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.list:
        for name in names:
            print(name)
        return 0

    if args.check:
        print(f"OK — {redact_path(secrets_path)} readable: {count} cacheable key name(s)")
        return 0

    if args.dry_run:
        print(f"OK — dry run parsed {count} cacheable key name(s); settings not modified")
        return 0

    print(f"OK — synced {count} cacheable key name(s) into .claude/settings.local.json")
    print("Secret values are intentionally not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
