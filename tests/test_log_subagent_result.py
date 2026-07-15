"""Tests for the Subagent Observatory PostToolUse hook (log_subagent_result.py).

Verifies the hook emits a `subagent_invoke` event to the live dashboard
log (.tmp/live-events.jsonl) with the right fields, for both success and
failure cases. Also exercises the pure helpers (bucket/model resolution,
event-field extraction) without touching the log.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import log_subagent_result as hook  # noqa: E402


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_is_error_response_detects_iserror_block():
    """A tool_response containing an iserror:true flag is an error."""
    resp = {"content": [{"type": "text", "text": "..."}], "iserror": True}
    assert hook.is_error_response(resp) is True


def test_is_error_response_detects_rate_limit_text():
    """Even without iserror, rate-limit / error keywords in text mark failure."""
    resp = "Provider rate limited the model request"
    assert hook.is_error_response(resp) is True
    resp2 = {"content": [{"type": "text", "text": "Error: something failed"}]}
    assert hook.is_error_response(resp2) is True


def test_is_error_response_passes_success():
    """A plain successful response is not an error."""
    assert hook.is_error_response("here is the analysis") is False
    assert hook.is_error_response({"content": [{"type": "text", "text": "ok"}]}) is False


def test_estimate_tokens_lower_bounded():
    """Token estimate must be >= 1 even for empty content (floor)."""
    assert hook.estimate_tokens("") >= 1
    assert hook.estimate_tokens("a" * 4000) >= 100  # ~4 chars/token
    assert hook.estimate_tokens(None) >= 1


def test_extract_subagent_type_from_tool_input():
    """subagent_type comes from tool_input.subagent_type (or subagentType)."""
    assert hook.extract_subagent_type({"subagent_type": "medical-lit-reviewer"}) == "medical-lit-reviewer"
    assert hook.extract_subagent_type({"subagentType": "Explore"}) == "Explore"
    assert hook.extract_subagent_type({}) == ""


# ---------------------------------------------------------------------------
# Event emission — uses a temp log file to avoid polluting the real one
# ---------------------------------------------------------------------------

def _run_hook_with_input(input_data: dict, log_file: Path) -> int:
    """Invoke the hook's main() against input_data, with LOG_FILE overridden."""
    hook.LOG_FILE = log_file
    hook.STATE_FILE = log_file.parent / "fanout_state.json"
    old_stdin = sys.stdin
    sys.stdin = type("S", (), {"read": lambda self: json.dumps(input_data)})()
    try:
        return hook.main()
    finally:
        sys.stdin = old_stdin


