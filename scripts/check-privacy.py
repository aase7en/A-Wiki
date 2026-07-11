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
  - Tracked-but-gitignored files (escaped-private-file bug class — a file
    that got `git add -f`'d once and stayed tracked even though .gitignore
    now excludes it)
  - Extra P0 personal-data regexes, loaded at runtime from the private,
    gitignored drive/personal/privacy-patterns.txt (never hardcoded here)

Skips:
  - Binary files (null-byte sniff on the first 8KB) — an .xlsx is never
    scanned as text
  - Font/OSS license boilerplate (*-OFL.txt, LICENSE*) for email checks only

Safe patterns (whitelisted):
  - example.com, example.org, a-wiki.local domains
  - .local / .ts.net hostnames (LAN mDNS, Tailscale MagicDNS) — not emails
  - `ssh user@host` targets — not an email address
  - bot@<anything> — a bot identity, not a personal email
  - `<your-...>`, `${...}`, `$HOME`, `~/...` template forms
  - `aase7en/A-Wiki` and `aase7en.github.io` (public, intended)

Usage:
  python3 scripts/check-privacy.py             # exit 0 = clean
  python3 scripts/check-privacy.py --verbose   # show all matches
  python3 scripts/check-privacy.py --json      # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Emoji in status prints (✅ / 🚨) crash on non-UTF-8 consoles (Thai Windows =
# cp874), turning a clean scan into a crash instead of a clean exit code.
# Same fix as scripts/regen-skill-surfaces.py — degrade unencodable characters
# instead of dying.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parent.parent

# Codenames / handles to scrub. Add yours here when forking.
PERSONAL_CODENAMES = [
    r"aase7en(?!/A-Wiki|\.github\.io)",  # github handle in repo URLs / Pages domain is OK
    r"Asse7en",
    r"sunday-estate",
    r"richbusinessman",
]

# Hardcoded home directory paths (any platform).
# Each pattern MUST have one capture group = the username, so that
# ``_is_system_user(m)`` can allowlist container/OS default accounts.
HOME_PATH_PATTERNS = [
    r"/Users/([A-Za-z0-9._-]+)/",      # macOS
    r"/home/([A-Za-z0-9._-]+)/",        # Linux
    r"C:\\\\Users\\\\([A-Za-z0-9._-]+)\\\\",  # Windows escaped
    r"C:/Users/([A-Za-z0-9._-]+)/",     # Windows forward-slash
]

# Usernames that are NOT personal — they're container/OS default accounts
# (Docker ``node`` image, Raspberry Pi OS ``pi``, Umbrel ``umbrel``, …).
# Matches from HOME_PATH_PATTERNS whose captured group is in this set are
# suppressed so the scan doesn't drown in ~17 false-positives per Hermes run.
# Rationale: docs/architecture/hermes-cross-agent-handoff.md §"RCA findings"
# — the Docker node user + RPi OS pi user showed up as 17 spurious leaks.
SYSTEM_USERS: frozenset[str] = frozenset({
    "node",        # official node Docker image default user
    "pi",          # Raspberry Pi OS default user
    "umbrel",      # Umbrel app-store server default user
    "ubuntu",      # official ubuntu Docker image / Ubuntu cloud images
    "root",        # universal superuser (system, not personal)
    "nobody",      # unprivileged system account (nginx, etc.)
    "app", "appuser", "www-data", "wwwrun",  # common service accounts
    # Doc-placeholder home paths, e.g. C:/Users/you/, /home/user/ — generic
    # example usernames in READMEs/runbooks, never real people.
    "name", "user", "work", "you",
})

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
    "gitlab.com",
    "codeberg.org",
    "example.co.th",
    "etda.or.th",
    "pdpc.or.th",
}

