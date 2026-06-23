"""Tests for Hermes model priority routing.

Run: python -m pytest tests/test_model_routing.py -v
"""
import json
import os
import sys
from pathlib import Path

import pytest

POOL_DIR = Path(__file__).resolve().parents[1] / "scripts" / "hermes" / "model-pool"
sys.path.insert(0, str(POOL_DIR))

import importlib.util


def _load(modname, filename):
    spec = importlib.util.spec_from_file_location(modname, POOL_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cost_router_mod = _load("cost_router_mod", "cost-router.py")
fb_mod = _load("fb_mod", "model-fallback-router.py")


# ---------------------------------------------------------------------------
# cost-router
# ---------------------------------------------------------------------------

def test_cost_matrix_has_codeplan_tier():
    assert "zai-codeplan/glm-4.7" in cost_router_mod.COST_MATRIX
    assert "zai-codeplan/glm-5.2" in cost_router_mod.COST_MATRIX
    glm47 = cost_router_mod.COST_MATRIX["zai-codeplan/glm-4.7"]
    assert glm47["subscription"] is True
    assert glm47["priority"] == 1


def test_deepseek_default_priority():
    flash = cost_router_mod.COST_MATRIX["deepseek/deepseek-v4-flash"]
    assert flash["priority"] == 2
    assert flash["subscription"] is False


def test_zai_free_model_is_free():
    assert cost_router_mod.COST_MATRIX["zai/glm-4.7-flash"]["free"] is True
    assert cost_router_mod.COST_MATRIX["zai/glm-4.7-flash"]["priority"] == 3


def test_estimate_cost_unknown_model():
    est = cost_router_mod.estimate_cost("nope/none", 1000, 100)
    assert "error" in est


def test_estimate_cost_cached_ratio():
    est = cost_router_mod.estimate_cost("deepseek/deepseek-v4-flash", 10000, 2000, cached_ratio=0.5)
    assert est["cached_tokens"] == 5000
    assert est["total_cost"] > 0


def test_recommend_light_role_returns_deepseek_default():
    rec = cost_router_mod.recommend(10000, 2000, role="light")
    assert rec["recommended"] == "deepseek/deepseek-v4-flash"


def test_recommend_complex_role_prefers_codeplan():
    rec = cost_router_mod.recommend(10000, 2000, role="complex")
    assert rec["recommended"] == "zai-codeplan/glm-5.2"


def test_recommend_skips_blacklisted_provider(tmp_path, monkeypatch):
    # Point restrict path at a temp blacklist file
    fake_state = {"blacklisted_providers": {"zai-codeplan": {"reason": "test"}}, "schema_version": 1}
    tmp_restrict = tmp_path / "restrict-state.json"
    tmp_restrict.write_text(json.dumps(fake_state), encoding="utf-8")
    monkeypatch.setattr(cost_router_mod, "RESTRICT_PATH", str(tmp_restrict))

    rec = cost_router_mod.recommend(10000, 2000, role="complex")
    # codeplan blacklisted -> should NOT recommend any zai-codeplan model
    assert "zai-codeplan" not in [m.split("/", 1)[0] for m in
                                  [r["model"] for r in rec["all"]]]
    assert "zai-codeplan" in rec["blacklisted_providers"]


def test_recommend_exclude_subscription():
    rec = cost_router_mod.recommend(10000, 2000, role="complex", exclude_subscription=True)
    assert all(not r["subscription"] for r in rec["all"])


# ---------------------------------------------------------------------------
# fallback-router restrict logic
# ---------------------------------------------------------------------------

def test_is_restrict_status_403():
    assert fb_mod.is_restrict_status(403, "restricted") is True
    assert fb_mod.is_restrict_status(403, "") is True


def test_is_restrict_status_429_is_not_restrict():
    assert fb_mod.is_restrict_status(429, "rate limit") is False


def test_is_restrict_status_401_keyword():
    assert fb_mod.is_restrict_status(401, "use in unsupported tools") is True


def test_blacklist_provider_persists(tmp_path, monkeypatch):
    tmp_restrict = tmp_path / "restrict-state.json"
    monkeypatch.setattr(fb_mod, "RESTRICT_PATH", str(tmp_restrict))

    fb_mod.blacklist_provider("zai-codeplan", "test restrict")
    state = json.loads(tmp_restrict.read_text(encoding="utf-8"))
    assert "zai-codeplan" in state["blacklisted_providers"]
    assert state["blacklisted_providers"]["zai-codeplan"]["recovery"].startswith("manual")


def test_clear_blacklist_manual_recovery(tmp_path, monkeypatch):
    tmp_restrict = tmp_path / "restrict-state.json"
    tmp_restrict.write_text(json.dumps(
        {"blacklisted_providers": {"zai-codeplan": {"reason": "x"}}, "schema_version": 1}),
        encoding="utf-8")
    monkeypatch.setattr(fb_mod, "RESTRICT_PATH", str(tmp_restrict))

    fb_mod.clear_blacklist("zai-codeplan")
    state = json.loads(tmp_restrict.read_text(encoding="utf-8"))
    assert "zai-codeplan" not in state["blacklisted_providers"]


def test_handle_failure_restrict_blacklists_provider(tmp_path, monkeypatch):
    # Isolate all state files
    tmp_pool = tmp_path / "model-pool.json"
    tmp_pool.write_text(json.dumps({
        "providers": {
            "zai-codeplan": {"base_url": "http://x"},
            "deepseek": {"base_url": "http://y"},
        },
        "fallback_chain": {"text": ["zai-codeplan/glm-4.7", "deepseek/deepseek-v4-flash"]},
    }), encoding="utf-8")
    tmp_restrict = tmp_path / "restrict-state.json"
    tmp_restrict.write_text(json.dumps({"blacklisted_providers": {}, "schema_version": 1}), encoding="utf-8")
    tmp_cd = tmp_path / "rate-limit-state.json"
    tmp_cd.write_text(json.dumps({"cooldowns": {}}), encoding="utf-8")

    monkeypatch.setattr(fb_mod, "POOL_PATH", str(tmp_pool))
    monkeypatch.setattr(fb_mod, "RESTRICT_PATH", str(tmp_restrict))
    monkeypatch.setattr(fb_mod, "STATE_PATH", str(tmp_cd))
    monkeypatch.setattr(fb_mod, "update_hermes_aux_config", lambda *a, **k: False)
    monkeypatch.setattr(fb_mod, "notify_telegram", lambda *a, **k: False)

    nxt, base, msg, actions = fb_mod.handle_failure(
        "zai-codeplan/glm-4.7", "text", status_code=403, body="restricted")
    assert any("BLACKLISTED" in a for a in actions)
    assert nxt == "deepseek/deepseek-v4-flash"

    state = json.loads(tmp_restrict.read_text(encoding="utf-8"))
    assert "zai-codeplan" in state["blacklisted_providers"]


def test_handle_failure_rate_limit_cooldowns_model(tmp_path, monkeypatch):
    tmp_pool = tmp_path / "model-pool.json"
    tmp_pool.write_text(json.dumps({
        "providers": {
            "zai-codeplan": {"base_url": "http://x"},
            "deepseek": {"base_url": "http://y"},
        },
        "fallback_chain": {"text": ["zai-codeplan/glm-4.7", "deepseek/deepseek-v4-flash"]},
    }), encoding="utf-8")
    tmp_restrict = tmp_path / "restrict-state.json"
    tmp_restrict.write_text(json.dumps({"blacklisted_providers": {}, "schema_version": 1}), encoding="utf-8")
    tmp_cd = tmp_path / "rate-limit-state.json"
    tmp_cd.write_text(json.dumps({"cooldowns": {}}), encoding="utf-8")

    monkeypatch.setattr(fb_mod, "POOL_PATH", str(tmp_pool))
    monkeypatch.setattr(fb_mod, "RESTRICT_PATH", str(tmp_restrict))
    monkeypatch.setattr(fb_mod, "STATE_PATH", str(tmp_cd))
    monkeypatch.setattr(fb_mod, "update_hermes_aux_config", lambda *a, **k: False)
    monkeypatch.setattr(fb_mod, "notify_telegram", lambda *a, **k: False)

    nxt, base, msg, actions = fb_mod.handle_failure(
        "zai-codeplan/glm-4.7", "text", status_code=429, body="rate limit")
    assert any("cooled" in a for a in actions)
    assert nxt == "deepseek/deepseek-v4-flash"
    # 429 must NOT blacklist provider
    state = json.loads(tmp_restrict.read_text(encoding="utf-8"))
    assert "zai-codeplan" not in state["blacklisted_providers"]


# ---------------------------------------------------------------------------
# JSON validity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", [
    "model-pool.json",
    "model-priority-config.json",
    "restrict-state.json",
])
def test_json_files_valid(fname):
    path = POOL_DIR / fname
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
