"""Tests for scripts/eval/race_eval.py — multi-model concurrent eval (R2).

Iron Law #1: failing tests written FIRST. These pin the contract of
race_eval() before any implementation exists.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import race_eval  # noqa: E402  -- module under test (created by R2)


# ---------------------------------------------------------------------------
# Sample cases + mock delegate
# ---------------------------------------------------------------------------
CASE_DOCTOR = {
    "id": "doctor-1",
    "subagent": "clinical-reasoner",
    "prompt": "What is the first-line drug for hypertension?",
    "required": ["lisinopril"],
    "forbidden": ["i don't know"],
}


def _mock_delegate_passing(model: str, prompt: str) -> str:
    """A mock that always returns a response containing 'lisinopril'."""
    return f"[{model}] lisinopril is first-line."


def _mock_delegate_failing(model: str, prompt: str) -> str:
    """A mock that always returns a response without required keyword."""
    return f"[{model}] i don't know"


def _mock_delegate_first_only(model: str, prompt: str) -> str:
    """Model A passes, model B fails — for per-model distinction tests."""
    if model == "model-a":
        return "lisinopril works"
    return "no idea"


# ---------------------------------------------------------------------------
# 1. Concurrency: wall-clock < sequential
# ---------------------------------------------------------------------------
def test_race_eval_concurrent_all_models(monkeypatch):
    """All model×k tasks run concurrently — wall-clock should be far below
    sequential (each mock call sleeps ~0.15s; 3 models × k=2 = 6 calls).
    Sequential ~0.9s; concurrent with max_workers=6 should be ~0.15s.
    """
    def slow_delegate(model, prompt):
        time.sleep(0.15)
        return "lisinopril"
    monkeypatch.setattr(race_eval, "delegate_to_model", slow_delegate)

    t0 = time.monotonic()
    out = race_eval.race_eval(
        models=["a", "b", "c"], case=CASE_DOCTOR, k=2, max_workers=6,
    )
    elapsed = time.monotonic() - t0
    # Concurrent: ~0.15s. Allow generous slack for CI scheduling (0.5s).
    assert elapsed < 0.5, f"Expected concurrent (<0.5s), took {elapsed:.2f}s"
    assert len(out["by_model"]) == 3


# ---------------------------------------------------------------------------
# 2. pass@k computed correctly per model
# ---------------------------------------------------------------------------
def test_pass_at_k_per_model_correct(monkeypatch):
    """model-a passes 2/2 → pass@k=1.0; model-b fails 2/2 → pass@k=0.0."""
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_first_only)
    out = race_eval.race_eval(
        models=["model-a", "model-b"], case=CASE_DOCTOR, k=2, max_workers=4,
    )
    assert out["by_model"]["model-a"]["pass_at_k"] == pytest.approx(1.0)
    assert out["by_model"]["model-b"]["pass_at_k"] == pytest.approx(0.0)
    assert out["by_model"]["model-a"]["passed"] == 2
    assert out["by_model"]["model-a"]["total_samples"] == 2


# ---------------------------------------------------------------------------
# 3. first-past-the-post winner (fastest first pass)
# ---------------------------------------------------------------------------
def test_first_past_the_post_winner(monkeypatch):
    """Winner = model that passes its first sample fastest."""
    call_times = {}

    def timed_delegate(model, prompt):
        # model-a is fast (0.01s), model-b is slow (0.10s)
        delay = 0.01 if model == "model-a" else 0.10
        time.sleep(delay)
        call_times[model] = time.monotonic()
        return "lisinopril"  # both pass

    monkeypatch.setattr(race_eval, "delegate_to_model", timed_delegate)
    out = race_eval.race_eval(
        models=["model-a", "model-b"], case=CASE_DOCTOR, k=1, max_workers=2,
    )
    assert out["winner"] == "model-a"  # faster first pass


# ---------------------------------------------------------------------------
# 4. max_workers respected (no more than max_workers concurrent)
# ---------------------------------------------------------------------------
def test_max_workers_respected(monkeypatch):
    """At most `max_workers` tasks run concurrently at any instant."""
    import threading
    active = {"current": 0, "peak": 0}
    lock = threading.Lock()

    def counting_delegate(model, prompt):
        with lock:
            active["current"] += 1
            active["peak"] = max(active["peak"], active["current"])
        time.sleep(0.05)
        with lock:
            active["current"] -= 1
        return "lisinopril"

    monkeypatch.setattr(race_eval, "delegate_to_model", counting_delegate)
    # 6 tasks (3 models × k=2), max_workers=2 → peak should be ≤ 2
    race_eval.race_eval(
        models=["a", "b", "c"], case=CASE_DOCTOR, k=2, max_workers=2,
    )
    assert active["peak"] <= 2, f"peak concurrency {active['peak']} > max_workers 2"


# ---------------------------------------------------------------------------
# 5. Partial failure tolerated (one model raises → others still complete)
# ---------------------------------------------------------------------------
def test_partial_failure_tolerated(monkeypatch):
    def flaky_delegate(model, prompt):
        if model == "boom":
            raise RuntimeError("model boom exploded")
        return "lisinopril"

    monkeypatch.setattr(race_eval, "delegate_to_model", flaky_delegate)
    out = race_eval.race_eval(
        models=["good", "boom", "alsogood"], case=CASE_DOCTOR, k=2, max_workers=3,
    )
    # boom's samples are counted as fails (pass=False), not crashes
    assert out["by_model"]["boom"]["passed"] == 0
    assert out["by_model"]["boom"]["total_samples"] == 2
    assert out["by_model"]["good"]["passed"] == 2
    assert out["by_model"]["alsogood"]["passed"] == 2


# ---------------------------------------------------------------------------
# 6. render_race_report format
# ---------------------------------------------------------------------------
def test_render_report_format(monkeypatch):
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_passing)
    out = race_eval.race_eval(
        models=["a", "b"], case=CASE_DOCTOR, k=2, max_workers=2,
    )
    report = race_eval.render_race_report(out)
    assert "a" in report and "b" in report
    # Should have a verdict column header
    assert "verdict" in report.lower() or "winner" in report.lower() or "best" in report.lower()


# ---------------------------------------------------------------------------
# 7. Empty models → empty result
# ---------------------------------------------------------------------------
def test_empty_models_returns_empty(monkeypatch):
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_passing)
    out = race_eval.race_eval(models=[], case=CASE_DOCTOR, k=2, max_workers=4)
    assert out["by_model"] == {}
    assert out["winner"] is None or out.get("winner") is None


# ---------------------------------------------------------------------------
# 8. dry_run=True → zero delegate calls
# ---------------------------------------------------------------------------
def test_dry_run_makes_zero_calls(monkeypatch):
    call_count = {"n": 0}

    def counting(model, prompt):
        call_count["n"] += 1
        return "lisinopril"

    monkeypatch.setattr(race_eval, "delegate_to_model", counting)
    out = race_eval.race_eval(
        models=["a", "b"], case=CASE_DOCTOR, k=2, max_workers=4, dry_run=True,
    )
    assert call_count["n"] == 0
    assert out["dry_run"] is True


# ---------------------------------------------------------------------------
# 9. Custom judge function respected
# ---------------------------------------------------------------------------
def test_custom_judge_fn_respected(monkeypatch):
    """A custom judge that always returns False → pass@k = 0 for all."""
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_passing)

    def always_fail(case, response):
        return False

    out = race_eval.race_eval(
        models=["a"], case=CASE_DOCTOR, k=2, max_workers=2, judge_fn=always_fail,
    )
    assert out["by_model"]["a"]["pass_at_k"] == 0.0
    assert out["by_model"]["a"]["passed"] == 0


# ---------------------------------------------------------------------------
# 10. k >= samples → pass@k returns 1.0 if at least one pass (boundary)
# ---------------------------------------------------------------------------
def test_k_larger_than_samples_returns_one(monkeypatch):
    """With k=5 but only 2 samples taken, and 1 pass: n=2,c=1,k=5.
    Since n-c=1 < k=5, the standard formula returns 1.0 (at least one of
    any 5 picks must hit the 1 pass). race_eval takes `k` samples literally
    (loops k times), so k=5 → 5 samples. Use a model that passes 3/5.
    """
    call_n = {"n": 0}

    def mixed(model, prompt):
        call_n["n"] += 1
        # pass on samples 1,3,5; fail on 2,4
        return "lisinopril" if call_n["n"] % 2 == 1 else "nothing"

    monkeypatch.setattr(race_eval, "delegate_to_model", mixed)
    out = race_eval.race_eval(
        models=["a"], case=CASE_DOCTOR, k=5, max_workers=1,  # serial for determinism
    )
    # n=5, c=3, k=5 → n-c=2 < k=5 → pass@k = 1.0
    assert out["by_model"]["a"]["pass_at_k"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 11. Multiple cases (run_race across a suite subset)
# ---------------------------------------------------------------------------
def test_run_race_multiple_cases(monkeypatch):
    """run_race() helper should iterate cases + produce per-case results."""
    case2 = {**CASE_DOCTOR, "id": "doctor-2", "prompt": "Second case"}
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_passing)
    out = race_eval.run_race(
        models=["a", "b"], cases=[CASE_DOCTOR, case2], k=1, max_workers=4,
    )
    assert "doctor-1" in out["by_case"]
    assert "doctor-2" in out["by_case"]
    assert out["by_case"]["doctor-1"]["by_model"]["a"]["pass_at_k"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 12. S6.0: token recording in race results (for cost tracking)
# ---------------------------------------------------------------------------
def test_race_eval_records_tokens(monkeypatch):
    """S6.0: race_eval ต้อง record tokens_in/tokens_out ใน sample + aggregate."""
    monkeypatch.setattr(race_eval, "delegate_to_model", _mock_delegate_passing)
    out = race_eval.race_eval(
        models=["a", "b"], case=CASE_DOCTOR, k=2, max_workers=4,
    )
    # tokens ในแต่ละ sample
    for model in ["a", "b"]:
        samples = out["by_model"][model].get("samples", [])
        assert len(samples) == 2
        for s in samples:
            assert "tokens_in" in s
            assert "tokens_out" in s
            assert s["tokens_in"] > 0  # prompt ไม่ว่าง
            assert s["tokens_out"] > 0  # response ไม่ว่าง
    # aggregate ใน by_model
    assert out["by_model"]["a"]["tokens_in"] > 0
    assert out["by_model"]["a"]["tokens_out"] > 0
