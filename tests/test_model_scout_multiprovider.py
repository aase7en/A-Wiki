"""
Tests for multi-provider scout + catalog classification.

Scout must scan models across providers (OpenRouter aggregates z-ai, anthropic,
google, deepseek, qwen, ...) and classify each into primary (flagship) vs
secondary (cheap/fast/free) so the chooser can serve "main + backup" per ค่าย.

Iron Law #1: tests precede implementation. Must NOT break the existing
recommendations/sources structure (test_model_router_policy covers that).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCOUT_PY = REPO_ROOT / "scripts" / "model-scout-current.py"


def _scout_mod():
    spec = importlib.util.spec_from_file_location("model_scout_current", SCOUT_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scout():
    return _scout_mod()


def _entry(model_id, name=None, prompt="0.000001", completion="0.000002", ctx=128000):
    return {
        "model_id": model_id,
        "name": name or model_id,
        "context_length": ctx,
        "prompt_price": prompt,
        "completion_price": completion,
    }


# ── classification ─────────────────────────────────────────────────────────

def test_classify_glm_46_is_primary(scout):
    out = scout.classify_model(_entry("z-ai/glm-4.6", "Z.AI: GLM 4.6", "0.0000006", "0.0000022"))
    assert out["role"] == "primary"
    assert out["tier_hint"] in ("L3", "L4")


def test_classify_glm_air_is_secondary(scout):
    out = scout.classify_model(_entry("z-ai/glm-4.5-air", "Z.AI: GLM 4.5 Air", "0.0000002", "0.0000011"))
    assert out["role"] == "secondary"


def test_classify_free_model_is_secondary_l1(scout):
    out = scout.classify_model(_entry("google/gemini-2.5-flash:free", "Gemini Flash (free)", "0", "0"))
    assert out["role"] == "secondary"
    assert out["tier_hint"] == "L1"


def test_classify_flagship_opus_is_primary(scout):
    out = scout.classify_model(_entry("anthropic/claude-opus-4", "Claude Opus", "0.000015", "0.000075"))
    assert out["role"] == "primary"
    assert out["tier_hint"] == "L4"


# ── catalog grouping ───────────────────────────────────────────────────────

def test_build_catalog_groups_by_provider_prefix(scout):
    openrouter = {
        "status": "ok",
        "all_candidates": [
            _entry("z-ai/glm-4.6", "GLM 4.6", "0.0000006", "0.0000022"),
            _entry("z-ai/glm-4.5-air", "GLM 4.5 Air", "0.0000002", "0.0000011"),
            _entry("anthropic/claude-opus-4", "Opus", "0.000015", "0.000075"),
            _entry("google/gemini-2.5-flash:free", "Gemini Flash free", "0", "0"),
            _entry("deepseek/deepseek-chat", "DeepSeek Chat", "0.0000003", "0.0000009"),
        ],
    }
    cat = scout.build_catalog(openrouter, None)
    assert "z-ai" in cat["by_provider"]
    assert "anthropic" in cat["by_provider"]
    assert "google" in cat["by_provider"]
    # GLM 4.6 should be in z-ai primary list
    zai_primary_ids = {m["model_id"] for m in cat["by_provider"]["z-ai"]["primary"]}
    assert "z-ai/glm-4.6" in zai_primary_ids
    zai_secondary_ids = {m["model_id"] for m in cat["by_provider"]["z-ai"]["secondary"]}
    assert "z-ai/glm-4.5-air" in zai_secondary_ids
    # flat models list carries provider + role on every entry
    assert all("provider" in m and "role" in m for m in cat["models"])


def test_build_catalog_offline_safe_empty(scout):
    cat = scout.build_catalog({"status": "skipped"}, None)
    assert cat["models"] == []
    assert cat["by_provider"] == {}


# ── end-to-end: offline scout still writes recommendations + adds catalog ───

def test_scout_offline_writes_catalog_and_keeps_recommendations(tmp_path):
    out = tmp_path / "scout.json"
    report = tmp_path / "scout.md"
    catalog = tmp_path / "catalog.json"
    result = subprocess.run(
        [
            sys.executable, str(SCOUT_PY), "--offline",
            "--out", str(out), "--report", str(report),
            "--catalog", str(catalog), "--json",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    # existing structure preserved
    assert data["recommendations"]["free-current"]["role"] == "free-current"
    assert "catalog" in data
    # separate catalog file written + valid
    cat = json.loads(catalog.read_text(encoding="utf-8"))
    assert "models" in cat and "by_provider" in cat and "generated_at" in cat
