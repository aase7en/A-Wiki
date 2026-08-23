"""Slice F: awiki doctor + guide."""
from __future__ import annotations

import importlib.util as ilu
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_doctor_runs_and_reports_sections():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "awiki-doctor.py")],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=REPO_ROOT, timeout=600)
    out = res.stdout
    for sec in ("registry", "hooks", "mcp", "specs", "privacy"):
        assert sec in out, f"doctor missing section {sec}"
    assert "brain healthy" in out or "attention" in out
    # on a healthy checkout this must be green end-to-end
    assert res.returncode == 0, out[-400:]


def test_guide_topics():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "awiki-guide.py")],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=REPO_ROOT, timeout=60)
    assert "30 วินาที" in res.stdout and "/A" in res.stdout
    for topic, marker in (("install", "pip install"),
                          ("skills", "awiki skill list"),
                          ("adopt", "awiki adopt")):
        r2 = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "awiki-guide.py"), topic],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=REPO_ROOT, timeout=60)
        assert r2.returncode == 0 and marker in r2.stdout
