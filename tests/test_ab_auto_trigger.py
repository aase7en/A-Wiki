"""Tests for scripts/lib/ab_auto_trigger.py — auto A/B experiment from task patterns.

Iron Law #1: failing tests written FIRST.

ab_auto_trigger คือ bridge ระหว่าง task_board (Neural Spine) กับ ab_routing
(R4) ที่มีอยู่แล้ว. เมื่อ:
  - มี task ที่ทำซ้ำๆ (เช่น 'review PR', 'summarize doc') ≥ N ครั้ง
  - และยังไม่มี A/B experiment สำหรับ task type นี้
→ propose experiment (draft config entry, write to .tmp/ab-proposals.jsonl)
→ user ยืนยัน → activate via ab_rotator

Reuse 100%: ab_routing.load_experiments + ab_routing.advance_experiment
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import ab_auto_trigger as ab  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. classify_task_pattern — group tasks by goal keyword
# ---------------------------------------------------------------------------
def test_classify_groups_similar_tasks(tmp_path):
    """Tasks with similar goals → grouped into a pattern."""
    import task_board
    board = task_board.TaskBoard(tmp_path / "tasks.json")
    for kw in ["review", "review", "review", "summarize", "summarize"]:
        board.add(goal=f"{kw} something")
    patterns = ab.classify_task_patterns(tmp_path / "tasks.json", min_count=2)
    # 'review' (3x) + 'summarize' (2x) → 2 patterns
    assert any(p["keyword"] == "review" and p["count"] == 3 for p in patterns)
    assert any(p["keyword"] == "summarize" and p["count"] == 2 for p in patterns)


def test_classify_ignores_rare_tasks(tmp_path):
    import task_board
    board = task_board.TaskBoard(tmp_path / "tasks.json")
    board.add(goal="unique one-off task")
    board.add(goal="another unique")
    patterns = ab.classify_task_patterns(tmp_path / "tasks.json", min_count=3)
    assert patterns == []


def test_classify_empty_when_no_board(tmp_path):
    assert ab.classify_task_patterns(tmp_path / "missing.json", min_count=2) == []


# ---------------------------------------------------------------------------
# 2. has_experiment — check if ab-experiments.json already covers a keyword
# ---------------------------------------------------------------------------
def test_has_experiment_true_when_keyword_present(tmp_path):
    """If config has 'review' subagent → 'review' keyword is covered."""
    config = {
        "experiments": [
            {"subagent": "code-reviewer", "champion": "x", "challenger": "y",
             "active": True}
        ]
    }
    cfg_path = tmp_path / "ab.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    assert ab.has_experiment("code-reviewer", cfg_path) is True


def test_has_experiment_false_when_keyword_absent(tmp_path):
    config = {"experiments": [{"subagent": "other", "champion": "x",
                                "challenger": "y", "active": True}]}
    cfg_path = tmp_path / "ab.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    assert ab.has_experiment("summarize", cfg_path) is False


def test_has_experiment_false_when_config_missing(tmp_path):
    assert ab.has_experiment("x", tmp_path / "missing.json") is False


# ---------------------------------------------------------------------------
# 3. propose_experiment — draft experiment entry for a repeated pattern
# ---------------------------------------------------------------------------
def test_propose_returns_dict_with_required_fields():
    proposal = ab.propose_experiment(
        keyword="review", count=5,
        sample_goals=["review PR #1", "review PR #2"],
    )
    assert isinstance(proposal, dict)
    for field in ("subagent", "champion", "challenger", "active",
                  "phase_size", "total_phases", "reason"):
        assert field in proposal, f"missing {field}"


def test_propose_inactive_by_default():
    """Proposals must default to active=False (user must explicitly enable)."""
    proposal = ab.propose_experiment(keyword="review", count=5, sample_goals=["x"])
    assert proposal["active"] is False


def test_propose_includes_evidence_in_reason():
    proposal = ab.propose_experiment(
        keyword="review", count=10, sample_goals=["review PR #1", "review PR #2"])
    assert "10" in proposal["reason"]
    assert "review" in proposal["reason"].lower()


# ---------------------------------------------------------------------------
# 4. write_proposal_to_ledger — record proposal as idea entry
# ---------------------------------------------------------------------------
def test_write_proposal_to_ledger(tmp_path):
    """Proposal should be written to ledger as type=idea tagged 'ab-proposal'."""
    import memory_ledger
    ledger_path = tmp_path / "ledger.jsonl"
    proposal = ab.propose_experiment(keyword="review", count=5, sample_goals=["x"])
    ab.write_proposal_to_ledger(ledger_path, proposal)
    entries = memory_ledger.MemoryLedger(ledger_path)._load_all()
    ideas = [e for e in entries if e.get("type") == "idea"
             and "ab-proposal" in e.get("tags", [])]
    assert len(ideas) == 1
    assert "review" in ideas[0]["summary"].lower()


# ---------------------------------------------------------------------------
# 5. scan_and_propose — end-to-end: tasks → patterns → proposals
# ---------------------------------------------------------------------------
def test_scan_and_propose_creates_proposals(tmp_path):
    """Repeated tasks without existing experiment → proposal drafted."""
    import task_board
    board = task_board.TaskBoard(tmp_path / "tasks.json")
    for i in range(5):
        board.add(goal=f"review PR #{i}")
    ledger_path = tmp_path / "ledger.jsonl"
    config_path = tmp_path / "ab.json"
    config_path.write_text(json.dumps({"experiments": []}), encoding="utf-8")

    n = ab.scan_and_propose(
        tasks_path=tmp_path / "tasks.json",
        ledger_path=ledger_path,
        config_path=config_path,
        min_count=3,
    )
    assert n >= 1


def test_scan_and_propose_skips_when_experiment_exists(tmp_path):
    """If ab-experiments.json already has 'review' → don't re-propose."""
    import task_board
    board = task_board.TaskBoard(tmp_path / "tasks.json")
    for i in range(5):
        board.add(goal=f"review PR #{i}")
    config = {"experiments": [
        {"subagent": "review", "champion": "x", "challenger": "y", "active": True}
    ]}
    config_path = tmp_path / "ab.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    n = ab.scan_and_propose(
        tasks_path=tmp_path / "tasks.json",
        ledger_path=tmp_path / "ledger.jsonl",
        config_path=config_path,
        min_count=3,
    )
    assert n == 0, "should skip when experiment already exists"
