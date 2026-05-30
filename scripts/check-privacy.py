#!/usr/bin/env python3
"""
Pre-publish privacy audit for A-Wiki.
=====================================

Scans TRACKED files (git ls-files) for personal/private data that would leak
if the repo were published. Exits 1 on any finding so it can run in CI
(.github/workflows/secret-scan.yml) or as a pre-push hook.

Detects:
  - Hardcoded user paths (/Users/<name>/, /home/<name>/, C:\\Users\\<name>\\)
  - Personal email addresses (anything but example.com / a-wiki.local placeholders)
  - Known developer codenames / handles (configurable below)
  - Real API keys (sk-..., AIza..., gho_..., etc.)
  - GoogleDrive-* / OneDrive-* CloudStorage paths with account name in them

Safe patterns (whitelisted):
  - example.com, example.org, a-wiki.local domains
  - `<your-...>`, `${...}`, `$HOME`, `~/...` template forms
  - `aase7en/A-Wiki` (the GitHub handle in README badges — public, intended)

Usage:
  python3 scripts/check-privacy.py             # exit 0 = clean
  python3 scripts/check-privacy.py --verbose   # show all matches
  python3 scripts/check-privacy.py --json      # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Codenames / handles to scrub. Add yours here when forking.
PERSONAL_CODENAMES = [
    r"aase7en(?!/A-Wiki)",  # github handle in repo URLs is OK
    r"Asse7en",
    r"sunday-estate",
    r"richbusinessman",
]

# Hardcoded home directory paths (any platform).
HOME_PATH_PATTERNS = [
    r"/Users/[A-Za-z0-9._-]+/",      # macOS
    r"/home/[A-Za-z0-9._-]+/",        # Linux
    r"C:\\\\Users\\\\[A-Za-z0-9._-]+\\\\",  # Windows escaped
    r"C:/Users/[A-Za-z0-9._-]+/",     # Windows forward-slash
]

# CloudStorage paths with account names embedded.
CLOUDSTORAGE_PATTERNS = [
    r"GoogleDrive-[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"OneDrive-[A-Za-z0-9._-]+(?!\*)",
    r"Dropbox-[A-Za-z0-9._-]+(?!\*)",
]

# Email addresses (excluding obviously-fake placeholders).
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
EMAIL_WHITELIST_DOMAINS = {
    "example.com", "example.org", "example.net",
    "a-wiki.local", "test.local", "umbrel.local",
    "noreply.github.com", "users.noreply.github.com",
    "anthropic.com",  # Co-Authored-By in commit trailers is OK if surfaced
    "github.com",     # git@github.com SSH URL prefix is not a real email
}

# Substrings that mark a line as a template/example, not a real value.
TEMPLATE_MARKERS = (
    "YOUR_", "<your-", "<YOUR_", "${", "<repo-",
    "example.com", "example.org",
    "GoogleDrive-<", "GoogleDrive-${",
)

# Real API key shapes.
SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{20,}", "OpenAI-style"),
    (r"sk-ant-[A-Za-z0-9_-]{20,}", "Anthropic"),
    (r"AIza[A-Za-z0-9_-]{30,}", "Google"),
    (r"gho_[A-Za-z0-9]{30,}", "GitHub OAuth"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub PAT"),
    (r"glpat-[A-Za-z0-9_-]{20,}", "GitLab PAT"),
    (r"xoxb-[A-Za-z0-9-]{20,}", "Slack bot"),
]

# Files we never scan (binaries, lock files, our own audit code).
SKIP_PATHS = {
    "scripts/check-privacy.py",      # this file documents the patterns
    "CHANGELOG.md",                  # historical record may cite redacted artifacts
}
SKIP_DIRS = {"raw", "drive", ".git", "node_modules", ".pytest_cache", "__pycache__"}
SKIP_PREFIXES = (
    # Vendored upstream skills keep their original examples and test fixtures.
    "skills/_upstream/",
    "skills/ecosystem/",
)
SKIP_SUFFIXES = {
    ".db", ".sqlite", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf",
    ".onnx", ".bin", ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".zip",
}


def tracked_files() -> list[Path]:
    """Return git-tracked files relative to repo root."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.splitlines()
    return [REPO_ROOT / p for p in out if p]


def should_skip(p: Path) -> bool:
    rel = p.relative_to(REPO_ROOT).as_posix()
    if rel in SKIP_PATHS:
        return True
    if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    parts = set(p.relative_to(REPO_ROOT).parts)
    if parts & SKIP_DIRS:
        return True
    if p.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def email_is_personal(addr: str) -> bool:
    domain = addr.split("@", 1)[1].lower() if "@" in addr else ""
    if domain in EMAIL_WHITELIST_DOMAINS:
        return False
    return True


def scan(verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    codename_re = re.compile("|".join(PERSONAL_CODENAMES))
    home_re = re.compile("|".join(HOME_PATH_PATTERNS))
    cloud_re = re.compile("|".join(CLOUDSTORAGE_PATTERNS))
    email_re = re.compile(EMAIL_PATTERN)
    secret_res = [(re.compile(p), label) for p, label in SECRET_PATTERNS]

    for path in tracked_files():
        if should_skip(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in codename_re.finditer(line):
                findings.append({
                    "file": rel, "line": lineno, "kind": "codename",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            for m in home_re.finditer(line):
                findings.append({
                    "file": rel, "line": lineno, "kind": "home_path",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            for m in cloud_re.finditer(line):
                findings.append({
                    "file": rel, "line": lineno, "kind": "cloudstorage",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            for m in email_re.finditer(line):
                if email_is_personal(m.group(0)):
                    findings.append({
                        "file": rel, "line": lineno, "kind": "email",
                        "match": m.group(0), "context": line.strip()[:160],
                    })
            for rx, label in secret_res:
                for m in rx.finditer(line):
                    # Skip obvious template values like `sk-or-v1-YOUR_KEY_HERE`
                    if any(tm in line for tm in TEMPLATE_MARKERS):
                        continue
                    findings.append({
                        "file": rel, "line": lineno, "kind": f"secret/{label}",
                        "match": m.group(0)[:20] + "…",
                        "context": "(redacted)",
                    })

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="show every match with file:line context")
    ap.add_argument("--json", action="store_true",
                    help="emit findings as JSON (machine-readable)")
    args = ap.parse_args()

    findings = scan(verbose=args.verbose)

    if args.json:
        json.dump(findings, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1 if findings else 0

    if not findings:
        print("✅ check-privacy: no personal data detected in tracked files")
        return 0

    # Group by kind, then by file.
    by_kind: dict[str, list[dict]] = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f)

    print(f"🚨 check-privacy: {len(findings)} finding(s) across {len({f['file'] for f in findings})} file(s)\n")
    for kind in sorted(by_kind):
        items = by_kind[kind]
        print(f"── {kind} ({len(items)}) ──")
        if args.verbose:
            for f in items:
                print(f"  {f['file']}:{f['line']}  {f['match']!r}")
                print(f"     │ {f['context']}")
        else:
            # collapse to file:line list
            seen_files: dict[str, int] = {}
            for f in items:
                seen_files[f["file"]] = seen_files.get(f["file"], 0) + 1
            for fn, n in sorted(seen_files.items()):
                print(f"  {fn}  ({n}×)")
        print()
    print("Re-run with -v / --verbose for line-by-line context.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
