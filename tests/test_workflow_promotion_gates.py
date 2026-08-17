"""Workflow promotion-gate invariants (A-Wiki vNext Phase 1 / P1.2).

Iron Law #1: failing tests written FIRST.

DISC/baseline context: `agent-model-scan.yml` used to run `--apply` on the
weekly schedule and push commits straight to `main` ("feat(agents):
auto-scan model swap"). Master plan §21 requires Discover → Candidate →
Proposal → explicit Promotion; a scheduled bot must never mutate main.

These tests pin the yaml contract:
  - `--apply` is reachable ONLY via explicit workflow_dispatch input
  - scheduled path defaults to --dry-run (candidate report)
  - no bare `git push` (which would push the checked-out main branch)
  - changes land on a `promotion/…` branch through a PR (the gate)
  - PR permission is declared
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WF = REPO_ROOT / ".github" / "workflows" / "agent-model-scan.yml"


def _text() -> str:
    return WF.read_text(encoding="utf-8")


def test_apply_is_gated_behind_explicit_dispatch_input():
    t = _text()
    assert "inputs.apply_swaps" in t, "--apply must be gated behind an explicit dispatch input"
    assert 'MODE="--dry-run"' in t, "default scan mode must be dry-run"


def test_no_bare_git_push_that_would_hit_main():
    t = _text()
    assert not re.search(r"^\s*git push\s*$", t, re.M), (
        "bare `git push` pushes the checked-out main branch — push a named promotion branch instead"
    )


def test_changes_land_on_promotion_branch_via_pr():
    t = _text()
    assert "promotion/agent-model-swap-" in t
    assert 'git push origin "$BRANCH"' in t
    assert "gh pr create" in t


def test_pull_request_permission_declared():
    assert "pull-requests: write" in _text()
