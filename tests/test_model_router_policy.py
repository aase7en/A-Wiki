from __future__ import annotations

import configparser
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "model-router-policy.py"
SCOUT_SCRIPT = REPO_ROOT / "scripts" / "model-scout-current.py"


def test_policy_generator_merges_roster_and_intel_cache(tmp_path):
    roster = tmp_path / "model-roster.conf"
    roster.write_text(
        '\n'.join(
            [
                'TIER1_PRIMARY="model/free-chat:free"',
                'TIER1_FALLBACK1="model/free-fallback:free"',
                'TIER2_PRIMARY="model/free-reasoner:free"',
                'TIER3_PRIMARY="model/free-long:free"',
                'RACE_MODELS="model/free-chat:free model/free-reasoner:free"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    intel = tmp_path / "latest.md"
    intel.write_text(
        "# AI Model Intel Cache\n\nGemini Flash is useful for cheap routing.\n",
        encoding="utf-8",
    )
    out = tmp_path / "policy.conf"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--roster",
            str(roster),
            "--intel",
            str(intel),
            "--scout",
            str(tmp_path / "missing-scout.json"),  # hermetic: never read repo .tmp
            "--out",
            str(out),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["policy_path"] == str(out)
    assert payload["intel_available"] is True
    text = out.read_text(encoding="utf-8")
    assert "TIER1_PRIMARY=model/free-chat:free" in text
    assert "TIER2_PRIMARY=model/free-reasoner:free" in text
    assert "MODEL_ROUTER_POLICY_SOURCE=model-roster+model-intel" in text
    assert "MODEL_INTEL_AVAILABLE=1" in text
    assert "Gemini Flash" in text


def test_policy_generator_falls_back_without_intel(tmp_path):
    roster = tmp_path / "model-roster.conf"
    roster.write_text('TIER1_PRIMARY="model/free-chat:free"\n', encoding="utf-8")
    out = tmp_path / "policy.conf"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--roster",
            str(roster),
            "--intel",
            str(tmp_path / "missing.md"),
            "--scout",
            str(tmp_path / "missing-scout.json"),  # hermetic: never read repo .tmp
            "--out",
            str(out),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["intel_available"] is False
    text = out.read_text(encoding="utf-8")
    assert "MODEL_INTEL_AVAILABLE=0" in text
    assert "TIER1_PRIMARY=model/free-chat:free" in text


def test_policy_generator_escapes_shell_active_intel_summary(tmp_path):
    roster = tmp_path / "model-roster.conf"
    roster.write_text('TIER1_PRIMARY="model/free-chat:free"\n', encoding="utf-8")
    intel = tmp_path / "latest.md"
    intel.write_text("Summary with `command` and $(subshell) text.\n", encoding="utf-8")
    out = tmp_path / "policy.conf"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--roster",
            str(roster),
            "--intel",
            str(intel),
            "--out",
            str(out),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    # Quote the path: unquoted backslashes in Windows temp paths get eaten
    # by bash, making `source` a silent no-op (empty vars, rc 0).
    source_result = subprocess.run(
        ["bash", "-c", f'source "{out}"; printf \'%s\' "$MODEL_INTEL_SUMMARY"'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert source_result.returncode == 0, source_result.stderr
    assert source_result.stdout == "Summary with `command` and $(subshell) text."


def test_delegate_loads_router_policy_before_roster():
    text = (REPO_ROOT / "scripts" / "swarm" / "delegate.sh").read_text(encoding="utf-8")

    assert "model-router-policy.py" in text
    assert "model-scout-current.py" in text
    assert "MODEL_ROUTER_POLICY_CONF" in text
    assert "MODEL_SCOUT_CURRENT_JSON" in text
    assert "source \"$POLICY_CONF\"" in text


def test_refresh_scripts_regenerate_router_policy():
    roster_script = (REPO_ROOT / "scripts" / "update-model-roster.sh").read_text(encoding="utf-8")
    intel_script = (REPO_ROOT / "scripts" / "update-ai-model-intel.sh").read_text(encoding="utf-8")

    assert "model-router-policy.py" in roster_script
    assert "model-router-policy.py" in intel_script


def test_cost_routing_conf_documents_primary_model_ladder():
    config = configparser.ConfigParser()
    config.read(REPO_ROOT / "wiki" / "context" / "cost-routing.conf", encoding="utf-8")

    required_keys = {
        "provider",
        "model",
        "mode",
        "secret_name",
        "price_input_per_mtok",
        "price_output_per_mtok",
        "cache_read_multiplier",
        "cache_write_5m_multiplier",
        "cache_write_1h_multiplier",
        "note",
    }
    for section in ("tier_4a", "tier_4b", "tier_4c"):
        assert section in config
        assert required_keys <= set(config[section])
        assert "primary-agent only" in config[section]["note"]
        assert "harness must not call" in config[section]["note"]


def test_cost_routing_conf_labels_fixed_model_ids_as_seed_only():
    config = configparser.ConfigParser()
    config.read(REPO_ROOT / "wiki" / "context" / "cost-routing.conf", encoding="utf-8")

    assert "scout" in config
    assert config["scout"]["enabled"] == "true"
    assert config["scout"]["cache_path"] == ".tmp/model-scout-current.json"

    for section in ("tier_0", "tier_1", "tier_2", "tier_3"):
        values = config[section]
        assert values.get("seed_only") == "true", section
        assert "seed only; replaced by scout" in values.get("note", ""), section


def test_policy_generator_accepts_dynamic_scout_output(tmp_path):
    roster = tmp_path / "model-roster.conf"
    roster.write_text('TIER1_PRIMARY="seed/free:free"\n', encoding="utf-8")
    scout = tmp_path / "model-scout-current.json"
    scout.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-12T10:00:00+07:00",
                "recommendations": {
                    "free-current": {"model_id": "dynamic/free:free", "provider": "openrouter"},
                    "cheap-capable": {"model_id": "dynamic/cheap", "provider": "deepseek"},
                    "platform-low-scout": {"provider": "codex", "model_alias": "current-low-default"},
                },
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "policy.conf"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--roster",
            str(roster),
            "--scout",
            str(scout),
            "--out",
            str(out),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["scout_available"] is True
    text = out.read_text(encoding="utf-8")
    assert "MODEL_ROUTER_POLICY_SOURCE=model-roster+model-intel+current-scout" in text
    assert "MODEL_SCOUT_AVAILABLE=1" in text
    assert "MODEL_SCOUT_GENERATED_AT=2026-06-12T10:00:00+07:00" in text
    assert "TIER1_PRIMARY=dynamic/free:free" in text
    assert "TIER2_PRIMARY=dynamic/cheap" in text
    assert "MODEL_PLATFORM_LOW_SCOUT=codex:current-low-default" in text


def test_model_scout_current_offline_generates_policy_inputs(tmp_path):
    out = tmp_path / "model-scout-current.json"
    report = tmp_path / "model-scout-current.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "--offline",
            "--out",
            str(out),
            "--report",
            str(report),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert payload["scout_path"] == str(out)
    assert data["volatile"] is True
    assert data["generated_at"]
    assert data["recommendations"]["free-current"]["role"] == "free-current"
    assert data["recommendations"]["cheap-capable"]["role"] == "cheap-capable"
    assert data["recommendations"]["platform-low-scout"]["role"] == "platform-low-scout"
    assert data["recommendations"]["platform-primary"]["role"] == "platform-primary"
    source_urls = {source["url"] for source in data["sources"]}
    assert "https://openrouter.ai/docs/api/api-reference/models/get-models" in source_urls
    assert "https://api-docs.deepseek.com/quick_start/pricing" in source_urls
    assert "https://api-docs.deepseek.com/news/news260424" in source_urls
    assert "https://openrouter.ai/docs/guides/overview/models" in source_urls
    assert "DeepSeek V4 Flash" in report.read_text(encoding="utf-8")


def test_delegate_triggers_scout_refresh_for_stale_models():
    for path in ("scripts/delegate.sh", "scripts/swarm/delegate.sh"):
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert "refresh_model_scout" in text, path
        assert "MODEL_NOT_FOUND" in text, path
        assert "model-scout-current.py" in text, path
        assert "seed only; replaced by scout" in text, path
