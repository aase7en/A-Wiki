"""stop-auto-commit must gate pushes to main (continuity-gate rule #3).

Incident 2026-08-20: the Stop hook auto-committed generated noise with
leftover conflict markers and pushed straight to main — main's security
scan went red and every PR merging main inherited the failure. Owner of
that push was never identified.

Contract:
  - the hook runs the repo security scan (--ci --baseline) on the staged
    tree BEFORE any push to main; a failing/missing scan means NO push
  - pure generated-noise changes are not pushed to main by the session
    hook (they belong on work branches that pass CI)
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _hook_text() -> str:
    return (REPO_ROOT / ".claude" / "hooks" / "stop-auto-commit.sh").read_text(encoding="utf-8")


def test_hook_runs_security_scan_before_push():
    t = _hook_text()
    scan = t.find("scan_repo.py")
    push = t.find("git push origin main")
    assert scan != -1, "hook must run scripts/security/scan_repo.py"
    assert push != -1
    assert scan < push, "scan must run BEFORE the push"


def test_hook_scan_is_ci_baseline_mode():
    t = _hook_text()
    assert "--ci" in t and "--baseline" in t, (
        "the gate must use the same --ci --baseline contract as CI")


def test_scan_failure_blocks_push():
    t = _hook_text()
    # the push must be inside the guarded path (after a successful gate),
    # not unconditional
    m = re.search(r"git push origin main", t)
    assert m
    before = t[: m.start()]
    assert "SCAN" in before and ("SCAN_OK" in t or "scan_ok" in t or "GATE" in t), (
        "push must be conditional on the scan result")


def test_generated_noise_not_pushed_to_main():
    t = _hook_text()
    assert "GENERATED_NOISE" in t, (
        "hook must refuse to push pure generated-noise changes to main "
        "(continuity-gate rule 3)")
