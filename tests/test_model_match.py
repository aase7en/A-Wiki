"""
Tests for the task->tier->price matrix (cost-aware parallel selection).

Picks the cheapest model that fits the task tier, and only parallelizes when
it is actually worth it (latency-sensitive AND cheap/free lanes available) —
never paying 3x for trivial or expensive work. Iron Law #1: tests first.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MATCH_PY = REPO_ROOT / "scripts" / "model_match.py"


def _mod():
    spec = importlib.util.spec_from_file_location("model_match", MATCH_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mm():
    return _mod()


CATALOG = {
    "models": [
        {"model_id": "google/gemini-2.5-flash:free", "role": "secondary", "tier_hint": "L1", "prompt_price": "0", "completion_price": "0"},
        {"model_id": "deepseek/deepseek-chat-v3:free", "role": "secondary", "tier_hint": "L1", "prompt_price": "0", "completion_price": "0"},
        {"model_id": "z-ai/glm-4.5-air", "role": "secondary", "tier_hint": "L2", "prompt_price": "0.0000002", "completion_price": "0.0000011"},
        {"model_id": "z-ai/glm-4.6", "role": "primary", "tier_hint": "L4", "prompt_price": "0.0000006", "completion_price": "0.0000022"},
        {"model_id": "deepseek/deepseek-r1", "role": "primary", "tier_hint": "L4", "prompt_price": "0.00000055", "completion_price": "0.00000219"},
    ]
}


def test_reason_maps_to_l2(mm):
    d = mm.decide("reason", CATALOG)
    assert d["tier"] == "L2"
    assert d["primary"] == "z-ai/glm-4.5-air"  # cheapest L2-band model


def test_architect_maps_to_l4_primary(mm):
    d = mm.decide("architect", CATALOG)
    assert d["tier"] == "L4"
    assert d["primary"] in ("z-ai/glm-4.6", "deepseek/deepseek-r1")


def test_search_picks_a_free_model(mm):
    d = mm.decide("search", CATALOG)
    assert d["tier"] == "L1"
    assert d["primary"].endswith(":free")
    assert d["est_cost"].startswith("$0.0")


def test_parallelize_only_when_latency_and_cheap_lanes(mm):
    assert mm.decide("search", CATALOG, latency=False)["parallelize"] is False
    assert mm.decide("search", CATALOG, latency=True)["parallelize"] is True
    # expensive work must NOT fan out to 3 paid models just because it's latency-sensitive
    assert mm.decide("architect", CATALOG, latency=True)["parallelize"] is False


def test_parallelize_emits_race_models(mm):
    d = mm.decide("search", CATALOG, latency=True)
    assert len(d["race_models"]) >= 2
    assert all(m.endswith(":free") for m in d["race_models"])


def test_cli_outputs_json(mm, tmp_path):
    cat = tmp_path / "catalog.json"
    cat.write_text(json.dumps(CATALOG), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(MATCH_PY), "reason", "--catalog", str(cat), "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    d = json.loads(result.stdout)
    assert d["tier"] == "L2"
    assert "primary" in d and "parallelize" in d and "est_cost" in d
