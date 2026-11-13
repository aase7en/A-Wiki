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
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The historically-polluting TEST TARGETS (terra r3 precision): the whole
# skills_service file (registry drift vector) and the MCP-button class that
# presses wiki_regen_index for real (18-file generator vector). The full
# user_journey file is NOT run here because its FTS assertions need
# .wiki-index.db — a gitignored artifact that exists in CI (built by the
# workflow) and in dev clones, but never in a fresh worktree.
OFFENDERS = [
    "tests/test_skills_service.py",
    "tests/test_user_journey_e2e.py::TestJourney2bMcpButtons",
]


def test_known_offenders_leave_fresh_worktree_clean(tmp_path):
    wt = tmp_path / "wt"
    add = subprocess.run(
        ["git", "worktree", "add", "--detach", str(wt), "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    assert add.returncode == 0, f"worktree add failed: {add.stderr}"
    cleanup_ok = True
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
        # terra r2 F4 + r3 F2: cleanup failure must be VISIBLE — if the
        # worktree or its registration survives every fallback, fail
        rm = subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
        if rm.returncode != 0:
            # terra r4 F2: remove the directory FIRST, then prune so the
            # registration of a vanished directory is cleared, then verify
            # the registration is really gone from git's own list
            shutil.rmtree(wt, ignore_errors=True)
            subprocess.run(["git", "worktree", "prune"], cwd=REPO_ROOT,
                           capture_output=True, timeout=120)
        listing = subprocess.run(
            ["git", "worktree", "list", "--porcelain"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=120)
        # terra r5 F1: a failed listing with empty stdout would false-pass;
        # compare structured entry lines, not substrings
        if listing.returncode != 0:
            cleanup_ok = False
        else:
            registered = {line[len("worktree "):].strip()
                          for line in listing.stdout.splitlines()
                          if line.startswith("worktree ")}
            cleanup_ok = (not wt.exists()) and (str(wt) not in registered)
    assert cleanup_ok, (
        "worktree cleanup failed — registration may linger: "
        f"{rm.stderr[:200] if rm.returncode != 0 else 'rmtree incomplete'}")


def test_guard_file_list_is_sorted_unique():
    assert OFFENDERS == sorted(set(OFFENDERS))
