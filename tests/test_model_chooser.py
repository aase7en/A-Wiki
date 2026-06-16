"""
Tests for the model chooser: apply-model-selection.py + choose-model.py.

The chooser lets the user pin a primary (capable) + secondary (cheap) model.
Cost-first mapping: secondary serves L1 (search/lookup); primary serves L2/L3
(reason/scan). Iron Law #1 — tests precede implementation.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APPLY = REPO_ROOT / "scripts" / "apply-model-selection.py"
CHOOSE = REPO_ROOT / "scripts" / "choose-model.py"


def _catalog(path: Path):
    path.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-15",
                "providers": ["google", "z-ai"],
                "by_provider": {
                    "z-ai": {
                        "primary": [{"model_id": "z-ai/glm-4.6", "role": "primary", "tier_hint": "L4",
                                     "prompt_price": "0.0000006", "completion_price": "0.0000022", "context_length": 200000}],
                        "secondary": [{"model_id": "z-ai/glm-4.5-air", "role": "secondary", "tier_hint": "L2",
                                       "prompt_price": "0.0000002", "completion_price": "0.0000011", "context_length": 128000}],
                    },
                    "google": {
                        "primary": [],
                        "secondary": [{"model_id": "google/gemini-2.5-flash:free", "role": "secondary", "tier_hint": "L1",
                                       "prompt_price": "0", "completion_price": "0", "context_length": 1000000}],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def test_apply_selection_pins_roster_cost_first(tmp_path):
    roster = tmp_path / "model-roster.conf"
    roster.write_text('TIER1_PRIMARY="old/a"\nTIER2_PRIMARY="old/b"\nRACE_MODELS="x y"\n', encoding="utf-8")
    sel = tmp_path / "sel.json"
    sel.write_text(
        json.dumps({
            "primary": "z-ai/glm-4.6",
            "secondary": "google/gemini-2.5-flash:free",
            "race": ["z-ai/glm-4.6", "google/gemini-2.5-flash:free"],
        }),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(APPLY), "--in", str(sel), "--roster", str(roster), "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    text = roster.read_text(encoding="utf-8")
    assert 'TIER1_PRIMARY="google/gemini-2.5-flash:free"' in text   # secondary → cheap L1 lane
    assert 'TIER2_PRIMARY="z-ai/glm-4.6"' in text                   # primary → capable L2 lane
    assert "z-ai/glm-4.6" in text and "google/gemini-2.5-flash:free" in text  # race
    payload = json.loads(result.stdout)
    assert "TIER1_PRIMARY" in payload["changed"]


def test_apply_dry_run_does_not_write(tmp_path):
    roster = tmp_path / "model-roster.conf"
    original = 'TIER1_PRIMARY="keep/me"\n'
    roster.write_text(original, encoding="utf-8")
    sel = tmp_path / "sel.json"
    sel.write_text(json.dumps({"secondary": "google/gemini-2.5-flash:free"}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(APPLY), "--in", str(sel), "--roster", str(roster), "--dry-run"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert roster.read_text(encoding="utf-8") == original  # unchanged


def test_choose_list_prints_providers(tmp_path):
    cat = tmp_path / "catalog.json"
    _catalog(cat)
    result = subprocess.run(
        [sys.executable, str(CHOOSE), "--catalog", str(cat), "--list"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "z-ai" in result.stdout
    assert "glm-4.6" in result.stdout


def test_choose_build_selection_writes_json(tmp_path):
    cat = tmp_path / "catalog.json"
    _catalog(cat)
    out = tmp_path / "sel.json"
    result = subprocess.run(
        [sys.executable, str(CHOOSE), "--catalog", str(cat),
         "--primary", "z-ai/glm-4.6", "--secondary", "google/gemini-2.5-flash:free",
         "--out", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    sel = json.loads(out.read_text(encoding="utf-8"))
    assert sel["primary"] == "z-ai/glm-4.6"
    assert sel["secondary"] == "google/gemini-2.5-flash:free"
