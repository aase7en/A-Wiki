"""
Tests for the central provider registry + generic adapter.

The registry (wiki/context/providers.json) is the single source of truth for
LLM providers. Adding a provider must be one entry — no new bash function.

Iron Law #1: these tests are written before the implementation.
Public-safe: the registry must never contain secret values, only env var NAMES.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PY = REPO_ROOT / "scripts" / "swarm" / "provider_registry.py"
PROVIDERS_JSON = REPO_ROOT / "wiki" / "context" / "providers.json"
ROSTER_CONF = REPO_ROOT / "wiki" / "context" / "model-roster.conf"


def _load_module():
    spec = importlib.util.spec_from_file_location("provider_registry", REGISTRY_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def reg():
    return _load_module()


# ── Registry file: public-safe + structural ───────────────────────────────

def test_providers_json_exists_and_parses():
    assert PROVIDERS_JSON.exists(), "wiki/context/providers.json must exist"
    data = json.loads(PROVIDERS_JSON.read_text(encoding="utf-8"))
    assert data.get("version") == 1
    assert "providers" in data
    for name in ("openrouter", "zai", "gemini", "groq", "deepseek", "anthropic"):
        assert name in data["providers"], f"missing provider {name}"


def test_registry_is_public_safe_no_secret_values():
    """Registry must hold env var NAMES, never a key value."""
    raw = PROVIDERS_JSON.read_text(encoding="utf-8")
    # No literal API-key shapes
    for needle in ("sk-or-", "sk-ant-", "AIza", "gsk_"):
        assert needle not in raw, f"registry leaks a key-like literal: {needle}"
    data = json.loads(raw)
    for name, p in data["providers"].items():
        assert "auth_env" in p, f"{name} missing auth_env"
        assert p["auth_env"].endswith("_KEY") or "KEY" in p["auth_env"], name
        assert "api_style" in p and p["api_style"] in ("openai", "gemini", "anthropic")


def test_zai_routes_via_openrouter_and_default_model_is_glm():
    data = json.loads(PROVIDERS_JSON.read_text(encoding="utf-8"))
    zai = data["providers"]["zai"]
    assert zai.get("via") == "openrouter"
    assert zai.get("default_model", "").startswith("z-ai/glm")


# ── build_request: one shape per api_style ─────────────────────────────────

def test_build_request_openai_style(reg):
    spec = reg.build_request(
        "openrouter", "z-ai/glm-4.6", "hello",
        env={"OPENROUTER_API_KEY": "sk-test-123"},
    )
    assert spec["url"].startswith("https://openrouter.ai")
    assert spec["headers"]["Authorization"] == "Bearer sk-test-123"
    assert spec["extractor"] == "openai"
    assert spec["body"]["model"] == "z-ai/glm-4.6"
    assert spec["body"]["messages"][0]["content"] == "hello"


def test_build_request_gemini_style(reg):
    spec = reg.build_request(
        "gemini", "gemini-2.5-flash", "hi",
        env={"GEMINI_API_KEY": "AIza-test"},
    )
    assert ":generateContent" in spec["url"]
    assert "key=AIza-test" in spec["url"]
    assert spec["extractor"] == "gemini"
    assert spec["body"]["contents"][0]["parts"][0]["text"] == "hi"


def test_build_request_anthropic_style(reg):
    spec = reg.build_request(
        "anthropic", "claude-haiku-4-5", "yo",
        env={"ANTHROPIC_API_KEY": "sk-ant-test"},
    )
    assert spec["headers"]["x-api-key"] == "sk-ant-test"
    assert spec["headers"]["anthropic-version"]
    assert spec["extractor"] == "anthropic"
    assert spec["body"]["max_tokens"] >= 1


# ── via resolution: Z.ai falls back to OpenRouter until ZAI_API_KEY exists ──

def test_resolve_transport_zai_via_openrouter_when_no_key(reg):
    name, conf = reg.resolve_transport("zai", env={})
    assert name == "openrouter"
    assert conf["api_style"] == "openai"


def test_resolve_transport_zai_direct_when_key_present(reg):
    name, conf = reg.resolve_transport("zai", env={"ZAI_API_KEY": "zk-1"})
    assert name == "zai"
    assert conf["endpoint"].startswith("https://api.z.ai")


def test_build_request_zai_uses_openrouter_endpoint_keeps_model(reg):
    spec = reg.build_request(
        "zai", "z-ai/glm-4.6", "ping",
        env={"OPENROUTER_API_KEY": "sk-or-x"},  # no ZAI key
    )
    assert spec["url"].startswith("https://openrouter.ai")
    assert spec["body"]["model"] == "z-ai/glm-4.6"
    assert spec["transport_provider"] == "openrouter"


# ── CLI: build redacts the key; list enabled ───────────────────────────────

def test_cli_build_redacts_key():
    env = dict(os.environ, OPENROUTER_API_KEY="sk-or-SECRETVALUE")
    result = subprocess.run(
        [sys.executable, str(REGISTRY_PY), "build", "openrouter", "z-ai/glm-4.6"],
        input="hello", capture_output=True, text=True, env=env, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "sk-or-SECRETVALUE" not in result.stdout
    spec = json.loads(result.stdout)
    assert spec["headers"]["Authorization"] in ("Bearer ***", "Bearer [redacted]")


def test_cli_list_enabled_json():
    result = subprocess.run(
        [sys.executable, str(REGISTRY_PY), "list", "--enabled", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    names = {p["name"] for p in json.loads(result.stdout)}
    assert "openrouter" in names
    # zai is disabled by default (routes via openrouter), so not in enabled list
    assert "zai" not in names


# ── Integration: roster + delegate wiring ──────────────────────────────────

def test_roster_includes_glm_via_openrouter():
    text = ROSTER_CONF.read_text(encoding="utf-8")
    assert "z-ai/glm-4.6" in text, "GLM-4.6 must be a roster candidate"


def test_delegate_swarm_wires_registry_adapter():
    text = (REPO_ROOT / "scripts" / "swarm" / "delegate.sh").read_text(encoding="utf-8")
    assert "provider_registry.py" in text
    assert "try_registry_model" in text
