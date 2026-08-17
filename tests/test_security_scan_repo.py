"""Tests for scripts/security/scan_repo.py — Python security-scan orchestrator.

Iron Law #1: failing tests written FIRST (Phase 2 / P2.1).

The CI security scan used to be a fragile shell loop (word-splitting on
filenames with spaces, silent coverage caps). This module replaces it:
scan ALL tracked files for secret + machine-path patterns, skip binaries,
respect placeholders, exit non-zero on findings in --ci mode.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "security"))

import scan_repo as sr  # noqa: E402 -- module under test


PATTERNS = [
    ("test token", re.compile(r"ghp_[A-Za-z0-9]{20,}"), []),
    ("drive letter", re.compile(r"[A-Z]:\\\\Users\\\\[A-Za-z0-9._-]+"),
     ["placeholder"]),
]
PLACEHOLDERS = ["placeholder", "example"]


# ---------------------------------------------------------------------------
# scan_text — pure pattern core
# ---------------------------------------------------------------------------
def test_scan_text_flags_secret_line():
    hits = sr.scan_text('token = "ghp_' + "A1b2c3d4e5f6g7h8i9j0k1l2" + '"', PATTERNS, PLACEHOLDERS)
    assert len(hits) == 1
    assert hits[0][1] == "test token"


def test_scan_text_allows_placeholder_window():
    hits = sr.scan_text("# placeholder example: ghp_A1b2c3d4e5f6g7h8i9j0k1l2", PATTERNS, PLACEHOLDERS)
    assert hits == []


def test_scan_text_reports_line_numbers():
    text = "clean line\nalso clean\ntoken = ghp_" + "A1b2c3d4e5f6g7h8i9j0k1l2" + "\n"
    hits = sr.scan_text(text, PATTERNS, PLACEHOLDERS)
    assert hits[0][0] == 3


# ---------------------------------------------------------------------------
# scan_file — binary detection
# ---------------------------------------------------------------------------
def test_scan_file_skips_binary_nul_content(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"ghp_" + b"A1b2c3d4e5f6g7h8i9j0k1l2" + b"\x00\x01\x02binary")
    assert sr.scan_file(f, PATTERNS, PLACEHOLDERS) == []


def test_scan_file_handles_utf8_text(tmp_path):
    f = tmp_path / "ไฟล์ทดสอบ.py"  # non-ASCII filename must not break scanning
    f.write_text('k = "ghp_' + "A1b2c3d4e5f6g7h8i9j0k1l2" + '"', encoding="utf-8")
    hits = sr.scan_file(f, PATTERNS, PLACEHOLDERS)
    assert len(hits) == 1


# ---------------------------------------------------------------------------
# scan_repo — tracked-file iteration survives spaces in filenames
# ---------------------------------------------------------------------------
def _init_repo_with_file(tmp_path, name, content):
    f = tmp_path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"],
        cwd=tmp_path, check=True,
    )


def test_scan_repo_covers_filename_with_spaces(tmp_path):
    name = "docs with spaces/notes file.md"
    (tmp_path / "docs with spaces").mkdir()
    _init_repo_with_file(tmp_path, name, "secret ghp_" + "A1b2c3d4e5f6g7h8i9j0k1l2" + " here")
    findings = sr.scan_repo(tmp_path, PATTERNS, PLACEHOLDERS, excludes=[])
    assert any("notes file.md" in f.path.replace("\\", "/") for f in findings), (
        "filenames with spaces must be scanned, not word-split away"
    )


def test_scan_repo_respects_exclude_globs(tmp_path):
    _init_repo_with_file(tmp_path, "vendored/lib.py", "ghp_" + "A1b2c3d4e5f6g7h8i9j0k1l2")
    findings = sr.scan_repo(tmp_path, PATTERNS, PLACEHOLDERS, excludes=["vendored/**"])
    assert findings == []


def test_scan_repo_clean_repo_has_no_findings(tmp_path):
    _init_repo_with_file(tmp_path, "clean.py", "print('hello')\n")
    assert sr.scan_repo(tmp_path, PATTERNS, PLACEHOLDERS, excludes=[]) == []


# ---------------------------------------------------------------------------
# CLI — exit codes + baseline ratchet
# ---------------------------------------------------------------------------
def _planted_repo(tmp_path):
    token = "ghp_" + "Z9" + "0123456789abcdef" * 2  # 36 chars — matches real gh pattern
    _init_repo_with_file(tmp_path, "src/app.py", f"k = '{token}'")
    return tmp_path


def test_cli_ci_mode_flags_planted_secret(tmp_path):
    _planted_repo(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 1, f"planted secret must fail CI mode:\n{proc.stdout[:300]}"


def test_cli_baseline_ratchet_allows_known_and_fails_new(tmp_path):
    legacy_token = "ghp_" + "A1" + "0123456789abcdef" * 2  # 34 chars — matches real gh pattern
    _init_repo_with_file(tmp_path, "legacy.py", f"old {legacy_token} debt")
    baseline = tmp_path / "baseline.txt"
    first = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert first.returncode == 1
    # ratchet: record the legacy finding as baseline keys ("path::pattern")
    keys = [
        f"{m.group(1)}::{m.group(2)}"
        for l in first.stdout.splitlines()
        if (m := re.match(r"^(.*?):\d+: \[(.*?)\]", l))
    ]
    baseline.write_text("\n".join(f"{k}" for k in keys), encoding="utf-8")
    second = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--baseline", str(baseline), "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert second.returncode == 0, f"baseline findings must pass:\n{second.stdout[:300]}"
    # a NEW finding must still fail
    new_token = "ghp_" + "B3" + "0123456789abcdef" * 2  # 34 chars — matches real gh pattern
    (tmp_path / "new.py").write_text(f"new {new_token} leak")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "y"], cwd=tmp_path, check=True)
    third = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--baseline", str(baseline), "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert third.returncode == 1, "new findings must fail even with a baseline"
