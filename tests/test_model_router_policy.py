from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "model-router-policy.py"


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
    source_result = subprocess.run(
        ["bash", "-c", f"source {out}; printf '%s' \"$MODEL_INTEL_SUMMARY\""],
        capture_output=True,
        text=True,
        check=False,
    )
    assert source_result.returncode == 0, source_result.stderr
    assert source_result.stdout == "Summary with `command` and $(subshell) text."


def test_delegate_loads_router_policy_before_roster():
    text = (REPO_ROOT / "scripts" / "swarm" / "delegate.sh").read_text(encoding="utf-8")

    assert "model-router-policy.py" in text
    assert "MODEL_ROUTER_POLICY_CONF" in text
    assert "source \"$POLICY_CONF\"" in text


def test_refresh_scripts_regenerate_router_policy():
    roster_script = (REPO_ROOT / "scripts" / "update-model-roster.sh").read_text(encoding="utf-8")
    intel_script = (REPO_ROOT / "scripts" / "update-ai-model-intel.sh").read_text(encoding="utf-8")

    assert "model-router-policy.py" in roster_script
    assert "model-router-policy.py" in intel_script
