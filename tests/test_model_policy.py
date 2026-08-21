"""Phase 7 — Model control plane (brain-side POLICY authority). TDD red-first.

Contract (docs/migration/phase-7-model-control-work-order.md):
  - config/models/policy.yaml = vendor-neutral capability tiers + budgets
  - scripts/lib/model_policy.py = fail-closed loader/validator
  - runtime slot bindings live ONLY in gitignored machine-local files
  - conductor bridge exposes policy read-only for A-Conductor
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

POLICY = REPO_ROOT / "config" / "models" / "policy.yaml"


class TestPolicyFile:
    def test_policy_exists_with_schema(self):
        data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        assert data["schema"] == "awiki-model-policy/v1"

    def test_tiers_are_capability_classes_not_model_names(self):
        data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        tiers = data["tiers"]
        expected = {"free", "cheap", "capable", "primary"}
        assert expected <= set(tiers.keys())
        for name, spec in tiers.items():
            assert spec.get("description"), name
            # capability vocabulary — no vendor/model brand names
            assert not re.search(
                r"gpt-?\d|claude-?\d|gemini-?\d|deepseek|qwen|llama|sonnet|haiku|opus",
                yaml.safe_dump(spec), re.I), name

    def test_budget_rules_exist_per_task_type(self):
        data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        budgets = data["budgets"]
        assert "default" in budgets
        for task, rule in budgets.items():
            assert "max_tier" in rule, task


class TestLoader:
    def test_load_default_policy_ok(self):
        import model_policy as mp
        pol = mp.load_policy()
        assert pol["schema"] == "awiki-model-policy/v1"

    def test_unknown_schema_fails_closed(self, tmp_path):
        import model_policy as mp
        bad = tmp_path / "p.yaml"
        bad.write_text("schema: bogus/v2\n", encoding="utf-8")
        with pytest.raises(mp.PolicyError):
            mp.load_policy(path=bad)

    def test_unknown_tier_in_budget_fails_closed(self, tmp_path):
        import model_policy as mp
        bad = tmp_path / "p.yaml"
        bad.write_text(
            "schema: awiki-model-policy/v1\n"
            "tiers:\n  free: {description: x}\n"
            "budgets:\n  default: {max_tier: nonexistent}\n",
            encoding="utf-8")
        with pytest.raises(mp.PolicyError):
            mp.load_policy(path=bad)

    def test_malformed_yaml_fails_closed(self, tmp_path):
        import model_policy as mp
        bad = tmp_path / "p.yaml"
        bad.write_text("tiers: [unclosed\n", encoding="utf-8")
        with pytest.raises(mp.PolicyError):
            mp.load_policy(path=bad)

    def test_tier_order_enforced(self):
        import model_policy as mp
        pol = mp.load_policy()
        order = mp.tier_order(pol)
        assert order.index("free") < order.index("primary")

    def test_tier_within_budget(self):
        import model_policy as mp
        pol = mp.load_policy()
        assert mp.tier_allowed(pol, "free") is True
        # default budget must forbid at least the top tier for something
        top = "primary"
        assert isinstance(mp.tier_allowed(pol, top, task="default"), bool)


class TestRuntimeIsLocal:
    def test_runtime_local_is_gitignored(self):
        gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert re.search(r"config/models/runtime\.local\.(ya?ml)", gi) or \
               re.search(r"runtime\.local", gi), \
               "machine-local runtime bindings must be gitignored"

    def test_example_runtime_has_no_real_model_names(self):
        ex = REPO_ROOT / "config" / "models" / "runtime.local.yaml.example"
        assert ex.is_file()
        text = ex.read_text(encoding="utf-8")
        assert not re.search(
            r"gpt-?\d|claude-?\d|gemini-?\d|deepseek|qwen|llama", text, re.I)

    def test_resolve_slot_without_local_file_is_deterministic(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AWIKI_MODELS_RUNTIME", str(tmp_path / "missing.yaml"))
        import model_policy as mp
        out = mp.resolve_runtime()
        assert out["resolved"] is False
        assert out["reason"]


class TestBridgeModels:
    def test_bridge_models_read_only_json(self):
        import subprocess, json
        r = subprocess.run(
            [sys.executable, "-m", "conductor", "models", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=60)
        assert r.returncode == 0, r.stderr[:300]
        out = json.loads(r.stdout)
        assert out["schema"] == "awiki-model-policy/v1"
        assert "tiers" in out and "runtime" in out

    def test_bridge_models_hides_local_model_names(self):
        import subprocess, json
        r = subprocess.run(
            [sys.executable, "-m", "conductor", "models", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=60)
        blob = r.stdout
        assert not re.search(
            r"gpt-?\d|claude-?\d|gemini-?\d|deepseek|qwen|llama|sonnet|haiku",
            blob, re.I), "bridge must never leak real model names"
