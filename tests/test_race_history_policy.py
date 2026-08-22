"""N-P1-001 resolution (Phase 8) — race-history retention policy.

Decision (2026-08-22, Phase-8 eval/promotion redesign): race history is
ARTIFACT/RUNTIME TELEMETRY ONLY. It is never copied into the tracked
`evals/subagents/races/` history by the promotion job, and promotion
wording must not claim it promotes race history.
Rationale: unbounded daily snapshots bloat the tracked repo; artifacts
retain 90 days of evidence; a future explicit-snapshot promotion can be
added deliberately if ever needed.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "subagent-eval.yml"


def test_promote_job_never_copies_race_history_into_tracked_tree():
    text = WORKFLOW.read_text(encoding="utf-8")
    promote = text.split("  promote:")[1]  # the promote job half
    assert "races-history" not in promote, (
        "policy violation: promote job references races-history (N-P1-001: "
        "race history stays artifact telemetry)")


def test_promotion_wording_matches_policy():
    """Wordings must say results+policy only — no claimed race-history
    promotion (the drift N-P1-001 flagged)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "results + races + recommended model swaps" not in text
    assert "race history, and guardrailed" not in text
    assert "PR-gated: results + recommended model swaps" in text
    assert "races = artifact telemetry only" in text, (
        "policy rationale must be stated at the staging site")
