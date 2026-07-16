"""Tests for scripts/eval/run_pipeline_eval.py — Q4 end-to-end pipeline eval.

Pipeline eval chains subagent calls across stages (e.g. finance:
data-fetcher → analyst → debater), feeding each stage's output into the next
stage's prompt, then judges the FINAL output. This tests the chaining logic,
handoff injection, and pipeline-level pass@k — all pure / mockable.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import run_pipeline_eval as pe  # noqa: E402


def _stage(subagent, prompt, required=None, forbidden=None):
    return {"subagent": subagent, "prompt": prompt,
            "required": required or [], "forbidden": forbidden or []}


def _pipeline_suite(stages, model_overrides=None):
    """Build a minimal pipeline suite dict."""
    return {
        "suite": "test-pipeline",
        "description": "test",
        "stages": stages,
        "model_overrides": model_overrides or {},
    }


# ---------------------------------------------------------------------------
# Suite loading
# ---------------------------------------------------------------------------

def test_load_pipeline_suite_parses(tmp_path):
    """load_suite reads a pipeline suite with 'stages' (not 'cases')."""
    suite = _pipeline_suite([_stage("a", "p1"), _stage("b", "p2")])
    p = tmp_path / "test-pipeline.json"
    p.write_text(json.dumps(suite))
    loaded = pe.load_suite(p)
    assert loaded["suite"] == "test-pipeline"
    assert len(loaded["stages"]) == 2


def test_load_suite_rejects_missing_stages(tmp_path):
    """A suite without 'stages' key returns None (not a pipeline suite)."""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"suite": "x"}))
    assert pe.load_suite(p) is None


# ---------------------------------------------------------------------------
# Chain stages — output of stage N injected into stage N+1 prompt
# ---------------------------------------------------------------------------

def test_chain_stages_passes_output_forward(monkeypatch):
    """stage2's prompt must contain stage1's output text."""
    suite = _pipeline_suite([
        _stage("fetcher", "Get data for AAPL"),
        _stage("analyst", "Analyze this: {prev_output}"),
    ])
    captured = {}

    def fake_delegate(model, prompt):
        captured[model] = captured.get(model, []) + [prompt]
        return f"OUTPUT_FROM_STAGE for {prompt[:20]}"

    monkeypatch.setattr(pe, "delegate_to_model", fake_delegate)

    result = pe.run_pipeline(suite, models=["m1"], k=1)
    # stage2 prompt should contain stage1's output
    stage2_prompts = [p for p in captured["m1"] if "{prev_output}" not in p or "OUTPUT_FROM_STAGE" in p]
    assert any("OUTPUT_FROM_STAGE" in p for p in captured["m1"]), \
        "stage2 prompt must contain stage1 output"


def test_chain_stages_three_stages(monkeypatch):
    """3-stage chain: stage1 → stage2 → stage3, each receives prior output."""
    suite = _pipeline_suite([
        _stage("s1", "step1"),
        _stage("s2", "step2 {prev_output}"),
        _stage("s3", "step3 {prev_output}"),
    ])
    call_log = []

    def fake_delegate(model, prompt):
        call_log.append(prompt)
        return f"R{len(call_log)}"

    monkeypatch.setattr(pe, "delegate_to_model", fake_delegate)
    pe.run_pipeline(suite, models=["m"], k=1)
    assert len(call_log) == 3
    # stage2 prompt contains R1 (stage1 output)
    assert "R1" in call_log[1]
    # stage3 prompt contains R2 (stage2 output)
    assert "R2" in call_log[2]


# ---------------------------------------------------------------------------
# Judge final only — only the LAST stage's required/forbidden is checked
# ---------------------------------------------------------------------------

def test_judge_final_stage_only(monkeypatch):
    """Pipeline passes only if the FINAL stage's output satisfies its judge."""
    suite = _pipeline_suite([
        _stage("s1", "p1", required=["WRONG_THING"]),  # would fail if judged
        _stage("s2", "p2 {prev_output}", required=["FINAL_OK"]),  # final stage
    ])

    def fake_delegate(model, prompt):
        if "step1" in prompt or "p1" in prompt:
            return "intermediate without WRONG_THING"
        return "final output with FINAL_OK"

    monkeypatch.setattr(pe, "delegate_to_model", fake_delegate)
    result = pe.run_pipeline(suite, models=["m"], k=1)
    # Final stage passes → pipeline pass, even though stage1 would fail its judge
    assert result["by_model"]["m"]["pass_at_k"] == 1.0


def test_judge_final_stage_fails(monkeypatch):
    """Pipeline fails if the final stage's required keyword is missing."""
    suite = _pipeline_suite([
        _stage("s1", "p1"),
        _stage("s2", "p2 {prev_output}", required=["NEVER_PRESENT"]),
    ])
    monkeypatch.setattr(pe, "delegate_to_model", lambda m, p: "no keywords here")
    result = pe.run_pipeline(suite, models=["m"], k=1)
    assert result["by_model"]["m"]["pass_at_k"] == 0.0


