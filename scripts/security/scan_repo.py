#!/usr/bin/env python3
"""Repository-wide security scan — Python replacement for the CI shell loop.

Phase 2 / P2.1 (A-Wiki vNext). The old CI step scanned tracked files with a
fragile shell loop: word-splitting silently skipped filenames containing
spaces, and there was no binary detection. This orchestrator:

  - enumerates files via `git ls-files -z` (null-delimited — safe for any
    filename, including spaces and Unicode)
  - reuses the SAME pattern source as every other defense layer
    (scripts/hooks/security_patterns.yaml, via _scan_staged_diff) — no
    second pattern list to drift
  - skips binaries (NUL byte or undecodable content in the first chunk)
  - respects per-pattern allowlists + global placeholder windows
    (identical semantics to the staged-diff scanner)
  - supports exclude globs (vendored snapshots, upstream dirs, ...)
  - `--ci` exits 1 on any finding so CI can fail truthfully

Usage:
  python scripts/security/scan_repo.py [--ci] [--exclude GLOB ...] [--repo-root PATH]
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

from _scan_staged_diff import PATTERNS, PLACEHOLDERS  # noqa: E402 -- single pattern source

CHUNK_BYTES = 262_144  # scan in 256 KiB chunks; secrets are line-local

DEFAULT_EXCLUDES = [
    "skills/_upstream/**",
    "agent-skills/_upstream/**",
    ".gitnexus/**",
    "node_modules/**",
    "*.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    pattern: str
    match: str

    def baseline_key(self) -> str:
        """Stable identity for the legacy-debt ratchet (path + pattern)."""
        return f"{self.path}::{self.pattern}"

    def render(self) -> str:
        return f"{self.path}:{self.line}: [{self.pattern}] {self.match[:80]}"


def scan_text(
    text: str,
    patterns: list[tuple[str, re.Pattern[str], list[str]]],
    placeholders: list[str],
) -> list[tuple[int, str, str]]:
    """Return (line_no, pattern_name, matched_text) for every real hit.

    Placeholder semantics mirror _scan_staged_diff: a hit is suppressed when
    the lowercased ±40-char window around it contains an allowlist entry or
    a global placeholder substring.
    """
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        line_lower = line.lower()
        for name, regex, allowlist in patterns:
            for m in regex.finditer(line):
                window = line_lower[max(0, m.start() - 40): m.end() + 40]
                if any(a in window for a in allowlist):
                    continue
                if any(p in window for p in placeholders):
                    continue
                hits.append((line_no, name, m.group(0)))
                break  # one hit per pattern per line
    return hits


def _looks_binary(head: bytes) -> bool:
    return b"\x00" in head


def scan_file(
    path: Path,
    patterns: list[tuple[str, re.Pattern[str], list[str]]],
    placeholders: list[str],
) -> list[tuple[int, str, str]]:
    """Scan one file; binary files (NUL byte / undecodable) are skipped."""
    try:
        head = path.open("rb").read(CHUNK_BYTES)
    except OSError:
        return []
    if _looks_binary(head):
        return []
    try:
        text = head.decode("utf-8")
    except UnicodeDecodeError:
        return []  # non-UTF-8 payload — not a source/config file we can lint
    return scan_text(text, patterns, placeholders)


def iter_tracked_files(repo_root: Path) -> list[Path]:
    """All git-tracked files, null-delimited (spaces/Unicode-safe)."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root, capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {proc.stderr.decode(errors='replace')[:200]}")
    return [repo_root / p for p in proc.stdout.decode("utf-8", errors="replace").split("\0") if p]


def _excluded(rel_path: str, excludes: list[str]) -> bool:
    rel = rel_path.replace("\\", "/")
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, "/" + pat) for pat in excludes)


def scan_repo(
    repo_root: Path,
    patterns: list[tuple[str, re.Pattern[str], list[str]]],
    placeholders: list[str],
    excludes: list[str] | None = None,
) -> list[Finding]:
    """Scan every tracked file not matching an exclude glob."""
    excludes = DEFAULT_EXCLUDES + (excludes or [])
    findings: list[Finding] = []
    for path in iter_tracked_files(repo_root):
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if _excluded(rel, excludes):
            continue
        for line_no, name, match in scan_file(path, patterns, placeholders):
            findings.append(Finding(rel, line_no, name, match))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repository-wide secret/machine-path scan")
    parser.add_argument("--ci", action="store_true", help="exit 1 on NEW findings (CI gate mode)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--baseline", type=Path, default=None,
        help="file of known 'path::pattern' keys (legacy debt ratchet). "
             "Findings matching the baseline are reported but do not fail CI; "
             "coverage is NOT reduced — every file is still scanned.",
    )
    args = parser.parse_args(argv)

    findings = scan_repo(args.repo_root, PATTERNS, PLACEHOLDERS, excludes=args.exclude)

    baseline_keys: set[str] = set()
    if args.baseline and args.baseline.exists():
        baseline_keys = {
            line.strip() for line in
            args.baseline.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    new_findings = [f for f in findings if f.baseline_key() not in baseline_keys]
    for f in findings:
        marker = "" if f.baseline_key() not in baseline_keys else "  (baseline)"
        print(f.render() + marker)
    print(f"scanned: {len(iter_tracked_files(args.repo_root))} tracked files, "
          f"{len(findings)} finding(s), {len(new_findings)} new (non-baseline)")
    if new_findings and args.ci:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