# Substrings that mark a line as a template/example, not a real value.
TEMPLATE_MARKERS = (
    "YOUR_", "<your-", "<YOUR_", "${", "<repo-",
    "example.com", "example.org", "example.co.th",
    "GoogleDrive-<", "GoogleDrive-${",
    "/Users/me/", "/home/ubuntu/",
    "XXXXXXXX", "sk-management-dashboard",
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
    "CLAUDE.md",                     # protected doc; scrub only with explicit user permission
}
SKIP_DIRS = {"raw", "drive", ".git", "node_modules", ".pytest_cache", "__pycache__"}
SKIP_PREFIXES = (
    # Vendored upstream skills keep their original examples and test fixtures.
    "skills/_upstream/",
    "skills/anthropic-skills/",
    "skills/ecosystem/",
    "skills/claude-code/",
    "skills/delegation/",
    "skills/claude-thai/",
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


EMAIL_WHITELIST_DOMAIN_SUFFIXES = (
    ".local",   # mDNS / LAN hostnames (umbrel.local, myhost.local) — not real email
    ".ts.net",  # Tailscale MagicDNS hostnames (host.tailXXXX.ts.net)
)


def email_is_personal(addr: str) -> bool:
    local = addr.split("@", 1)[0].lower() if "@" in addr else ""
    domain = addr.split("@", 1)[1].lower() if "@" in addr else ""
    if domain in EMAIL_WHITELIST_DOMAINS:
        return False
    if domain.endswith(EMAIL_WHITELIST_DOMAIN_SUFFIXES):
        return False
    if local == "bot":  # bot@<anything> — a bot identity, not a personal email
        return False
    return True


_SSH_TARGET_PREFIX_RE = re.compile(r"(?:^|\s)ssh\s+$")


def _preceded_by_ssh(line: str, match_start: int) -> bool:
    """True if the text right before an email-shaped match is ``ssh ``.

    ``ssh user@host`` names an SSH target, not an email address — e.g.
    ``ssh umbrel@umbrel-1.tail<id>.ts.net`` in docs/runbooks/pi5-quick-start.md.
    """
    return bool(_SSH_TARGET_PREFIX_RE.search(line[:match_start]))


def _is_license_like(rel: str) -> bool:
    """Font/OSS license files carry example emails in their own boilerplate
    (SIL OFL, MIT, etc.) — not repo-owner personal data. Skip email checks
    for them (only email checks — other kinds still apply)."""
    name = Path(rel).name
    if name.upper().startswith("LICENSE"):
        return True
    if name.endswith("-OFL.txt"):
        return True
    return False


def is_binary(path: Path, sniff_bytes: int = 8192) -> bool:
    """True if the file looks binary (a NUL byte in the first N bytes).

    Prevents false positives like an .xlsx being flagged for "containing an
    email" when the match is actually inside compressed/binary bytes.
    """
    try:
        with path.open("rb") as fh:
            chunk = fh.read(sniff_bytes)
    except OSError:
        return False
    return b"\x00" in chunk


PRIVACY_PATTERNS_ENV = "AWIKI_PRIVACY_PATTERNS_FILE"
DEFAULT_PRIVACY_PATTERNS_FILE = REPO_ROOT / "drive" / "personal" / "privacy-patterns.txt"


def load_extra_personal_patterns(path: "Path | None" = None) -> list["re.Pattern[str]"]:
    """Load extra personal-data regexes from a private, gitignored file.

    Public-safe repo rule: real name/address/PII patterns must NEVER be
    hardcoded in this public script. Instead, each user drops their own
    regexes (one per line; blank lines and ``#``-prefixed lines are skipped)
    into ``drive/personal/privacy-patterns.txt`` — already gitignored via the
    ``drive`` and ``drive/personal/`` rules in .gitignore — and the scanner
    picks them up automatically. Override the file location with
    ``$AWIKI_PRIVACY_PATTERNS_FILE`` (used by tests) or the ``path`` argument.
    """
    if path is None:
        env_override = os.environ.get(PRIVACY_PATTERNS_ENV)
        path = Path(env_override) if env_override else DEFAULT_PRIVACY_PATTERNS_FILE
    if not path.exists():
        return []
    patterns: list[re.Pattern[str]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            patterns.append(re.compile(line))
        except re.error:
            continue
    return patterns


def tracked_but_ignored() -> list[str]:
    """Tracked files that WOULD be ignored under the current .gitignore rules.

    This is the "escaped-private-file" bug class (the session-memory.md
    incident): a gitignored path got ``git add -f``'d once and silently stays
    tracked forever after, even though .gitignore says it shouldn't be.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-ci", "--exclude-standard"],
            cwd=REPO_ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, OSError):
        return []
    return [p for p in out if p]


def _is_system_user(match: re.Match) -> bool:
    """True if a HOME_PATH_PATTERNS match captures a known container/OS user.

    HOME_PATH_PATTERNS is an alternation of per-OS patterns, each with its
    OWN capture group for the username.  Because only the matched branch's
    group is non-None, we scan ``match.groups()`` for the first captured
    value rather than reading a fixed index.  Suppresses ``/home/node/``,
    ``/home/pi/``, etc. so they don't show up as personal leaks.
    """
    for user in match.groups():
        if user is not None:
            return user in SYSTEM_USERS
    return False


def scan(
    verbose: bool = False,
    files: "list[Path] | None" = None,
    extra_patterns_path: "Path | None" = None,
) -> list[dict]:
    """Scan tracked files (or an injected ``files`` list, for tests) for
    personal/private data.

    ``files=None`` (the default / real CLI usage) scans every git-tracked
    file AND runs the repo-wide ``tracked_but_ignored()`` check. Passing an
    explicit ``files`` list (as tests do) scopes the scan to just those
    paths and skips the repo-wide check, which needs a real git repo rooted
    at ``REPO_ROOT``.
    """
    findings: list[dict] = []
    codename_re = re.compile("|".join(PERSONAL_CODENAMES))
    home_re = re.compile("|".join(HOME_PATH_PATTERNS))
    cloud_re = re.compile("|".join(CLOUDSTORAGE_PATTERNS))
    email_re = re.compile(EMAIL_PATTERN)
    secret_res = [(re.compile(p), label) for p, label in SECRET_PATTERNS]
    extra_patterns = load_extra_personal_patterns(extra_patterns_path)

    scan_files = tracked_files() if files is None else files

    for path in scan_files:
        if should_skip(path):
            continue
        if is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = path.relative_to(REPO_ROOT).as_posix()
        license_like = _is_license_like(rel)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in codename_re.finditer(line):
                findings.append({
                    "file": rel, "line": lineno, "kind": "codename",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            for m in home_re.finditer(line):
                if any(tm in line for tm in TEMPLATE_MARKERS):
                    continue
                if _is_system_user(m):
                    continue
                findings.append({
                    "file": rel, "line": lineno, "kind": "home_path",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            for m in cloud_re.finditer(line):
                findings.append({
                    "file": rel, "line": lineno, "kind": "cloudstorage",
                    "match": m.group(0), "context": line.strip()[:160],
                })
            if not license_like:
                for m in email_re.finditer(line):
                    if _preceded_by_ssh(line, m.start()):
                        continue
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
            for rx in extra_patterns:
                for m in rx.finditer(line):
                    findings.append({
                        "file": rel, "line": lineno, "kind": "P0/personal-data",
                        "match": m.group(0), "context": line.strip()[:160],
                    })

    if files is None:
        for rel in tracked_but_ignored():
            findings.append({
                "file": rel, "line": 0, "kind": "tracked-but-gitignored",
                "match": rel,
                "context": "tracked in git but matches current .gitignore rules "
                           "— escaped-private-file risk",
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

    # High-priority kinds (structural leaks / explicit PII) surface first,
    # ahead of the alphabetically-sorted rest.
    _HIGH_PRIORITY_KINDS = ("tracked-but-gitignored", "P0/personal-data")

    def _kind_sort_key(kind: str) -> tuple[int, str]:
        if kind in _HIGH_PRIORITY_KINDS:
            return (0, str(_HIGH_PRIORITY_KINDS.index(kind)))
        return (1, kind)

    print(f"🚨 check-privacy: {len(findings)} finding(s) across {len({f['file'] for f in findings})} file(s)\n")
    for kind in sorted(by_kind, key=_kind_sort_key):
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