def test_judge_final_stage_forbidden_present(monkeypatch):
    """Pipeline fails if the final stage emits a forbidden keyword."""
    suite = _pipeline_suite([
        _stage("s1", "p1"),
        _stage("s2", "p2", forbidden=["HALLUCINATION"]),
    ])
    monkeypatch.setattr(pe, "delegate_to_model", lambda m, p: "contains HALLUCINATION trap")
    result = pe.run_pipeline(suite, models=["m"], k=1)
    assert result["by_model"]["m"]["pass_at_k"] == 0.0


# ---------------------------------------------------------------------------
# Pipeline pass@k
# ---------------------------------------------------------------------------

def test_pipeline_pass_at_k_all_pass(monkeypatch):
    """k=3, all final-stage outputs pass → pass@k = 1.0."""
    suite = _pipeline_suite([_stage("s1", "p1"), _stage("s2", "p2", required=["OK"])])
    monkeypatch.setattr(pe, "delegate_to_model", lambda m, p: "OK")
    result = pe.run_pipeline(suite, models=["m"], k=3)
    assert result["by_model"]["m"]["pass_at_k"] == 1.0


def test_pipeline_pass_at_k_all_fail(monkeypatch):
    """k=3, all fail → pass@k = 0.0."""
    suite = _pipeline_suite([_stage("s1", "p1"), _stage("s2", "p2", required=["OK"])])
    monkeypatch.setattr(pe, "delegate_to_model", lambda m, p: "nope")
    result = pe.run_pipeline(suite, models=["m"], k=3)
    assert result["by_model"]["m"]["pass_at_k"] == 0.0


# ---------------------------------------------------------------------------
# Model overrides — different model per stage
# ---------------------------------------------------------------------------

def test_model_overrides_per_stage(monkeypatch):
    """model_overrides maps stage subagent → model, overriding the default."""
    suite = _pipeline_suite(
        [_stage("s1", "p1"), _stage("s2", "p2", required=["OK"])],
        model_overrides={"s1": "cheap-model", "s2": "smart-model"})
    used_models = []

    def fake_delegate(model, prompt):
        used_models.append(model)
        return "OK"

    monkeypatch.setattr(pe, "delegate_to_model", fake_delegate)
    pe.run_pipeline(suite, models=["default-model"], k=1)
    # s1 should use cheap-model, s2 should use smart-model
    assert "cheap-model" in used_models
    assert "smart-model" in used_models


# ---------------------------------------------------------------------------
# Handoff contract validation
# ---------------------------------------------------------------------------

def test_handoff_contract_validation_pass():
    """validate_handoff returns True when final output has required fields."""
    contract = {"required_fields": ["thesis", "rating"]}
    output = json.dumps({"thesis": "bullish", "rating": "buy", "extra": "x"})
    assert pe.validate_handoff(output, contract) is True


def test_handoff_contract_validation_missing_field():
    """validate_handoff returns False when a required field is missing."""
    contract = {"required_fields": ["thesis", "rating"]}
    output = json.dumps({"thesis": "bullish"})  # missing rating
    assert pe.validate_handoff(output, contract) is False


def test_handoff_contract_no_required_always_pass():
    """No required_fields in contract → always pass (lenient)."""
    output = "not even json"
    assert pe.validate_handoff(output, {}) is True


def test_handoff_contract_non_json_output():
    """Non-JSON output with required fields → False (can't extract fields)."""
    contract = {"required_fields": ["thesis"]}
    assert pe.validate_handoff("just plain text", contract) is False


# ---------------------------------------------------------------------------
# W5: multi-stage cost attribution (token recording per pipeline run)
# ---------------------------------------------------------------------------
def test_chain_stages_with_tokens_returns_token_counts(monkeypatch):
    """W5: _chain_stages_with_tokens() ต้องคืน (output, tokens_in, tokens_out)."""
    def mock_delegate(model, prompt):
        return "stage response " * 20

    monkeypatch.setattr(pe, "delegate_to_model", mock_delegate)
    stages = [
        {"id": "s1", "subagent": "a", "prompt": "Step 1: {input}"},
        {"id": "s2", "subagent": "b", "prompt": "Step 2: {prev_output}"},
    ]
    case = {"id": "c1", "input": "test data here"}
    output, tok_in, tok_out = pe._chain_stages_with_tokens(stages, "model", case, {})
    assert "stage response" in output
    assert tok_in > 0
    assert tok_out > 0


def test_run_pipeline_records_tokens(monkeypatch):
    """W5: run_pipeline() ต้อง record tokens_in/tokens_out ใน by_model."""
    def mock_delegate(model, prompt):
        return "pipeline output with verdict"
    monkeypatch.setattr(pe, "delegate_to_model", mock_delegate)
    suite = {
        "suite": "test-pipe",
        "stages": [
            {"id": "s1", "subagent": "a", "prompt": "Do: {topic}", "required": [], "forbidden": []},
            {"id": "s2", "subagent": "b", "prompt": "Judge: {prev_output}", "required": ["verdict"], "forbidden": []},
        ],
        "cases": [{"id": "c1", "topic": "test decision"}],
        "model_overrides": {},
    }
    result = pe.run_pipeline(suite, ["model-a"], k=1)
    model_stats = result["by_model"]["model-a"]
    assert "tokens_in" in model_stats, "by_model ต้องมี tokens_in (W5)"
    assert "tokens_out" in model_stats, "by_model ต้องมี tokens_out (W5)"
    assert model_stats["tokens_in"] > 0
    assert model_stats["tokens_out"] > 0
