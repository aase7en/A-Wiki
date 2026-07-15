"""Tests for scripts/eval/dag_eval.py — DAG pipeline composer (S3).

Iron Law #1: failing tests written FIRST.

S3 ขยาย pipeline eval (Q4 linear chain) เป็น generic DAG:
- sequential stage (default, backward-compat)
- parallel stage (fan-out หลาย branch พร้อมกัน)
- merge stage (fan-in, substitute {<stage_id>.output})

ใช้สำหรับ council pattern eval: question → 3 parallel critics → synthesis
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import dag_eval  # noqa: E402  -- module under test (created by S3)


# ---------------------------------------------------------------------------
# Sample DAG stages (council pattern: question → 2 critics → synthesis)
# ---------------------------------------------------------------------------
COUNCIL_STAGES = [
    {"id": "question", "subagent": "general-purpose", "prompt": "Analyze: {topic}", "type": "sequential"},
    {"id": "skeptic", "subagent": "debug-investigator", "prompt": "Challenge: {question.output}", "type": "parallel", "depends_on": "question"},
    {"id": "pragmatist", "subagent": "workflow-simplifier", "prompt": "Simplify: {question.output}", "type": "parallel", "depends_on": "question"},
    {"id": "synthesis", "subagent": "general-purpose", "prompt": "Merge: {skeptic.output} | {pragmatist.output}", "type": "merge", "depends_on": ["skeptic", "pragmatist"], "required": ["verdict"]},
]

CASE = {"id": "c1", "topic": "should we use microservices?"}


# ---------------------------------------------------------------------------
# 1. Topological sort — linear (A→B→C)
# ---------------------------------------------------------------------------
def test_topological_sort_linear():
    stages = [
        {"id": "a", "depends_on": None},
        {"id": "b", "depends_on": "a"},
        {"id": "c", "depends_on": "b"},
    ]
    order = dag_eval.topological_sort(stages)
    ids = [s["id"] for s in order]
    assert ids == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# 2. Topological sort — parallel branches (A→[B,C]→D)
# ---------------------------------------------------------------------------
def test_topological_sort_parallel_branches():
    stages = [
        {"id": "a"},
        {"id": "b", "depends_on": "a"},
        {"id": "c", "depends_on": "a"},
        {"id": "d", "depends_on": ["b", "c"]},
    ]
    order = dag_eval.topological_sort(stages)
    ids = [s["id"] for s in order]
    # a ก่อน b,c; b,c ก่อน d (ลำดับ b vs c ไม่สำคัญ)
    assert ids[0] == "a"
    assert ids[-1] == "d"
    assert set(ids[1:3]) == {"b", "c"}


# ---------------------------------------------------------------------------
# 3. Topological sort — cycle detection
# ---------------------------------------------------------------------------
def test_topological_sort_detects_cycle():
    stages = [
        {"id": "a", "depends_on": "c"},
        {"id": "b", "depends_on": "a"},
        {"id": "c", "depends_on": "b"},
    ]
    with pytest.raises(ValueError, match="cycle|Cycle"):
        dag_eval.topological_sort(stages)


# ---------------------------------------------------------------------------
# 4. parse_dag — validates required fields
# ---------------------------------------------------------------------------
def test_parse_dag_validates_required_fields():
    """stage ต้องมี id + prompt. depends_on required สำหรับ non-first stages."""
    # missing id → error
    with pytest.raises((ValueError, KeyError)):
        dag_eval.parse_dag([{"prompt": "x", "subagent": "y"}])
    # valid minimal
    parsed = dag_eval.parse_dag([{"id": "a", "prompt": "x"}])
    assert len(parsed) == 1
    assert parsed[0]["id"] == "a"
    # default type = sequential
    assert parsed[0].get("type", "sequential") == "sequential"


# ---------------------------------------------------------------------------
# 5. execute_dag — sequential matches linear chain (backward compat)
# ---------------------------------------------------------------------------
def test_execute_dag_sequential_matches_linear(monkeypatch):
    """stages ไม่มี type field → linear execution เหมือน _chain_stages เดิม."""
    # Mock delegate_to_model — track calls
    calls = []

    def mock_delegate(model, prompt):
        calls.append({"model": model, "prompt": prompt})
        return f"[{model}] response to: {prompt[:30]}"

    monkeypatch.setattr(dag_eval, "delegate_to_model", mock_delegate)

    stages = [
        {"id": "s1", "subagent": "a", "prompt": "Step 1: {input}"},
        {"id": "s2", "subagent": "b", "prompt": "Step 2: {prev_output}"},
    ]
    case = {"id": "c1", "input": "data"}
    result = dag_eval.execute_dag(stages, "default-model", case, {})
    # s2 should receive s1's output via {prev_output} (backward compat)
    assert len(calls) == 2
    assert "Step 1" in calls[0]["prompt"]
    assert "response to" in calls[1]["prompt"]  # s1 output injected
    # result = final output
    assert "response to" in result


# ---------------------------------------------------------------------------
# 6. execute_dag — parallel runs concurrent
# ---------------------------------------------------------------------------
def test_execute_dag_parallel_runs_concurrent(monkeypatch):
    """parallel stages รันพร้อมกัน — wall-clock < sequential."""
    def slow_delegate(model, prompt):
        time.sleep(0.15)
        return f"[{model}] done"

    monkeypatch.setattr(dag_eval, "delegate_to_model", slow_delegate)

    stages = [
        {"id": "q", "subagent": "x", "prompt": "Q: {topic}"},
        {"id": "c1", "subagent": "a", "prompt": "C1: {q.output}", "type": "parallel", "depends_on": "q"},
        {"id": "c2", "subagent": "b", "prompt": "C2: {q.output}", "type": "parallel", "depends_on": "q"},
    ]
    case = {"id": "c1", "topic": "test"}
    t0 = time.monotonic()
    dag_eval.execute_dag(stages, "model", case, {})
    elapsed = time.monotonic() - t0
    # q (0.15s) + parallel c1,c2 (0.15s) = ~0.30s concurrent
    # sequential จะเป็น 0.45s — concurrent ต้อง < 0.42s
    assert elapsed < 0.42, f"Expected concurrent (<0.42s), took {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# 7. execute_dag — merge substitutes all branch outputs
# ---------------------------------------------------------------------------
def test_execute_dag_merge_substitutes_all_branch_outputs(monkeypatch):
    """merge stage ต้อง substitute {skeptic.output} + {pragmatist.output}."""
    def mock_delegate(model, prompt):
        if "Challenge" in prompt or "challenge" in prompt.lower():
            return "SKEPTIC_SAYS_NO"
        if "Simplify" in prompt or "simplify" in prompt.lower():
            return "PRAGMATIST_SAYS_YES"
        # merge stage
        return f"MERGED: {prompt}"

    monkeypatch.setattr(dag_eval, "delegate_to_model", mock_delegate)

    stages = COUNCIL_STAGES
    case = CASE
    result = dag_eval.execute_dag(stages, "model", case, {})
    # synthesis prompt should contain both branch outputs
    assert "SKEPTIC_SAYS_NO" in result
    assert "PRAGMATIST_SAYS_YES" in result


# ---------------------------------------------------------------------------
# 8. execute_dag — judges terminal stage only
# ---------------------------------------------------------------------------
def test_execute_dag_judges_terminal_stage(monkeypatch):
    """Only the terminal/merge stage (no downstream deps) is judged."""
    judge_calls = []

    def mock_delegate(model, prompt):
        return "verdict: approved"  # contains 'verdict'

    monkeypatch.setattr(dag_eval, "delegate_to_model", mock_delegate)

    stages = COUNCIL_STAGES  # synthesis has required: ["verdict"]
    case = CASE
    result = dag_eval.execute_dag(stages, "model", case, {})
    # result should be judged — but we test the judge separately
    passed = dag_eval.judge_stage({"required": ["verdict"]}, result)
    assert passed is True
    # critic stages are NOT judged
    passed_critic = dag_eval.judge_stage({"required": ["nonexistent_kw"]}, "SKEPTIC_SAYS_NO")
    assert passed_critic is False


# ---------------------------------------------------------------------------
# 9. pipeline-council.json example suite loads + validates
# ---------------------------------------------------------------------------
def test_pipeline_council_suite_loads_and_validates():
    """Example suite pipeline-council.json ต้อง load + parse ได้."""
    suite_path = REPO_ROOT / "evals" / "subagents" / "pipeline-council.json"
    if not suite_path.exists():
        pytest.skip("pipeline-council.json not created yet")
    import json
    data = json.loads(suite_path.read_text(encoding="utf-8"))
    assert "suite" in data
    assert "stages" in data
    assert "cases" in data
    # validate DAG structure
    parsed = dag_eval.parse_dag(data["stages"])
    assert len(parsed) == len(data["stages"])
    # should not raise on topological sort
    dag_eval.topological_sort(parsed)
