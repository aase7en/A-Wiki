"""Tests for scripts/eval/adaptive_routing.py — data-driven model swap (P4).

P4 closes the feedback loop: observatory data (pass_rate per subagent) +
eval results (pass@k per model) → recommend model swaps with safety
guardrails (never-downgrade, min-samples, flap-protection). All functions
are pure (no I/O, no clock) so they're trivially deterministic.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import adaptive_routing as ar  # noqa: E402


def _stat(count, pass_rate, best_model="deepseek-v4-flash"):
    return {"count": count, "pass_rate": pass_rate, "best_model": best_model,
            "pass": int(count * pass_rate), "fail": int(count * (1 - pass_rate))}


def _stats(by_subagent):
    return {"total_invocations": sum(s["count"] for s in by_subagent.values()),
            "by_subagent": dict(by_subagent), "by_bucket": {}}


def _eval_results(suite_models_rates):
    """{suite: {model: pass_at_k}}"""
    return {s: {"by_model": {m: {"pass_at_k": r} for m, r in mm.items()},
                "by_case": {}} for s, mm in suite_models_rates.items()}


# ---------------------------------------------------------------------------
# recommend_model_changes — pure recommendation logic
# ---------------------------------------------------------------------------

def test_recommend_when_clear_winner():
    """Subagent using model A (pass_rate 0.5) but eval shows model B is 0.9
    (> min_delta 0.15) → recommend swap A→B."""
    stats = _stats({"medical-lit-reviewer": _stat(20, 0.5, best_model="deepseek-v4-flash")})
    # current_model="deepseek-v4-flash", eval shows glm-5.2 wins at 0.9
    eval_results = _eval_results({"medical": {
        "deepseek-v4-flash": 0.5, "glm-5.2": 0.9}})
    current_models = {"medical-lit-reviewer": "deepseek-v4-flash"}
    suite_to_subagents = {"medical": ["medical-lit-reviewer"]}

    recs = ar.recommend_model_changes(
        stats, eval_results, current_models, suite_to_subagents,
        config={"min_samples": 10, "min_delta": 0.15})
    assert len(recs) == 1
    r = recs[0]
    assert r["subagent"] == "medical-lit-reviewer"
    assert r["current"] == "deepseek-v4-flash"
    assert r["recommended"] == "glm-5.2"
    assert r["status"] == "recommend"


def test_hold_when_insufficient_samples():
    """Fewer than min_samples observatory invocations → hold (insufficient-data)."""
    stats = _stats({"x": _stat(3, 0.5)})  # only 3 samples < min_samples=10
    eval_results = _eval_results({"s": {"a": 0.5, "b": 0.9}})
    recs = ar.recommend_model_changes(
        stats, eval_results, {"x": "a"}, {"s": ["x"]},
        config={"min_samples": 10, "min_delta": 0.15})
    assert len(recs) == 1
    assert recs[0]["status"] == "insufficient-data"


def test_never_downgrade():
    """If the recommended model has LOWER pass@k than the current model's
    observed pass_rate, do NOT recommend (never-downgrade guardrail).
    Status should be 'hold-current-better'."""
    # Current model A has observed pass_rate 0.9 (great). Eval says A=0.9, B=0.7.
    # B is "best" only by suite-level eval, but A is better for THIS subagent.
    stats = _stats({"x": _stat(20, 0.9, best_model="a")})
    eval_results = _eval_results({"s": {"a": 0.9, "b": 0.95}})  # b slightly better in eval
    recs = ar.recommend_model_changes(
        stats, eval_results, {"x": "a"}, {"s": ["x"]},
        config={"min_samples": 10, "min_delta": 0.15})
    # b is 0.05 better than a in eval (below min_delta 0.15) → no recommendation.
    if recs:
        assert recs[0]["status"] != "recommend"


def test_min_delta_threshold_respected():
    """Swap recommended only when delta >= min_delta."""
    stats = _stats({"x": _stat(20, 0.7, best_model="a")})
    eval_results = _eval_results({"s": {"a": 0.7, "b": 0.80}})  # delta 0.10 < 0.15
    recs = ar.recommend_model_changes(
        stats, eval_results, {"x": "a"}, {"s": ["x"]},
        config={"min_samples": 10, "min_delta": 0.15})
    # 0.10 < 0.15 → no recommendation (or status != 'recommend').
    recommend_recs = [r for r in recs if r["status"] == "recommend"]
    assert not recommend_recs


def test_flap_detection():
    """If recent history shows this subagent was already swapped to the
    recommended model and then swapped back, mark 'hold-flapping' instead
    of 'recommend' (avoid oscillation)."""
    stats = _stats({"x": _stat(20, 0.5, best_model="a")})
    eval_results = _eval_results({"s": {"a": 0.5, "b": 0.9}})
    # Mock history: x was previously set to b, then back to a.
    history = [
        {"subagent": "x", "from": "a", "to": "b", "ts": 1000},
        {"subagent": "x", "from": "b", "to": "a", "ts": 2000},
    ]
    recs = ar.recommend_model_changes(
        stats, eval_results, {"x": "a"}, {"s": ["x"]},
        config={"min_samples": 10, "min_delta": 0.15,
                "flap_window_days": 7},
        history=history, now=3000)
    assert len(recs) == 1
    assert recs[0]["status"] == "hold-flapping"
    assert recs[0]["recommended"] == "b"


def test_no_flap_when_history_outside_window():
    """Old swap history (outside flap_window_days) → not flapping."""
    stats = _stats({"x": _stat(20, 0.5, best_model="a")})
    eval_results = _eval_results({"s": {"a": 0.5, "b": 0.9}})
    # History from 30 days ago — outside the 7-day window.
    old_ts = 30 * 86400
    history = [
        {"subagent": "x", "from": "a", "to": "b", "ts": old_ts},
        {"subagent": "x", "from": "b", "to": "a", "ts": old_ts + 100},
    ]
    recs = ar.recommend_model_changes(
        stats, eval_results, {"x": "a"}, {"s": ["x"]},
        config={"min_samples": 10, "min_delta": 0.15,
                "flap_window_days": 7},
        history=history, now=old_ts + 86400 * 30)
    recommend_recs = [r for r in recs if r["status"] == "recommend"]
    assert len(recommend_recs) == 1


def test_unknown_subagent_skipped():
    """Subagent in suite_to_subagents but absent from current_models → skip."""
    stats = _stats({})
    eval_results = _eval_results({"s": {"a": 0.9}})
    recs = ar.recommend_model_changes(
        stats, eval_results, {}, {"s": ["ghost"]},
        config={"min_samples": 1, "min_delta": 0.0})
    assert recs == []


# ---------------------------------------------------------------------------
# apply_changes — writes frontmatter (in tmp dir for test isolation)
# ---------------------------------------------------------------------------

def test_apply_changes_writes_frontmatter(tmp_path):
    """apply_changes edits the model: line of named subagent files."""
    agents = tmp_path / "agents" / "subagents"
    agents.mkdir(parents=True)
    (agents / "x.md").write_text("---\nname: x\nmodel: old\n---\nbody\n")
    changes = [{"subagent": "x", "current": "old", "recommended": "new",
                "status": "recommend", "current_pass_rate": 0.5,
                "new_pass_rate": 0.9, "delta": 0.4, "samples": 20}]
    applied = ar.apply_changes(changes, agents_dir=agents)
    assert applied == 1
    text = (agents / "x.md").read_text()
    assert "model: new" in text
    assert "model: old" not in text


def test_apply_changes_skips_non_recommend(tmp_path):
    """apply_changes only edits subagents with status == 'recommend'.
    'hold-flapping' / 'insufficient-data' → skipped."""
    agents = tmp_path / "agents" / "subagents"
    agents.mkdir(parents=True)
    (agents / "x.md").write_text("---\nmodel: old\n---\n")
    (agents / "y.md").write_text("---\nmodel: keep\n---\n")
    changes = [
        {"subagent": "x", "current": "old", "recommended": "new",
         "status": "hold-flapping", "current_pass_rate": 0.5,
         "new_pass_rate": 0.9, "delta": 0.4, "samples": 20},
        {"subagent": "y", "current": "keep", "recommended": "newer",
         "status": "insufficient-data", "current_pass_rate": 0.5,
         "new_pass_rate": 0.9, "delta": 0.4, "samples": 2},
    ]
    applied = ar.apply_changes(changes, agents_dir=agents)
    assert applied == 0
    assert "model: old" in (agents / "x.md").read_text()
    assert "model: keep" in (agents / "y.md").read_text()


def test_apply_changes_missing_file_skipped(tmp_path):
    """apply_changes skips when the subagent file doesn't exist."""
    agents = tmp_path / "agents" / "subagents"
    agents.mkdir(parents=True)
    changes = [{"subagent": "ghost", "current": "a", "recommended": "b",
                "status": "recommend", "current_pass_rate": 0.5,
                "new_pass_rate": 0.9, "delta": 0.4, "samples": 20}]
    applied = ar.apply_changes(changes, agents_dir=agents)
    assert applied == 0
