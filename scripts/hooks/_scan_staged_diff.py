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


def _load_patterns() -> list[tuple[str, re.Pattern[str], list[str]]]:
    """Load secret + machine-path patterns from YAML (builtin fallback)."""
    builtin_secrets = [
        ("sk- key", re.compile(r"sk-[A-Za-z0-9_-]{24,}")),
        ("AIza key", re.compile(r"AIza[0-9A-Za-z_-]{30,}")),
        ("gh token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}")),
        ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ]
    builtin_machine = [
        ("Windows user home", re.compile(r"C:\\Users\\([A-Za-z0-9._-]+)\\")),
        ("macOS user home", re.compile(r"/Users/([A-Za-z0-9._-]+)/")),
        ("Google Drive account", re.compile(r"CloudStorage/GoogleDrive-([A-Za-z0-9._-]+)")),
    ]
    try:
        import yaml  # type: ignore
    except ImportError:
        return builtin_secrets + builtin_machine
    if not PATTERNS_FILE.exists():
        return builtin_secrets + builtin_machine
    try:
        data = yaml.safe_load(PATTERNS_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return builtin_secrets + builtin_machine
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
    return out or (builtin_secrets + builtin_machine)


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
