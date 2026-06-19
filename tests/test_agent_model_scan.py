"""Tests for the weekly agent-model benchmark scanner with safe auto-apply.

Iron Law #1: failing tests first. Covers cost-class boundaries, the
"auto-apply only within the same cost class" rule, dependency-free YAML
frontmatter model rewrites, candidate selection, and dry-run vs apply.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_PY = REPO_ROOT / "scripts" / "agents" / "agent_model_scan.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("agent_model_scan", SCAN_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scan():
    return _load_module()


POLICY = {
    "cost_classes": {
        "free": {"rank": 0},
        "cheap-paid": {"rank": 1},
        "premium-paid": {"rank": 2},
    },
    "apply_policy": {
        "auto_apply_within_same_cost_class": True,
        "tier_up_requires_confirmation": True,
        "min_capability_gain": 5,
    },
    "agents": {
        "code-reviewer": {
            "file": ".kilo/agents/code-reviewer.md",
            "current_model": "google/gemini-3.5-flash",
            "role_dimension": "swe_bench",
            "cost_class": "free",
            "candidate_families": ["gemini-flash", "llama", "qwen", "kimi"],
            "managed": True,
        },
        "architect": {
            "file": ".kilo/agents/architect.md",
            "current_model": "openrouter/anthropic/claude-opus-4.8",
            "role_dimension": "reasoning",
            "cost_class": "premium-paid",
            "candidate_families": ["claude", "glm", "deepseek"],
            "managed": True,
        },
    },
}

SCORECARD = {
    "neutral_default": 50,
    "families": {
        "gemini-flash": {"match": ["gemini"], "swe_bench": 34, "reasoning": 62},
        "llama": {"match": ["llama"], "swe_bench": 26, "reasoning": 52},
        "qwen": {"match": ["qwen"], "swe_bench": 40, "reasoning": 66},
        "kimi": {"match": ["kimi"], "swe_bench": 55, "reasoning": 70},
        "claude": {"match": ["claude"], "swe_bench": 60, "reasoning": 85},
        "glm": {"match": ["glm"], "swe_bench": 68, "reasoning": 80},
        "deepseek": {"match": ["deepseek"], "swe_bench": 50, "reasoning": 75},
    },
}


# --- cost class boundaries -------------------------------------------------

def test_cost_rank_orders_correctly(scan):
    assert scan.cost_rank(POLICY, "free") < scan.cost_rank(POLICY, "cheap-paid")
    assert scan.cost_rank(POLICY, "cheap-paid") < scan.cost_rank(POLICY, "premium-paid")


def test_safe_swap_same_class_is_allowed(scan):
    assert scan.is_safe_swap(POLICY, "free", "free") is True
    assert scan.is_safe_swap(POLICY, "premium-paid", "premium-paid") is True


def test_safe_swap_tier_up_is_blocked(scan):
    # tiering UP (more expensive) must never auto-apply
    assert scan.is_safe_swap(POLICY, "free", "premium-paid") is False
    assert scan.is_safe_swap(POLICY, "free", "cheap-paid") is False


def test_safe_swap_tier_down_is_allowed(scan):
    # moving DOWN a cost class (cheaper) is permitted (cost-first rewards it)
    assert scan.is_safe_swap(POLICY, "premium-paid", "free") is True


# --- capability scoring ----------------------------------------------------

def test_capability_matches_family(scan):
    assert scan.capability_for_model(SCORECARD, "google/gemini-3.5-flash", "swe_bench") == 34
    assert scan.capability_for_model(SCORECARD, "groq/qwen/qwen3-32b", "reasoning") == 66


def test_capability_unknown_family_uses_neutral_default(scan):
    assert scan.capability_for_model(SCORECARD, "weird/unknown-model", "swe_bench") == 50


# --- candidate selection ---------------------------------------------------

def test_pick_better_candidate_within_same_cost_class(scan):
    # code-reviewer is free, gemini swe_bench=34; kimi (free credit) swe_bench=55
    # kimi is in candidate_families and same cost class -> selected as better
    decision = scan.decide_agent(POLICY["agents"]["code-reviewer"], SCORECARD, POLICY)
    assert decision["action"] == "apply"
    assert decision["from"] == "google/gemini-3.5-flash"
    assert "kimi" in decision["to"]
    assert decision["gain"] >= POLICY["apply_policy"]["min_capability_gain"]


def test_no_candidate_when_current_already_best(scan):
    cfg = {
        "current_model": "google/gemini-3.5-flash",
        "role_dimension": "swe_bench",
        "cost_class": "free",
        "candidate_families": ["gemini-flash", "llama"],  # llama swe_bench=26 < 34
        "managed": True,
    }
    decision = scan.decide_agent(cfg, SCORECARD, POLICY)
    assert decision["action"] == "none"


def test_tier_up_becomes_propose_not_apply(scan):
    # architect is premium-paid; pretend a candidate would be cheaper+better.
    # A swap that changes cost class to a higher rank must be 'propose', not 'apply'.
    cfg = {
        "current_model": "google/gemini-3.5-flash",
        "role_dimension": "reasoning",
        "cost_class": "free",
        "candidate_families": ["claude"],  # claude reasoning=85 but premium-paid
        "managed": True,
    }
    decision = scan.decide_agent(cfg, SCORECARD, POLICY)
    assert decision["action"] == "propose"


def test_unmanaged_agent_never_applies(scan):
    cfg = dict(POLICY["agents"]["architect"])
    cfg["managed"] = False
    decision = scan.decide_agent(cfg, SCORECARD, POLICY)
    assert decision["action"] in ("propose", "none")
    assert decision["action"] != "apply"


# --- frontmatter rewrite ---------------------------------------------------

MD_SAMPLE = """---
mode: primary
description: Reviews code
options:
  displayName: Code Reviewer
  id: code-reviewer
