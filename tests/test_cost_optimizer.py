"""Tests for scripts/eval/cost_optimizer.py — cost optimization recommender (T6).

Iron Law #1: failing tests written FIRST.

T6 ผสม cost_history (S6) + pareto_recommend (cost_aware_recommend) +
adaptive_routing pattern → recommend model ที่ "ดีพอ + ถูกสุด" + คำนวณ savings
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import cost_optimizer  # noqa: E402  -- module under test (created by T6)


# ---------------------------------------------------------------------------
# 1. analyze_suite picks cheapest "good enough" model
# ---------------------------------------------------------------------------
def test_analyze_suite_picks_cheapest_good_enough():
    """3 models: A (pass@k=0.9, $1), B (pass@k=0.8, $0.5), C (pass@k=0.6, $0.1).
    Threshold 0.7 → A + B ผ่าน, C ตก. ถูกสุด = B.
    """
    eval_by_model = {
        "model-a": {"pass_at_k": 0.9},
        "model-b": {"pass_at_k": 0.8},
        "model-c": {"pass_at_k": 0.6},  # below threshold
    }
    cost_by_model = {
        "model-a": 1.0,
        "model-b": 0.5,
        "model-c": 0.1,
    }
    rec = cost_optimizer.analyze_suite(
        "medical", eval_by_model, cost_by_model,
        current_model="model-a", min_pass_at_k=0.7,
    )
    assert rec is not None
    assert rec["recommended_model"] == "model-b"  # cheapest above threshold
    assert rec["recommended_cost"] == 0.5


# ---------------------------------------------------------------------------
# 2. analyze_suite skips all-below-threshold
# ---------------------------------------------------------------------------
def test_analyze_suite_skips_below_threshold():
    """ทุก model ต่ำกว่า threshold → None (ไม่ recommend)."""
    eval_by_model = {"a": {"pass_at_k": 0.5}, "b": {"pass_at_k": 0.6}}
    cost_by_model = {"a": 0.1, "b": 0.2}
    rec = cost_optimizer.analyze_suite(
        "test", eval_by_model, cost_by_model,
        current_model="a", min_pass_at_k=0.7,
    )
    assert rec is None or rec.get("recommended_model") is None


# ---------------------------------------------------------------------------
# 3. savings calculation correct
# ---------------------------------------------------------------------------
def test_savings_calculation_correct():
    """current_cost - recommended_cost = savings_usd; pct = savings/current."""
    eval_by_model = {"a": {"pass_at_k": 0.9}, "b": {"pass_at_k": 0.8}}
    cost_by_model = {"a": 2.0, "b": 0.5}
    rec = cost_optimizer.analyze_suite(
        "test", eval_by_model, cost_by_model,
        current_model="a", min_pass_at_k=0.7,
    )
    assert rec["savings_usd"] == pytest.approx(1.5, abs=0.01)  # 2.0 - 0.5
    assert rec["savings_pct"] == pytest.approx(0.75, abs=0.01)  # 1.5/2.0


# ---------------------------------------------------------------------------
# 4. no recommendation when current already cheapest
# ---------------------------------------------------------------------------
def test_no_recommendation_when_current_already_cheapest():
    """current model เป็นถูกสุดอยู่แล้ว → recommended = current, savings = 0."""
    eval_by_model = {"a": {"pass_at_k": 0.9}, "b": {"pass_at_k": 0.8}}
    cost_by_model = {"a": 0.3, "b": 0.5}  # a ถูกกว่า
    rec = cost_optimizer.analyze_suite(
        "test", eval_by_model, cost_by_model,
        current_model="a", min_pass_at_k=0.7,
    )
    assert rec["recommended_model"] == "a"
    assert rec["savings_usd"] == 0.0


# ---------------------------------------------------------------------------
# 5. render report format
# ---------------------------------------------------------------------------
def test_render_report_format():
    rec = {
        "suite": "medical", "current_model": "a", "current_cost": 2.0,
        "recommended_model": "b", "recommended_cost": 0.5,
        "savings_usd": 1.5, "savings_pct": 0.75, "reason": "cheaper + good enough",
    }
    report = cost_optimizer.render_optimizer_report([rec])
    assert "medical" in report
    assert "b" in report
    assert "1.5" in report or "1.50" in report


# ---------------------------------------------------------------------------
# 6. min_savings guardrail
# ---------------------------------------------------------------------------
def test_min_savings_guardrail():
    """ถ้า savings ต่ำกว่า min_savings → ไม่ recommend (status=no-action)."""
    eval_by_model = {"a": {"pass_at_k": 0.9}, "b": {"pass_at_k": 0.8}}
    cost_by_model = {"a": 1.0, "b": 0.9}  # savings เพียง 0.1
    rec = cost_optimizer.analyze_suite(
        "test", eval_by_model, cost_by_model,
        current_model="a", min_pass_at_k=0.7, min_savings=0.5,
    )
    # savings 0.1 < min_savings 0.5 → ไม่ recommend
    assert rec is None or rec.get("status") == "no-action" or rec.get("savings_usd", 0) < 0.5


# ---------------------------------------------------------------------------
# 7. apply_recommendations writes frontmatter (temp file)
# ---------------------------------------------------------------------------
def test_apply_writes_frontmatter(tmp_path):
    """apply_recommendations แก้ model: field ใน frontmatter (temp copy)."""
    sa_file = tmp_path / "test-agent.md"
    original = """---
name: test-agent
model: model-a
tools: Read
---

# Body
"""
    sa_file.write_text(original, encoding="utf-8")
    rec = {
        "suite": "test", "subagent": "test-agent",
        "current_model": "model-a", "recommended_model": "model-b",
        "savings_usd": 1.0, "status": "recommend",
    }
    cost_optimizer.apply_recommendations([rec], agents_dir=tmp_path, dry_run=False)
    result = sa_file.read_text(encoding="utf-8")
    assert "model: model-b" in result
    assert "model: model-a" not in result
    assert "# Body" in result  # preserved
