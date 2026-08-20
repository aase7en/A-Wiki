"""Scan a unified diff (stdin) for secret + machine-path patterns.

Used by pre-commit-awiki.sh (Layer 2). Loads patterns from
scripts/hooks/security_patterns.yaml (USA-1 §5.3 single source) and flags any
match in ADDED lines (lines starting with '+' but not '+++').

Outputs human-readable findings to stdout (empty = clean). Exit 0 always —
the caller (pre-commit-awiki.sh) decides whether to block based on output.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERNS_FILE = REPO_ROOT / "scripts" / "hooks" / "security_patterns.yaml"


class PatternSourceUnavailable(RuntimeError):
    """The canonical yaml pattern source cannot be used. In strict/CI mode
    this ABORTS the scan — a silently degraded pattern set is how the
    2026-08-20 PR #17 CI incident produced 20 phantom baseline mismatches."""


def _load_patterns(strict: bool = False) -> list[tuple[str, re.Pattern[str], list[str]]]:
    """Load secret + machine-path patterns from YAML (builtin fallback).

    Every entry — YAML-loaded or builtin — is a 3-tuple (name, regex,
    allowlist). The builtin fallback previously emitted 2-tuples, which
    crashed the scan loop in environments without PyYAML and turned the
    layer-2 gate fail-open (2026-08-17, P2.1 root cause).
    """
    builtin_secrets = [
        ("sk- key", re.compile(r"sk-[A-Za-z0-9_-]{24,}"), []),
        ("AIza key", re.compile(r"AIza[0-9A-Za-z_-]{30,}"), []),
        ("gh token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"), []),
        ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), []),
    ]
    builtin_machine = [
        ("Windows user home", re.compile(r"C:\\Users\\([A-Za-z0-9._-]+)\\"), []),
        ("macOS user home", re.compile(r"/Users/([A-Za-z0-9._-]+)/"), []),
        ("Google Drive account", re.compile(r"CloudStorage/GoogleDrive-([A-Za-z0-9._-]+)"), []),
    ]
    def _unavailable(reason: str):
        if strict:
            raise PatternSourceUnavailable(
                f"security pattern source unavailable ({reason}) — refusing "
                f"to scan with a degraded pattern set in strict/CI mode. "
                f"Fix the environment (install PyYAML / restore "
                f"{PATTERNS_FILE}) and re-run.")
        sys.stderr.write(
            f"⚠️  security pattern source unavailable ({reason}) — falling "
            f"back to the SMALL builtin pattern subset; coverage is reduced "
            f"until this is fixed.\n")
        return builtin_secrets + builtin_machine

    try:
        import yaml  # type: ignore
    except ImportError:
        return _unavailable("PyYAML not installed")
    if not PATTERNS_FILE.exists():
        return _unavailable(f"missing {PATTERNS_FILE}")
    try:
        data = yaml.safe_load(PATTERNS_FILE.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return _unavailable(f"malformed yaml: {e}")
    out: list[tuple[str, re.Pattern[str], list[str]]] = []
    for key in ("secret_patterns", "machine_path_patterns"):
        for e in data.get(key) or []:
            try:
                out.append((
                    e.get("name", "unnamed"),
                    re.compile(e["regex"]),
                    [s.lower() for s in e.get("allowlist", [])],
                ))
            except (KeyError, re.error):
                continue
    if not out:
        return _unavailable("yaml loaded but defines no patterns")
    return out


PATTERNS = _load_patterns()
PLACEHOLDERS = ["...", "example", "placeholder", "redacted", "your_", "your-",
                "xxxx", "<", ">", "test", "demo", "sample"]


def main() -> int:
    diff = sys.stdin.read()
    findings: list[str] = []
    for line in diff.splitlines():
        # Only scan ADDED lines (unified diff: starts with '+' but not '+++').
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        content_lower = content.lower()
        for name, regex, allowlist in PATTERNS:
            for m in regex.finditer(content):
                window = content_lower[max(0, m.start() - 40): m.end() + 40]
                # Check both the pattern's own allowlist and the global placeholders.
                if any(a in window for a in allowlist):
                    continue
                if any(p in window for p in PLACEHOLDERS):
                    continue
                findings.append(f"  {name}: {m.group(0)[:80]}")
                break  # one hit per pattern per line
    if findings:
        print("\n".join(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
