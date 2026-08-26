"""Versioning — G5 Slice V: the brain carries a live, visible version.

Contract: VERSION file is semver, CHANGELOG's newest entry matches it,
`awiki doctor` prints the version, and the version actually moved with
this work (not the stale 2.5-month-old 1.3.0).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_file_is_semver_and_current():
    v = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert SEMVER.fullmatch(v), f"VERSION not semver: {v!r}"
    assert v != "1.3.0", "version must move past the stale 1.3.0"


def test_changelog_newest_entry_matches_version():
    v = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[?v?(\d+\.\d+\.\d+)", text, re.M)
    assert m, "CHANGELOG has no versioned heading"
    assert m.group(1) == v, f"CHANGELOG head {m.group(1)} != VERSION {v}"
    # and the entry is not the stale one
    assert "2026-06-12" not in text.split("\n##", 2)[1]


def test_doctor_prints_version():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "awiki-doctor.py")],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=REPO_ROOT, timeout=600)
    v = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert f"v{v}" in res.stdout, "doctor must surface the brain version"


def test_doctor_version_line_is_first_class():
    """The version is identity, not noise: it prints before sections."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "awiki-doctor.py")],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=REPO_ROOT, timeout=600)
    v = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    idx_ver = res.stdout.find(f"v{v}")
    idx_section = res.stdout.find("registry")
    assert 0 <= idx_ver < idx_section
