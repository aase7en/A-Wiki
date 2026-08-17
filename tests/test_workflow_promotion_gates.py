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


# ---------------------------------------------------------------------------
# P1.3 — model-pool telemetry must not be committed to git (runtime cache only)
# ---------------------------------------------------------------------------
POOL_WF = REPO_ROOT / ".github" / "workflows" / "model-pool-scout.yml"
POOL_JSON = "scripts/hermes/model-pool/model-pool.json"


def test_model_pool_scout_reports_without_auto_commit():
    t = POOL_WF.read_text(encoding="utf-8")
    assert "schedule:" in t, "6h scan cadence must be preserved"
    assert "actions/upload-artifact@v4" in t, "scan results must remain available as artifact"
    assert "git commit" not in t, "runtime telemetry must not be committed (P1.3)"
    assert "git push" not in t


def test_model_pool_scout_has_no_write_permission():
    t = POOL_WF.read_text(encoding="utf-8")
    assert "contents: write" not in t


def test_model_pool_json_is_runtime_cache_not_tracked():
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "--", POOL_JSON], cwd=REPO_ROOT,
        capture_output=True, text=True,
    )
    assert tracked.stdout.strip() == "", f"{POOL_JSON} must be untracked runtime cache"


def test_model_pool_json_is_gitignored():
    import subprocess

    ign = subprocess.run(
        ["git", "check-ignore", "-q", POOL_JSON], cwd=REPO_ROOT,
    )
    assert ign.returncode == 0, f"{POOL_JSON} must be listed in .gitignore"


# ---------------------------------------------------------------------------
# P1.4 — retired workflows (fail-open health + duplicate Pages deploy)
# Reference inspection 2026-08-17: both files referenced only by migration
# docs (descriptive); nothing pushes gh-pages; wiki-health-digest tests
# target a different workflow; duties covered by wiki-health.yml + ci.yml
# (freshness) + pages-deploy.yml (Pages).
# ---------------------------------------------------------------------------
def test_daily_maintenance_workflow_retired():
    assert not (REPO_ROOT / ".github" / "workflows" / "daily-maintenance.yml").exists(), (
        "fail-open health check + auto-commit main retired per master plan §6"
    )


def test_duplicate_pages_deploy_workflow_retired():
    assert not (REPO_ROOT / ".github" / "workflows" / "deploy-awiki-live.yml").exists(), (
        "duplicate of pages-deploy.yml (which already stages a minimal _site payload)"
    )