def test_hook_emits_subagent_invoke_event_on_success(tmp_path):
    """A successful Agent call → one subagent_invoke event with result=pass."""
    log_file = tmp_path / "live-events.jsonl"
    # Seed a matching PreToolUse start timestamp so latency can be computed.
    import time
    state = {"calls": [{"ts": time.time() - 1.2, "subagent_type": "Explore",
                        "model": "deepseek-v4-flash", "bucket": "deepseek"}]}
    hook.STATE_FILE = tmp_path / "fanout_state.json"
    hook.STATE_FILE.write_text(json.dumps(state))

    input_data = {
        "tool_name": "Agent",
        "tool_input": {"subagent_type": "Explore", "prompt": "find files"},
        "tool_response": "Found 5 files matching the query, here they are ...",
    }
    rc = _run_hook_with_input(input_data, log_file)
    assert rc == 0  # never blocks
    lines = [json.loads(l) for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    ev = lines[0]
    assert ev["type"] == "subagent_invoke"
    assert ev["subagent_type"] == "Explore"
    assert ev["result"] == "pass"
    assert ev["model"] == "deepseek-v4-flash"
    assert "latency_ms" in ev and ev["latency_ms"] >= 0
    assert "tokens_out" in ev and ev["tokens_out"] >= 1


def test_hook_emits_fail_on_rate_limit_error(tmp_path):
    """A tool_response containing 'rate limited' → result=fail."""
    log_file = tmp_path / "live-events.jsonl"
    input_data = {
        "tool_name": "Agent",
        "tool_input": {"subagent_type": "Explore"},
        "tool_response": {"content": [{"type": "text",
                          "text": "Provider rate limited the model request"}]},
    }
    rc = _run_hook_with_input(input_data, log_file)
    assert rc == 0
    ev = json.loads(log_file.read_text().strip())
    assert ev["result"] == "fail"
    assert ev["subagent_type"] == "Explore"


def test_hook_skips_non_agent_tools(tmp_path):
    """Only Agent-tool PostToolUse fires — a Bash call writes nothing."""
    log_file = tmp_path / "live-events.jsonl"
    rc = _run_hook_with_input(
        {"tool_name": "Bash", "tool_input": {"command": "ls"},
         "tool_response": "file1\nfile2"},
        log_file,
    )
    assert rc == 0
    assert not log_file.exists() or not log_file.read_text().strip()


def test_hook_never_blocks(tmp_path):
    """The hook must always exit 0 (observatory = measure, never block)."""
    log_file = tmp_path / "live-events.jsonl"
    # Even a catastrophic-looking input shouldn't block.
    rc = _run_hook_with_input({"tool_name": "Agent", "tool_response": {}}, log_file)
    assert rc == 0


# ---------------------------------------------------------------------------
# R4: A/B phase tagging
# ---------------------------------------------------------------------------
def test_ab_tag_returns_none_when_no_experiment(monkeypatch, tmp_path):
    """No active experiment → _ab_tag returns None (zero overhead)."""
    if not hook._AB_OK:
        import pytest
        pytest.skip("ab_routing not importable")
    # Point config + state at non-existent paths → load_experiments returns [].
    import ab_routing
    monkeypatch.setattr(ab_routing, "DEFAULT_CONFIG", tmp_path / "nope.json")
    monkeypatch.setattr(ab_routing, "DEFAULT_STATE", tmp_path / "nostate.json")
    tag = hook._ab_tag("any-subagent")
    assert tag is None


def test_ab_tag_returns_phase_when_active(monkeypatch, tmp_path):
    """An active experiment + matching state → _ab_tag returns {ab_phase, ab_model}."""
    if not hook._AB_OK:
        import pytest
        pytest.skip("ab_routing not importable")
    import ab_routing
    config = tmp_path / "ab-experiments.json"
    config.write_text(json.dumps({"experiments": [
        {"subagent": "test-agent", "champion": "model-a", "challenger": "model-b",
         "active": True, "phase_size": 10, "total_phases": 4}
    ]}), encoding="utf-8")
    state = tmp_path / "ab-state.json"
    state.write_text(json.dumps({"test-agent": {"current_phase": "B", "current_model": "model-b"}}),
                     encoding="utf-8")
    monkeypatch.setattr(ab_routing, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(ab_routing, "DEFAULT_STATE", state)
    tag = hook._ab_tag("test-agent")
    assert tag == {"ab_phase": "B", "ab_model": "model-b"}


def test_hook_emits_ab_phase_tag_when_active(monkeypatch, tmp_path):
    """End-to-end: when an active experiment targets the subagent, the emitted
    event includes ab_phase + ab_model fields."""
    if not hook._AB_OK:
        import pytest
        pytest.skip("ab_routing not importable")
    import ab_routing
    config = tmp_path / "ab-experiments.json"
    config.write_text(json.dumps({"experiments": [
        {"subagent": "test-agent", "champion": "model-a", "challenger": "model-b",
         "active": True, "phase_size": 10, "total_phases": 4}
    ]}), encoding="utf-8")
    state = tmp_path / "ab-state.json"
    state.write_text(json.dumps({"test-agent": {"current_phase": "A", "current_model": "model-a"}}),
                     encoding="utf-8")
    monkeypatch.setattr(ab_routing, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(ab_routing, "DEFAULT_STATE", state)

    log_file = tmp_path / "live-events.jsonl"
    hook.STATE_FILE = tmp_path / "fanout_state.json"
    input_data = {
        "tool_name": "Agent",
        "tool_input": {"subagent_type": "test-agent", "prompt": "do something"},
        "tool_response": {"content": [{"type": "text", "text": "done"}]},
    }
    rc = _run_hook_with_input(input_data, log_file)
    assert rc == 0
    events = [json.loads(l) for l in log_file.read_text().strip().split("\n") if l.strip()]
    assert len(events) == 1
    assert events[0]["ab_phase"] == "A"
    assert events[0]["ab_model"] == "model-a"


def test_hook_no_ab_tag_when_no_experiment(tmp_path):
    """When no experiment is active, the emitted event has NO ab_phase field."""
    if not hook._AB_OK:
        import pytest
        pytest.skip("ab_routing not importable")
    import ab_routing
    # Point at non-existent config → no experiments.
    monkeypatch_global = type("M", (), {"setattr": staticmethod(lambda *a: None)})()
    # Use the real tmp_path override approach:
    ab_routing.DEFAULT_CONFIG = tmp_path / "nope.json"
    ab_routing.DEFAULT_STATE = tmp_path / "nostate.json"
    try:
        log_file = tmp_path / "live-events.jsonl"
        hook.STATE_FILE = tmp_path / "fanout_state.json"
        input_data = {
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "some-agent", "prompt": "do something"},
            "tool_response": {"content": [{"type": "text", "text": "done"}]},
        }
        rc = _run_hook_with_input(input_data, log_file)
        assert rc == 0
        events = [json.loads(l) for l in log_file.read_text().strip().split("\n") if l.strip()]
        assert len(events) == 1
        assert "ab_phase" not in events[0]  # zero overhead — no tag
    finally:
        # Restore defaults so other tests aren't affected.
        from pathlib import Path as _P
        ab_routing.DEFAULT_CONFIG = _P(hook.REPO_ROOT) / "agents" / "ab-experiments.json"
        ab_routing.DEFAULT_STATE = _P(hook.REPO_ROOT) / ".tmp" / "ab-experiment-state.json"
