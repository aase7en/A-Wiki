#!/usr/bin/env python3
"""
import-keys.py — Load API keys from Google Drive .secrets → settings.local.json env block

Reads:  <GDRIVE>/A-Wiki-Data/.secrets   (KEY=VALUE format)
Writes: .claude/settings.local.json     (merges into "env" block)

Run: python scripts/sync-secrets.py
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

GDRIVE_PATHS = [
    Path("L:/My Drive/A-Wiki-Data/.secrets"),                                    # Windows
    Path.home() / "Library/CloudStorage" / "GoogleDrive-aase7en@sunday-estate.com" / "My Drive" / "A-Wiki-Data" / ".secrets",  # Mac (work account)
    Path.home() / "Library/CloudStorage" / "GoogleDrive-a.richbusinessman@gmail.com" / "My Drive" / "A-Wiki-Data" / ".secrets",  # Mac (personal account)
]

SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.local.json"

# Secrets that MUST NEVER be cached in settings.local.json — always fetched
# on-demand via scripts/lib/drive_secrets.py::fetch_secret(). High-sensitivity
# values (master passwords, unlock tokens) live ONLY in Drive .secrets.
# See: cloud-link-system memory, secrets-policy memory
NEVER_CACHE = {"WIKI_UNLOCK"}


def find_secrets_file():
    for p in GDRIVE_PATHS:
        if p.exists():
            return p
    return None


def parse_secrets(path: Path) -> dict:
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


def save_settings(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    secrets_path = find_secrets_file()
    if not secrets_path:
        print("ERROR: .secrets file not found in any Google Drive location")
        print("Searched:")
        for p in GDRIVE_PATHS:
            print(f"  {p}")
        sys.exit(1)

    secrets = parse_secrets(secrets_path)
    if not secrets:
        print(f"ERROR: No KEY=VALUE entries found in {secrets_path}")
        sys.exit(1)

    settings = load_settings(SETTINGS_PATH)
    existing_env = settings.get("env", {})

    merged = {**existing_env, **secrets}
    settings["env"] = merged

    save_settings(SETTINGS_PATH, settings)

    print(f"OK — synced {len(secrets)} keys from {secrets_path}")
    for k in secrets:
        masked = secrets[k][:8] + "..." if len(secrets[k]) > 8 else "***"
        print(f"  {k} = {masked}")
    print(f"Written to: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
