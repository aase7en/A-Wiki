"""Tests for scripts/hooks/_scan_staged_diff.py — Layer 3 pre-commit scanner.

Scans a unified diff (stdin) for secret + machine-path patterns. Exit 0
always — the caller (pre-commit-awiki.sh) decides whether to block based
on stdout output (empty = clean).
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "_scan_staged_diff.py"


def _run(diff_text: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=diff_text,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=os.environ, cwd=str(REPO_ROOT), timeout=30)


def test_clean_diff_produces_no_output():
    r = _run("+def foo():\n+    return 1\n")
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_detects_secret_in_added_line():
    r = _run('+API_KEY = "sk-' + "A" * 30 + '"\n')
    assert r.returncode == 0  # advisory, exit 0
    # but should print findings to stdout
    assert "sk-" in r.stdout.lower() or "secret" in r.stdout.lower() or "key" in r.stdout.lower()


def test_ignores_removed_lines():
    """Only ADDED lines (starting with '+') should be scanned."""
    r = _run('-API_KEY = "sk-' + "A" * 30 + '"\n')
    assert r.returncode == 0
    # Removed line should not trigger findings
    assert r.stdout.strip() == ""


def test_fail_open_on_empty_stdin():
    r = _run("")
    assert r.returncode == 0


class TestWiring:
    def test_referenced_in_pre_commit_script(self):
        """The hook is invoked from pre-commit-awiki.sh, not directly."""
        precommit = REPO_ROOT / "scripts" / "hooks" / "pre-commit-awiki.sh"
        if not precommit.exists():
            return  # skip if pre-commit script doesn't exist
        content = precommit.read_text(encoding="utf-8")
        assert "_scan_staged_diff" in content or "scan_staged" in content, (
            "_scan_staged_diff must be referenced in pre-commit-awiki.sh"
        )
