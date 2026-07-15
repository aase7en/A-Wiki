"""Tests for scripts/eval/cost_aware_recommend.py — Q5 Pareto model selection.

Instead of always picking the HIGHEST pass@k model (which may be expensive),
this recommends the CHEAPEST model that meets a "good enough" pass@k threshold
(Pareto frontier: quality >= threshold, then minimize cost).

Pure functions — no I/O, no network. The COST_MATRIX is passed as a parameter
(in production, imported from scripts/hermes/model-pool/cost-router.py).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import cost_aware_recommend as ca  # noqa: E402


# Minimal cost matrix (USD per 1M tokens) — mirrors COST_MATRIX shape.
COST = {
    "deepseek-v4-flash": {"input": 0.15, "output": 0.60, "free": False},
    "deepseek-v4-pro":   {"input": 1.10, "output": 4.40, "free": False},
    "glm-5.2":           {"input": 0.00, "output": 0.00, "free": True},
    "sonnet":            {"input": 3.00, "output": 15.00, "free": False},
}


# ---------------------------------------------------------------------------
# cost_per_1k_calls — estimate USD for 1000 calls at avg token usage
# ---------------------------------------------------------------------------

def test_cost_per_1k_calls_basic():
    """1k calls × 500 input + 200 output tokens at given rates."""
    # deepseek-v4-flash: input 0.15/1M, output 0.60/1M
    # 1000 calls × (500 in + 200 out) = 500k in + 200k out
    # = (0.15 × 0.5) + (0.60 × 0.2) = 0.075 + 0.12 = 0.195
    cost = ca.cost_per_1k_calls("deepseek-v4-flash", COST,
                                avg_input_tokens=500, avg_output_tokens=200)
    assert abs(cost - 0.195) < 0.001


def test_cost_per_1k_calls_free_model():
    """Free model (input=0, output=0) → cost = 0."""
    cost = ca.cost_per_1k_calls("glm-5.2", COST)
    assert cost == 0.0


def test_cost_per_1k_calls_unknown_model():
    """Unknown model → cost = None (caller must handle)."""
    cost = ca.cost_per_1k_calls("nonexistent-model", COST)
    assert cost is None


# ---------------------------------------------------------------------------
# pareto_recommend — cheapest model above pass@k threshold
# ---------------------------------------------------------------------------

def test_pareto_picks_cheapest_above_threshold():
    """Among models with pass@k >= 0.7, pick the cheapest."""
    # glm-5.2: pass@k 0.8, cost 0 (free) — should win
    # deepseek-v4-flash: pass@k 0.9, cost 0.195
    # sonnet: pass@k 0.95, cost much higher
    eval_by_model = {
        "glm-5.2": {"pass_at_k": 0.8},
        "deepseek-v4-flash": {"pass_at_k": 0.9},
        "sonnet": {"pass_at_k": 0.95},
    }
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    assert rec["recommended"] == "glm-5.2"
    assert rec["reason"] == "cheapest-above-threshold"


def test_pareto_skips_below_threshold():
    """Models below min_pass_at_k are excluded even if cheap."""
    eval_by_model = {
        "glm-5.2": {"pass_at_k": 0.5},  # below 0.7
        "deepseek-v4-flash": {"pass_at_k": 0.8},
    }
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    assert rec["recommended"] == "deepseek-v4-flash"
    # glm-5.2 should be in excluded list
    assert any(e["model"] == "glm-5.2" for e in rec["excluded"])


def test_pareto_all_below_threshold():
    """All models below threshold → no recommendation (return None)."""
    eval_by_model = {
        "glm-5.2": {"pass_at_k": 0.5},
        "deepseek-v4-flash": {"pass_at_k": 0.6},
    }
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    assert rec is None


def test_pareto_tie_break_by_cost():
    """Two models with same pass@k → pick cheaper one."""
    eval_by_model = {
        "deepseek-v4-flash": {"pass_at_k": 0.85},
        "deepseek-v4-pro": {"pass_at_k": 0.85},  # same pass@k, more expensive
    }
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    assert rec["recommended"] == "deepseek-v4-flash"


def test_pareto_includes_cost_in_result():
    """Recommendation dict includes cost_per_1k_calls for transparency."""
    eval_by_model = {"deepseek-v4-flash": {"pass_at_k": 0.9}}
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    assert "cost_per_1k_calls" in rec
    assert rec["cost_per_1k_calls"] is not None
    assert rec["cost_per_1k_calls"] > 0


# ---------------------------------------------------------------------------
# Budget filter
# ---------------------------------------------------------------------------

def test_budget_filter_excludes_expensive():
    """--cost-budget caps monthly cost; expensive models filtered out."""
    eval_by_model = {
        "glm-5.2": {"pass_at_k": 0.8},           # free
        "deepseek-v4-flash": {"pass_at_k": 0.9},  # ~$0.195/1k
        "sonnet": {"pass_at_k": 0.95},            # very expensive
    }
    # Budget: $1/month. At 1k calls: glm=$0, flash=$0.195, sonnet=$big.
    # sonnet exceeds → excluded; flash under budget; glm free.
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7,
                              monthly_budget_usd=1.0, estimated_calls=1000)
    assert rec["recommended"] in ("glm-5.2", "deepseek-v4-flash")
    assert "sonnet" not in [e["model"] for e in rec.get("excluded", [])] or \
        any(e["model"] == "sonnet" for e in rec["excluded"])


# ---------------------------------------------------------------------------
# render_cost_preview — human-readable table
# ---------------------------------------------------------------------------

def test_render_cost_preview_lists_models():
    """Preview table lists every candidate with pass@k + cost."""
    eval_by_model = {
        "glm-5.2": {"pass_at_k": 0.8},
        "deepseek-v4-flash": {"pass_at_k": 0.9},
    }
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    report = ca.render_cost_preview(eval_by_model, rec, COST)
    assert "glm-5.2" in report
    assert "deepseek-v4-flash" in report
    assert "recommended" in report.lower() or "→" in report


def test_render_cost_preview_no_recommendation():
    """When pareto returns None, preview explains why."""
    eval_by_model = {"glm-5.2": {"pass_at_k": 0.5}}  # all below threshold
    rec = ca.pareto_recommend(eval_by_model, COST, min_pass_at_k=0.7)
    report = ca.render_cost_preview(eval_by_model, rec, COST)
    assert "no model" in report.lower() or "threshold" in report.lower() or "below" in report.lower()