model: google/gemini-3.5-flash
permission:
  edit: deny
---

You are a code reviewer.
"""


def test_rewrite_frontmatter_model_updates_value(scan):
    out = scan.rewrite_frontmatter_model(MD_SAMPLE, "groq/qwen/qwen3-32b")
    assert "model: groq/qwen/qwen3-32b" in out
    # body and other keys preserved
    assert "You are a code reviewer." in out
    assert "displayName: Code Reviewer" in out
    assert "model: google/gemini-3.5-flash" not in out


def test_rewrite_frontmatter_preserves_variant_and_structure(scan):
    md = MD_SAMPLE.replace(
        "model: google/gemini-3.5-flash\n",
        "model: google/gemini-3.5-flash\nvariant: max\n",
    )
    out = scan.rewrite_frontmatter_model(md, "groq/qwen/qwen3-32b")
    assert "variant: max" in out
    assert out.count("---") == 2


def test_rewrite_frontmatter_inserts_model_when_absent(scan):
    md = "---\nmode: primary\ndescription: x\n---\nbody\n"
    out = scan.rewrite_frontmatter_model(md, "google/gemini-3.5-flash")
    assert "model: google/gemini-3.5-flash" in out


# --- dry-run vs apply end to end ------------------------------------------

def _write_repo(tmp_path: Path) -> Path:
    agents = tmp_path / ".kilo" / "agents"
    agents.mkdir(parents=True)
    (agents / "code-reviewer.md").write_text(MD_SAMPLE, encoding="utf-8")
    return agents


def test_dry_run_does_not_modify_files(scan, tmp_path, monkeypatch):
    agents = _write_repo(tmp_path)
    before = (agents / "code-reviewer.md").read_text("utf-8")

    policy = json.loads(json.dumps(POLICY))
    policy["agents"]["code-reviewer"]["file"] = str(agents / "code-reviewer.md")
    monkeypatch.setattr(scan, "REPO_ROOT", tmp_path)

    report = scan.run_scan(policy, SCORECARD, apply_changes=False, repo_root=tmp_path)
    after = (agents / "code-reviewer.md").read_text("utf-8")
    assert after == before  # dry-run must not write
    # but it should still report the would-be apply
    applied = [d for d in report["decisions"] if d["action"] == "apply"]
    assert applied, "dry-run should surface intended applies"


def test_apply_writes_model_and_logs(scan, tmp_path, monkeypatch):
    agents = _write_repo(tmp_path)
    log_path = tmp_path / "scan-log.jsonl"

    policy = json.loads(json.dumps(POLICY))
    policy["agents"]["code-reviewer"]["file"] = str(agents / "code-reviewer.md")
    policy["apply_policy"]["revert_log"] = str(log_path)

    report = scan.run_scan(policy, SCORECARD, apply_changes=True, repo_root=tmp_path)
    after = (agents / "code-reviewer.md").read_text("utf-8")
    assert "model: " in after
    assert "google/gemini-3.5-flash" not in after  # changed to better candidate
    assert report["applied"] >= 1
    assert log_path.exists()
    # revert log must record from->to for revertibility
    first_line = json.loads(log_path.read_text("utf-8").splitlines()[0])
    assert first_line["from"] == "google/gemini-3.5-flash"
    assert "to" in first_line


def test_revert_restores_previous_model(scan, tmp_path, monkeypatch):
    agents = _write_repo(tmp_path)
    log_path = tmp_path / "scan-log.jsonl"

    policy = json.loads(json.dumps(POLICY))
    policy["agents"]["code-reviewer"]["file"] = str(agents / "code-reviewer.md")
    policy["apply_policy"]["revert_log"] = str(log_path)

    scan.run_scan(policy, SCORECARD, apply_changes=True, repo_root=tmp_path)
    scan.revert_last(policy, repo_root=tmp_path)
    restored = (agents / "code-reviewer.md").read_text("utf-8")
    assert "google/gemini-3.5-flash" in restored
