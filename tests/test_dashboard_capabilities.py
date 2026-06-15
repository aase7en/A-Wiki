"""Tests for the live-dashboard /api/capabilities endpoint logic."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = REPO_ROOT / "scripts" / "live-dashboard" / "server.py"


def _load_server():
    spec = importlib.util.spec_from_file_location("ld_server", SERVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_default_config_has_glm_zai_international():
    mod = _load_server()
    z = [m for m in mod.DEFAULT_MODEL_CONFIG["models"] if m["id"] == "zhipu"][0]
    assert z["model_id"] == "glm-4.6"
    assert "api.z.ai" in z["api_url"]
    assert z["enabled"] is False  # ships disabled until key added
    assert z["key_env"] == "ZHIPU_API_KEY"


def test_recommended_by_task_excludes_disabled(tmp_path, monkeypatch):
    mod = _load_server()
    # Point config at a temp file where GLM is disabled
    cfg = {"models": [
        {"id": "zhipu", "name": "GLM", "enabled": False, "provider": "zhipu",
         "key_env": "ZHIPU_API_KEY", "model_id": "glm-4.6"},
        {"id": "deepseek", "name": "DeepSeek V3", "enabled": True, "provider": "deepseek",
         "key_env": "DEEPSEEK_API_KEY", "model_id": "deepseek-chat"},
    ]}
    cfg_file = tmp_path / "model-config.json"
    cfg_file.write_text(json.dumps(cfg), "utf-8")
    monkeypatch.setattr(mod, "MODEL_CONFIG_FILE", cfg_file)

    rec = mod._recommended_by_task()
    # GLM (reasoning 80) is disabled → DeepSeek (75) must win reason
    assert rec["reason"]["id"] == "deepseek"


def test_recommended_by_task_picks_glm_when_enabled(tmp_path, monkeypatch):
    mod = _load_server()
    cfg = {"models": [
        {"id": "zhipu", "name": "GLM", "enabled": True, "provider": "zhipu",
         "key_env": "ZHIPU_API_KEY", "model_id": "glm-4.6"},
        {"id": "deepseek", "name": "DeepSeek V3", "enabled": True, "provider": "deepseek",
         "key_env": "DEEPSEEK_API_KEY", "model_id": "deepseek-chat"},
    ]}
    cfg_file = tmp_path / "model-config.json"
    cfg_file.write_text(json.dumps(cfg), "utf-8")
    monkeypatch.setattr(mod, "MODEL_CONFIG_FILE", cfg_file)

    rec = mod._recommended_by_task()
    assert rec["reason"]["id"] == "zhipu"  # GLM reasoning 80 > DeepSeek 75


def test_load_capabilities_returns_families():
    mod = _load_server()
    caps = mod._load_capabilities()
    assert "families" in caps
    assert "glm" in caps["families"]


def test_keys_status_never_returns_values(monkeypatch):
    mod = _load_server()
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-value")
    keys = mod._read_keys_status()
    names = {k["name"] for k in keys}
    assert "GEMINI_API_KEY" in names
    for k in keys:
        assert set(k.keys()) == {"name", "set"}  # only name + bool, never a value
        assert "super-secret-value" not in json.dumps(k)
