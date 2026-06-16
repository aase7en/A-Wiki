"""
Tests for Live Dashboard event flow: event_logger + cost-tier model_active emit.

The dashboard must surface (a) what model the primary agent is on + its cost
tier, and (b) the planned model lanes (route_plan). Iron Law #1: tests first.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENT_LOGGER = REPO_ROOT / "scripts" / "live-dashboard" / "event_logger.py"
COST_HOOK = REPO_ROOT / "scripts" / "hooks" / "check_cost_tier.py"


def _event_logger_mod():
    spec = importlib.util.spec_from_file_location("event_logger", EVENT_LOGGER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_event_logger_appends_route_plan(tmp_path):
    mod = _event_logger_mod()
    mod.LOG_FILE = tmp_path / "live-events.jsonl"
    mod.log("route_plan", tier="L2", models="z-ai/glm-4.6 google/gemini-2.5-flash:free", parallelize="1")
    lines = (tmp_path / "live-events.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[-1])
    assert entry["type"] == "route_plan"
    assert entry["tier"] == "L2"
    assert "ts" in entry


def test_cost_tier_hook_emits_model_active(tmp_path):
    today = datetime.now().strftime("%Y-%m-%d")
    (tmp_path / f"cost-tier-{today}.txt").write_text("L4|implementation|test", encoding="utf-8")
    env = {
        **_clean_env(),
        "AWIKI_COST_GATE_TMP_DIR": str(tmp_path),
        "AWIKI_PRIMARY_MODEL": "claude-opus-4-8",
    }
    result = subprocess.run(
        [sys.executable, str(COST_HOOK)],
        input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "wiki/x.md"}}),
        capture_output=True, text=True, env=env, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    events_file = tmp_path / "live-events.jsonl"
    assert events_file.exists(), "model_active event not written"
    entries = [json.loads(l) for l in events_file.read_text(encoding="utf-8").splitlines()]
    active = [e for e in entries if e["type"] == "model_active"]
    assert active and active[-1]["tier"] == "L4"
    assert active[-1]["model"] == "claude-opus-4-8"


def _clean_env():
    import os

    env = dict(os.environ)
    env.pop("CI", None)
    env.pop("HOOK_SKIP", None)
    return env
