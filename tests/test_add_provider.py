"""
Tests for the guided add-API-key flow (scripts/add-provider.py).

Public-safe contract (Iron Law #6 + secrets policy):
  - provider metadata (env var NAME, endpoint, api_style) goes into providers.json
  - the KEY VALUE goes ONLY into drive/.secrets — never the repo / registry
  - --dry-run writes nothing

Iron Law #1: tests precede implementation.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADD_PROVIDER = REPO_ROOT / "scripts" / "add-provider.py"


def _base_registry(path: Path):
    path.write_text(
        json.dumps({"version": 1, "providers": {
            "openrouter": {"label": "OpenRouter", "api_style": "openai", "enabled": True,
                           "endpoint": "https://openrouter.ai/api/v1/chat/completions",
                           "auth_env": "OPENROUTER_API_KEY"}
        }}),
        encoding="utf-8",
    )


def test_registers_provider_metadata_only(tmp_path):
    registry = tmp_path / "providers.json"
    _base_registry(registry)
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-existing\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ADD_PROVIDER),
         "--provider", "mistral", "--env-name", "MISTRAL_API_KEY",
         "--endpoint", "https://api.mistral.ai/v1/chat/completions",
         "--api-style", "openai", "--key", "sk-mistral-SECRET",
         "--registry", str(registry), "--secrets-file", str(secrets), "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    reg = json.loads(registry.read_text(encoding="utf-8"))
    assert "mistral" in reg["providers"]
    assert reg["providers"]["mistral"]["auth_env"] == "MISTRAL_API_KEY"
    # registry must hold the env NAME, never the value
    assert "sk-mistral-SECRET" not in registry.read_text(encoding="utf-8")


def test_key_value_written_to_secrets_only(tmp_path):
    registry = tmp_path / "providers.json"
    _base_registry(registry)
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-existing\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ADD_PROVIDER),
         "--provider", "mistral", "--env-name", "MISTRAL_API_KEY",
         "--endpoint", "https://api.mistral.ai/v1/chat/completions",
         "--key", "sk-mistral-SECRET",
         "--registry", str(registry), "--secrets-file", str(secrets)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    secrets_text = secrets.read_text(encoding="utf-8")
    assert "MISTRAL_API_KEY=sk-mistral-SECRET" in secrets_text
    assert "OPENROUTER_API_KEY=sk-or-existing" in secrets_text  # preserved


def test_dry_run_writes_nothing(tmp_path):
    registry = tmp_path / "providers.json"
    _base_registry(registry)
    before_reg = registry.read_text(encoding="utf-8")
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-existing\n", encoding="utf-8")
    before_sec = secrets.read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ADD_PROVIDER),
         "--provider", "mistral", "--env-name", "MISTRAL_API_KEY",
         "--endpoint", "https://api.mistral.ai/v1/chat/completions",
         "--key", "sk-mistral-SECRET", "--dry-run",
         "--registry", str(registry), "--secrets-file", str(secrets)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert registry.read_text(encoding="utf-8") == before_reg
    assert secrets.read_text(encoding="utf-8") == before_sec
    # output must not leak the secret value
    assert "sk-mistral-SECRET" not in result.stdout


def test_zai_enable_updates_existing_entry(tmp_path):
    registry = tmp_path / "providers.json"
    registry.write_text(
        json.dumps({"version": 1, "providers": {
            "zai": {"label": "Z.ai (GLM)", "api_style": "openai", "enabled": False,
                    "via": "openrouter", "endpoint": "https://api.z.ai/api/paas/v4/chat/completions",
                    "auth_env": "ZAI_API_KEY"}
        }}),
        encoding="utf-8",
    )
    secrets = tmp_path / ".secrets"
    secrets.write_text("", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ADD_PROVIDER),
         "--provider", "zai", "--env-name", "ZAI_API_KEY",
         "--key", "zk-real", "--enable",
         "--registry", str(registry), "--secrets-file", str(secrets)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    reg = json.loads(registry.read_text(encoding="utf-8"))
    assert reg["providers"]["zai"]["enabled"] is True
    # going direct is fine to leave `via` — resolver prefers direct once key exists
