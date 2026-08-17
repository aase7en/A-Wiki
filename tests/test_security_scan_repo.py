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


def _make_baseline(repo_root: Path, findings_out: list) -> Path:
    """Write a baseline covering exactly the findings returned (R-P2-003 keys).

    Uses the module's REAL pattern set (sr.PATTERNS) so keys match what the
    CLI subprocess generates from security_patterns.yaml.
    """
    findings = sr.scan_repo(repo_root, sr.PATTERNS, sr.PLACEHOLDERS, excludes=[])
    findings_out.extend(findings)
    b = repo_root / "baseline.txt"
    b.write_text(chr(10).join(f.baseline_key() for f in findings), encoding="utf-8")
    return b


def test_cli_baseline_ratchet_allows_known_and_fails_new(tmp_path):
    legacy_token = "ghp_" + "A1" + "0123456789abcdef" * 2  # 34 chars — matches real gh pattern
    _init_repo_with_file(tmp_path, "legacy.py", f"old {legacy_token} debt")
    found: list = []
    baseline = _make_baseline(tmp_path, found)
    assert len(found) == 1

    first = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert first.returncode == 1
    second = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--baseline", str(baseline), "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert second.returncode == 0, "baseline findings must pass: " + second.stdout[:300]


def test_ratchet_different_same_pattern_finding_fails(tmp_path):
    """R-P2-003 #2: a NEW different token with the same pattern+file must fail."""
    tok_a = "ghp_" + "A1" + "0123456789abcdef" * 2
    _init_repo_with_file(tmp_path, "legacy.py", f"old {tok_a} debt")
    found: list = []
    baseline = _make_baseline(tmp_path, found)

    tok_b = "ghp_" + "E9" + "fedcba9876543210" * 2  # same pattern, different value
    (tmp_path / "legacy.py").write_text(
        (tmp_path / "legacy.py").read_text(encoding="utf-8") + chr(10) + "more " + tok_b + chr(10),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--baseline", str(baseline), "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 1, "different same-pattern finding was suppressed by a coarse key"


def test_ratchet_extra_identical_occurrence_fails(tmp_path):
    """R-P2-003 #3: exceeding the baselined occurrence COUNT must fail."""
    tok = "ghp_" + "F4" + "0123456789abcdef" * 2
    _init_repo_with_file(tmp_path, "legacy.py", f"a {tok}")
    found: list = []
    baseline = _make_baseline(tmp_path, found)
    assert len(found) == 1

    (tmp_path / "legacy.py").write_text(
        "a " + tok + chr(10) + "b " + tok + chr(10), encoding="utf-8"  # 2 identical occurrences
    )
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "security" / "scan_repo.py"),
         "--ci", "--baseline", str(baseline), "--repo-root", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 1, "extra identical occurrence beyond baseline count was suppressed"


def test_baseline_contains_no_raw_secret(tmp_path):
    """R-P2-003 #4: baseline files must never hold raw matched values."""
    tok = "ghp_" + "B5" + "0123456789abcdef" * 2
    _init_repo_with_file(tmp_path, "legacy.py", f"x {tok} y")
    found: list = []
    baseline = _make_baseline(tmp_path, found)
    text = baseline.read_text(encoding="utf-8")
    assert tok not in text, "raw secret leaked into baseline"
    assert found[0].match == tok  # sanity: the finding itself did match


# ---------------------------------------------------------------------------
# R-P2-002 — no silent byte cap: the WHOLE file must be scanned
# ---------------------------------------------------------------------------
def test_secret_beyond_256kib_is_detected(tmp_path):
    """A planted secret after the former 256 KiB single-read cap must fail."""
    token = "ghp_" + "C7" + "0123456789abcdef" * 2  # 34 chars — real gh pattern
    filler = "#" + "x" * 78 + "\n"                  # ~80-byte comment lines
    big = tmp_path / "big.py"
    big.write_text(filler * 4000, encoding="utf-8")  # ~320 KiB of filler
    with big.open("a", encoding="utf-8") as f:
        f.write(f"k = '{token}'\n")
    assert big.stat().st_size > 262_144
    hits = sr.scan_file(big, PATTERNS, PLACEHOLDERS)
    assert any(h[1] == "test token" for h in hits), "secret beyond 256 KiB was invisible"
    assert hits[-1][0] == 4001, "line number must survive full-file scanning"


def test_secret_inside_multikib_single_line_is_detected(tmp_path):
    """Boundary case: a >300 KiB single line with the token at its end."""
    token = "ghp_" + "D8" + "0123456789abcdef" * 2
    huge_line = "y" * (300 * 1024) + " " + token + "\n"
    f1 = tmp_path / "longline.txt"
    f1.write_text(huge_line, encoding="utf-8")
    hits = sr.scan_file(f1, PATTERNS, PLACEHOLDERS)
    assert any(h[1] == "test token" for h in hits), "token near the old chunk boundary escaped"


def test_scan_repo_full_coverage_no_chunk_constant(tmp_path):
    """CHUNK_BYTES-style single-read caps must not exist in the scanner."""
    import inspect
    src = inspect.getsource(sr)
    assert "CHUNK_BYTES" not in src, "silent byte cap reintroduced"
