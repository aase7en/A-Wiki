#!/usr/bin/env python3
"""vendor_watch.py — silent upstream-commit watcher for A-Wiki's vendored skills.

A-Wiki vendors several upstream skill repos (9arm-skills, ECC, mattpocock/skills,
anthropics/skills, microsoft/SkillOpt) via `scripts/refresh-*.sh`. Nothing today
tells the user those upstreams moved — the user must remember to re-run the
refresh scripts on a schedule. This module gives SessionStart a cheap, offline
-safe way to nudge: "upstream X has a new commit, run refresh-X.sh".

Design constraints (see docs/protocols/brain-improvement-gate.md — Level -1/0):
- Free, local-first: one `git ls-remote <url> HEAD` per vendor, 3s timeout.
- Throttled: a vendor is only re-checked if its cache entry is >24h old.
- Cached: last known upstream sha + last-checked timestamp live in
  .tmp/vendor-check-cache.json (gitignored — see .gitignore `.tmp/`).
- Silent by default: quiet when current; any failure (offline, timeout,
  corrupt cache, unwritable cache dir, unexpected exception) degrades to
  "no notice" — this module must never raise out of check_vendors().
- Pure logic / injectable runner: no test in tests/test_vendor_watch.py
  touches the real network — see `runner` param on check_vendors().

Wired into scripts/hooks/session_start.py (best-effort, wrapped so any
exception there also degrades to silence).
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

# Emoji in the notice line crashes on non-UTF-8 consoles (Thai Windows =
# cp874). Degrade unencodable characters instead of dying — same pattern as
# scripts/regen-skill-surfaces.py / scripts/check-privacy.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = REPO_ROOT / ".tmp" / "vendor-check-cache.json"

STALE_AFTER_HOURS = 24
LS_REMOTE_TIMEOUT_SECONDS = 3


@dataclass(frozen=True)
class Vendor:
    name: str
    url: str
    refresh_script: str  # repo-relative, e.g. "scripts/refresh-9arm.sh"


# Derived by reading each refresh-*.sh script's REMOTE/URL/BRANCH header.
VENDORS: tuple[Vendor, ...] = (
    Vendor("9arm", "https://github.com/thananon/9arm-skills.git", "scripts/refresh-9arm.sh"),
    Vendor("ecosystem", "https://github.com/affaan-m/ECC.git", "scripts/refresh-ecosystem.sh"),
    Vendor("mattpocock", "https://github.com/mattpocock/skills.git", "scripts/refresh-mattpocock.sh"),
    Vendor("anthropic-skills", "https://github.com/anthropics/skills.git", "scripts/refresh-anthropic-skills.sh"),
    Vendor("skillopt", "https://github.com/microsoft/SkillOpt.git", "scripts/refresh-skillopt.sh"),
)

RunnerFn = Callable[[str, str], Optional[str]]


def default_runner(name: str, url: str) -> Optional[str]:
    """Run `git ls-remote <url> HEAD` with a short timeout.

    Returns the full HEAD sha, or None on any failure (offline, timeout,
    nonzero exit, unparsable output). Never raises.
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", url, "HEAD"],
            capture_output=True,
            text=True,
            timeout=LS_REMOTE_TIMEOUT_SECONDS,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    stdout = (result.stdout or "").strip()
    if not stdout:
        return None

    first_line = stdout.splitlines()[0]
    sha = first_line.split()[0].strip() if first_line.split() else ""
    if len(sha) < 7:
        return None
    return sha


def load_cache(cache_path: Path = CACHE_PATH) -> dict:
    """Read the vendor-check cache. Any read/parse failure -> empty dict."""
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(cache: dict, cache_path: Path = CACHE_PATH) -> None:
    """Write the vendor-check cache. Never raises — best-effort only."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, sort_keys=True)
    except Exception:
        pass


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_stale(entry: dict, now: datetime, stale_after_hours: float) -> bool:
    """A vendor is stale (needs a fresh ls-remote) if it has never been
    checked, or its last check is older than stale_after_hours."""
    last_checked = entry.get("last_checked") if entry else None
    if not last_checked:
        return True
    checked_dt = _parse_iso(last_checked)
    if checked_dt is None:
        return True
    age_hours = (now - checked_dt).total_seconds() / 3600
    return age_hours > stale_after_hours


def format_notice(vendor: Vendor, sha: str) -> str:
    short_sha = sha[:7]
    return (
        f"\U0001f504 vendor {vendor.name}: new upstream commit {short_sha} "
        f"— run: bash {vendor.refresh_script}"
    )


def check_vendors(
    vendors: Iterable[Vendor] = VENDORS,
    cache_path: Path = CACHE_PATH,
    runner: RunnerFn = default_runner,
    now: Optional[datetime] = None,
    stale_after_hours: float = STALE_AFTER_HOURS,
) -> list[str]:
    """Check each vendor's upstream HEAD, throttled by the on-disk cache.

    For every vendor whose cache entry is stale (or missing), calls
    `runner(vendor.name, vendor.url)` to get the current upstream sha. If
    that differs from the previously cached sha, appends a notice line.
    The first-ever check for a vendor only establishes a baseline (no prior
    sha to compare against) and does not notify.

    Never raises: any per-vendor failure (runner exception, runner
    returning None, cache corruption) is skipped silently and does not
    block the other vendors. The whole function degrades to an empty list
    on catastrophic failure (e.g. an unwritable cache directory).
    """
    try:
        now = now or datetime.now(timezone.utc)
        cache = load_cache(cache_path)
        notices: list[str] = []
        changed = False

        for vendor in vendors:
            try:
                entry = cache.get(vendor.name, {}) if isinstance(cache, dict) else {}
                if not _is_stale(entry, now, stale_after_hours):
                    continue

                sha = runner(vendor.name, vendor.url)
                if not sha:
                    continue

                previous_sha = entry.get("last_sha") if isinstance(entry, dict) else None
                cache[vendor.name] = {
                    "last_checked": now.isoformat(),
                    "last_sha": sha,
                }
                changed = True

                if previous_sha and previous_sha != sha:
                    notices.append(format_notice(vendor, sha))
            except Exception:
                continue

        if changed:
            save_cache(cache, cache_path)

        return notices
    except Exception:
        return []


if __name__ == "__main__":
    for line in check_vendors():
        print(line)
