"""WO-AWIKI-HYGIENE-07 — repo-pollution guard.

Known offenders (tests that historically wrote real generated surfaces into
the checkout during a full-suite run) are executed in a FRESH git worktree;
the worktree must end `git status --porcelain`-clean. This guards the whole
class of pollution: any test that regenerates wiki surfaces or rewrites
tracked files without byte-exact restore will fail here.

Root causes fixed alongside (see docs/work-orders/WO-AWIKI-HYGIENE-07):
1. test_skills_service.py — registry "restore" re-dumped JSON (bytes drift)
2. test_user_journey_e2e.py — MCP button wiki_regen_index runs gen-index.py
   for real with cwd=REPO_ROOT (18 generated files)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The two historically-polluting files; run together to also catch ordering
# interactions between them.
OFFENDERS = [
    "tests/test_skills_service.py",
    "tests/test_user_journey_e2e.py",
]


def test_known_offenders_leave_fresh_worktree_clean(tmp_path):
    wt = tmp_path / "wt"
    add = subprocess.run(
        ["git", "worktree", "add", "--detach", str(wt), "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    assert add.returncode == 0, f"worktree add failed: {add.stderr}"
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = ""
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *OFFENDERS, "-q", "--no-header"],
            cwd=wt, capture_output=True, text=True, timeout=900, env=env)
        # terra r1 F2: offenders must PASS outright in a fresh worktree —
        # accepting rc=1 would green-light failures that never reach the
        # pollution vector (false-green guard).
        assert proc.returncode == 0, (
            f"offenders failed in fresh worktree (rc={proc.returncode}):\n"
            f"{proc.stdout[-600:]}\n{proc.stderr[-400:]}")
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=wt, capture_output=True, text=True, timeout=120)
        assert status.returncode == 0, "git status failed in worktree"
        assert status.stdout.strip() == "", (
            "known offenders left the worktree dirty — repo pollution "
            f"regression:\n{status.stdout}")
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt)],
            cwd=REPO_ROOT, capture_output=True, timeout=120)


def test_guard_file_list_is_sorted_unique():
    assert OFFENDERS == sorted(set(OFFENDERS))
