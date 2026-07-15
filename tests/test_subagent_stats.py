"""Tests for the Subagent Observatory aggregation module (subagent_stats.py).

Verifies the pure aggregation function that reads .tmp/live-events.jsonl,
filters `subagent_invoke` events, and produces per-subagent + per-model
statistics. Also exercises the CLI entrypoint in dry form.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import subagent_stats as st  # noqa: E402


def _write_events(path: Path, events: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def test_aggregate_empty_log(tmp_path):
    """No events → empty stats with the expected schema."""
    log = tmp_path / "live-events.jsonl"
    log.write_text("")
    out = st.aggregate(log_file=log)
    assert out["total_invocations"] == 0
    assert out["by_subagent"] == {}
    assert out["by_bucket"] == {}
    assert out["window_seconds"] >= 0


def test_aggregate_counts_pass_and_fail(tmp_path):
    """Two pass + one fail for medical-lit-reviewer → count=3, pass_rate≈0.67."""
    log = tmp_path / "live-events.jsonl"
    _write_events(log, [
        {"ts": 1.0, "type": "subagent_invoke", "subagent_type": "medical-lit-reviewer",
         "model": "deepseek-v4-flash", "bucket": "deepseek", "result": "pass",
         "latency_ms": 1200, "tokens_in": 10, "tokens_out": 50},
        {"ts": 2.0, "type": "subagent_invoke", "subagent_type": "medical-lit-reviewer",
         "model": "deepseek-v4-flash", "bucket": "deepseek", "result": "pass",
         "latency_ms": 800, "tokens_in": 10, "tokens_out": 40},
        {"ts": 3.0, "type": "subagent_invoke", "subagent_type": "medical-lit-reviewer",
         "model": "deepseek-v4-flash", "bucket": "deepseek", "result": "fail",
         "latency_ms": 200, "tokens_in": 10, "tokens_out": 5},
    ])
    out = st.aggregate(log_file=log)
    assert out["total_invocations"] == 3
    sa = out["by_subagent"]["medical-lit-reviewer"]
    assert sa["count"] == 3
    assert sa["pass"] == 2
    assert sa["fail"] == 1
    assert abs(sa["pass_rate"] - 0.667) < 0.01


def test_aggregate_latency_percentiles(tmp_path):
    """p50 + p95 latency are computed from the latency_ms values."""
    log = tmp_path / "live-events.jsonl"
    latencies = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    events = [
        {"ts": float(i), "type": "subagent_invoke", "subagent_type": "x",
         "model": "m", "bucket": "b", "result": "pass", "latency_ms": l}
        for i, l in enumerate(latencies)
    ]
    _write_events(log, events)
    out = st.aggregate(log_file=log)
    sa = out["by_subagent"]["x"]
    # p50 of [100..1000] step 100 (10 values) → linear interp at idx 4.5 = 550
    assert sa["latency_p50_ms"] == 550
    assert sa["latency_p95_ms"] >= 900
    assert sa["latency_p95_ms"] <= 1000


def test_aggregate_by_bucket(tmp_path):
    """Invocations are grouped by rate-limit bucket too."""
    log = tmp_path / "live-events.jsonl"
    _write_events(log, [
        {"ts": 1.0, "type": "subagent_invoke", "subagent_type": "a",
         "model": "m1", "bucket": "deepseek", "result": "pass", "latency_ms": 100},
        {"ts": 2.0, "type": "subagent_invoke", "subagent_type": "b",
         "model": "m2", "bucket": "glm", "result": "fail", "latency_ms": 200},
        {"ts": 3.0, "type": "subagent_invoke", "subagent_type": "c",
         "model": "m3", "bucket": "deepseek", "result": "pass", "latency_ms": 150},
    ])
    out = st.aggregate(log_file=log)
    assert out["by_bucket"]["deepseek"]["count"] == 2
    assert out["by_bucket"]["deepseek"]["pass"] == 2
    assert out["by_bucket"]["glm"]["count"] == 1
    assert out["by_bucket"]["glm"]["fail"] == 1


def test_aggregate_ignores_non_subagent_events(tmp_path):
    """hook_check + delegate_done events must not pollute the count."""
    log = tmp_path / "live-events.jsonl"
    _write_events(log, [
        {"ts": 1.0, "type": "hook_check", "hook": "x", "result": "pass"},
        {"ts": 2.0, "type": "delegate_done", "model": "m", "duration_ms": 100},
        {"ts": 3.0, "type": "subagent_invoke", "subagent_type": "a",
         "model": "m", "bucket": "b", "result": "pass", "latency_ms": 50},
    ])
    out = st.aggregate(log_file=log)
    assert out["total_invocations"] == 1
    assert "a" in out["by_subagent"]


def test_aggregate_window_filters_old_events(tmp_path):
    """Events older than the window are excluded."""
    import time
    log = tmp_path / "live-events.jsonl"
    now = time.time()
    _write_events(log, [
        {"ts": now - 7200, "type": "subagent_invoke", "subagent_type": "old",
         "model": "m", "bucket": "b", "result": "pass", "latency_ms": 10},
        {"ts": now - 10, "type": "subagent_invoke", "subagent_type": "recent",
         "model": "m", "bucket": "b", "result": "pass", "latency_ms": 20},
    ])
    out = st.aggregate(log_file=log, window_seconds=3600)
    assert out["total_invocations"] == 1
    assert "recent" in out["by_subagent"]
    assert "old" not in out["by_subagent"]


def test_aggregate_model_leaderboard(tmp_path):
    """Each subagent's stat includes the models seen + which had best pass_rate."""
    log = tmp_path / "live-events.jsonl"
    _write_events(log, [
        {"ts": 1.0, "type": "subagent_invoke", "subagent_type": "x",
         "model": "glm-5.2", "bucket": "glm", "result": "pass", "latency_ms": 100},
        {"ts": 2.0, "type": "subagent_invoke", "subagent_type": "x",
         "model": "glm-5.2", "bucket": "glm", "result": "pass", "latency_ms": 120},
        {"ts": 3.0, "type": "subagent_invoke", "subagent_type": "x",
         "model": "deepseek-v4-flash", "bucket": "deepseek", "result": "fail", "latency_ms": 90},
    ])
    out = st.aggregate(log_file=log)
    sa = out["by_subagent"]["x"]
    assert "glm-5.2" in sa["models"]
    assert sa["best_model"] == "glm-5.2"  # 2/2 pass vs 0/1


def test_cli_summary_dry(tmp_path, capsys):
    """The CLI summary function renders a readable table without crashing."""
    log = tmp_path / "live-events.jsonl"
    _write_events(log, [
        {"ts": 1.0, "type": "subagent_invoke", "subagent_type": "a",
         "model": "m", "bucket": "b", "result": "pass", "latency_ms": 100,
         "tokens_out": 50},
    ])
    stats = st.aggregate(log_file=log)
    text = st.render_summary(stats)
    assert "a" in text
    assert "pass" in text.lower() or "100" in text
