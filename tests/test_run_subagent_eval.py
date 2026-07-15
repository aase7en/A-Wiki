"""Tests for the Subagent Eval Harness runner (run_subagent_eval.py).

Verifies suite loading, case matching, pass@k computation, and the dry-run
path (which must NOT make any API calls). The runner's real-model path
(--apply) is exercised only by the user later; these tests cover the
deterministic, offline pieces.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import run_subagent_eval as ev  # noqa: E402


# ---------------------------------------------------------------------------
# Suite loading
# ---------------------------------------------------------------------------

def test_load_suite_parses_json(tmp_path):
    """load_suite reads a JSON eval file and returns the parsed dict."""
    suite = {
        "suite": "test-domain",
        "description": "test",
        "cases": [
            {"id": "c1", "subagent": "x", "prompt": "say hi",
             "required": ["hi"], "forbidden": ["bye"]},
        ],
    }
    p = tmp_path / "test-domain.json"
    p.write_text(json.dumps(suite))
    loaded = ev.load_suite(p)
    assert loaded["suite"] == "test-domain"
    assert len(loaded["cases"]) == 1
    assert loaded["cases"][0]["id"] == "c1"


def test_load_suite_missing_returns_none(tmp_path):
    """A non-existent path returns None (not a crash)."""
    assert ev.load_suite(tmp_path / "nope.json") is None


# ---------------------------------------------------------------------------
# Case judging (required/forbidden keyword matching)
# ---------------------------------------------------------------------------

def test_judge_pass_when_all_required_present():
    case = {"required": ["PubMed", "citation"], "forbidden": []}
    assert ev.judge(case, "Found in PubMed with citation [1]") is True


def test_judge_fail_when_required_missing():
    case = {"required": ["PubMed"], "forbidden": []}
    assert ev.judge(case, "I searched Google") is False


def test_judge_fail_when_forbidden_present():
    case = {"required": ["ok"], "forbidden": ["I don't know"]}
    assert ev.judge(case, "ok but I don't know the answer") is False


def test_judge_case_insensitive():
    case = {"required": ["PASSRATE"], "forbidden": ["error"]}
    assert ev.judge(case, "the passrate is high") is True


# ---------------------------------------------------------------------------
# pass@k computation
# ---------------------------------------------------------------------------

def test_pass_at_k_all_pass():
    """k=3, all 3 results pass → pass@3 = 1.0."""
    results = [{"pass": True}, {"pass": True}, {"pass": True}]
    assert ev.pass_at_k(results, k=3) == 1.0


def test_pass_at_k_some_fail():
    """k=3, 2 pass + 1 fail → pass@3 = 1.0 (at least one pass in any k)."""
    results = [{"pass": True}, {"pass": False}, {"pass": True}]
    # pass@k = 1 - C(fail, k)/C(total, k); with 1 fail out of 3, k=3 → 1.0
    assert ev.pass_at_k(results, k=3) == 1.0


def test_pass_at_k_all_fail():
    """k=3, all fail → pass@3 = 0.0."""
    results = [{"pass": False}, {"pass": False}, {"pass": False}]
    assert ev.pass_at_k(results, k=3) == 0.0


def test_pass_at_k_empty():
    assert ev.pass_at_k([], k=3) == 0.0


# ---------------------------------------------------------------------------
# Dry-run plan (must NOT make API calls)
# ---------------------------------------------------------------------------

def test_dry_run_emits_plan_without_api(tmp_path, capsys, monkeypatch):
    """--dry-run prints the plan (suite + case count) and makes zero delegate calls."""
    suite = {
        "suite": "medical",
        "description": "medical eval",
        "cases": [
            {"id": "m1", "subagent": "medical-lit-reviewer",
             "prompt": "summarize drug X", "required": ["drug"], "forbidden": []},
            {"id": "m2", "subagent": "clinical-reasoner",
             "prompt": "ddx for fever", "required": ["fever"], "forbidden": []},
        ],
    }
    suite_path = tmp_path / "medical.json"
    suite_path.write_text(json.dumps(suite))

    # Track whether any API call would happen — patch the delegate fn.
    called = {"n": 0}

    def fake_delegate(model, prompt):
        called["n"] += 1
        return "FAKE RESPONSE"

    monkeypatch.setattr(ev, "delegate_to_model", fake_delegate)

    plan = ev.build_plan(suite_paths=[suite_path], models=["deepseek-v4-flash"], k=1, dry_run=True)
    assert plan["total_cases"] == 2
    assert plan["models"] == ["deepseek-v4-flash"]
    assert plan["dry_run"] is True
    assert plan["estimated_calls"] == 0  # dry-run → no API calls
    assert called["n"] == 0  # delegate was never invoked


def test_apply_plan_estimates_api_calls(tmp_path):
    """Non-dry-run plan estimates the API call count (cases × models × k)."""
    suite = {
        "suite": "finance",
        "cases": [
            {"id": "f1", "subagent": "finance-analyst", "prompt": "analyze AAPL",
             "required": ["AAPL"], "forbidden": []},
        ],
    }
    p = tmp_path / "finance.json"
    p.write_text(json.dumps(suite))
    plan = ev.build_plan(suite_paths=[p], models=["deepseek-v4-flash", "glm-5.2"], k=3, dry_run=False)
    # 1 case × 2 models × 3 samples = 6 calls
    assert plan["estimated_calls"] == 6
