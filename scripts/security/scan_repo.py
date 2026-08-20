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
  - streams EVERY line of every tracked text file — no silent byte cap
    (R-P2-002); binaries (NUL byte in the sniff window) are skipped by
    explicit policy
  - respects per-pattern allowlists + global placeholder windows
    (identical semantics to the staged-diff scanner)
  - supports exclude globs (vendored snapshots, upstream dirs, ...)
  - baseline ratchet keys are path::pattern::fingerprint — finding-specific
    and multiplicity-aware via Counter, with NO raw secrets stored (R-P2-003)
  - `--ci` exits 1 on any non-baselined finding so CI fails truthfully

Usage:
  python scripts/security/scan_repo.py [--ci] [--exclude GLOB ...] [--repo-root PATH]
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

from _scan_staged_diff import (  # noqa: E402 -- single pattern source
    PLACEHOLDERS, PatternSourceUnavailable, _load_patterns)

# CI mode loads the pattern source STRICTLY: a missing/broken yaml
# pattern file must abort the scan, never quietly degrade to the
# builtin subset (2026-08-20 incident: dependency-less Python made
# every baseline key mismatch → 20 phantom findings).

# Back-compat module surface for existing tests/tools (non-strict load —
# the STRICT load happens per-run inside main() when --ci is set).
PATTERNS = _load_patterns()

BINARY_SNIFF_BYTES = 8192  # NUL-byte detection window ONLY — not a scan cap (R-P2-002)

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

    def fingerprint(self) -> str:
        """Stable, secret-free digest of the matched value (R-P2-003)."""
        return hashlib.sha256(self.match.encode("utf-8")).hexdigest()[:16]

    def baseline_key(self) -> str:
        """Finding-specific ratchet identity — path + pattern + match digest.

        Coarse path::pattern keys suppressed NEW same-pattern findings in the
        same file; the fingerprint makes the ratchet finding-specific while
        keeping raw secrets out of baseline files. Multiplicity is handled by
        the Counter the caller builds from these keys.
        """
        return f"{self.path}::{self.pattern}::{self.fingerprint()}"

    def render(self) -> str:
        return f"{self.path}:{self.line}: [{self.pattern}] {self.match[:80]}"


def _scan_line(line: str, patterns, placeholders) -> list[tuple[str, str]]:
    """All real hits in one line: (pattern_name, matched_text)."""
    out: list[tuple[str, str]] = []
    line_lower = line.lower()
    for name, regex, allowlist in patterns:
        for m in regex.finditer(line):
            window = line_lower[max(0, m.start() - 40): m.end() + 40]
            if any(a in window for a in allowlist):
                continue
            if any(p in window for p in placeholders):
                continue
            out.append((name, m.group(0)))
            break  # one hit per pattern per line
    return out


def scan_text(
    text: str,
    patterns: list[tuple[str, re.Pattern[str], list[str]]],
    placeholders: list[str],
) -> list[tuple[int, str, str]]:
    """Return (line_no, pattern_name, matched_text) for every real hit."""
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for name, match in _scan_line(line, patterns, placeholders):
            hits.append((line_no, name, match))
    return hits


def scan_file(
    path: Path,
    patterns: list[tuple[str, re.Pattern[str], list[str]]],
    placeholders: list[str],
) -> list[tuple[int, str, str]]:
    """Stream EVERY line of the file — no byte cap (R-P2-002).

    Binary policy: NUL byte in the sniff window → skip (explicit, narrow).
    All other bytes are decoded with replacement and scanned, so a secret
    anywhere in the file — including past any size boundary — is detected.
    """
    try:
        with path.open("rb") as raw:
            if b"\x00" in raw.read(BINARY_SNIFF_BYTES):
                return []
            raw.seek(0)
            hits: list[tuple[int, str, str]] = []
            with io.TextIOWrapper(raw, encoding="utf-8", errors="replace") as tf:
                for line_no, line in enumerate(tf, 1):
                    for name, match in _scan_line(line, patterns, placeholders):
                        hits.append((line_no, name, match))
            return hits
    except OSError:
        return []


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
        help="file of known 'path::pattern::fingerprint' keys (legacy debt "
             "ratchet). Multiplicity-aware: N identical baselined occurrences "
             "suppress exactly N findings; anything beyond fails. No raw "
             "secrets are stored — keys carry a sha256 digest only.",
    )
    args = parser.parse_args(argv)

    patterns = _load_patterns(strict=args.ci)
    findings = scan_repo(args.repo_root, patterns, PLACEHOLDERS, excludes=args.exclude)

    baseline_counts: Counter[str] = Counter()
    if args.baseline and args.baseline.exists():
        baseline_counts = Counter(
            line.strip() for line in
            args.baseline.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        )

    remaining = baseline_counts.copy()
    new_findings: list[Finding] = []
    baselined: list[Finding] = []
    for f in findings:
        key = f.baseline_key()
        if remaining[key] > 0:
            remaining[key] -= 1
            baselined.append(f)
        else:
            new_findings.append(f)
    for f in new_findings:
        print(f.render())
    for f in baselined:
        print(f.render() + "  (baseline)")
    print(f"scanned: {len(iter_tracked_files(args.repo_root))} tracked files, "
          f"{len(findings)} finding(s), {len(new_findings)} new (non-baseline)")
    if new_findings and args.ci:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
