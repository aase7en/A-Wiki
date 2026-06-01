"""Tests for the A-Wiki render-html skill (Iron Law #1: written before implementation).

Each surface adapter must:
  - emit a single self-contained HTML document
  - embed its source data losslessly (round-trips via the #awiki-data block)
  - expose a Copy-as-JSON control (round-trip back into the agent)
  - never let data break out of the <script> container
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import render       # noqa: E402
import parse_plan   # noqa: E402


def _load(name: str) -> dict:
    return json.loads((SKILL_ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def _embedded_data(html: str) -> dict:
    m = re.search(
        r'<script[^>]*id="awiki-data"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert m, "missing #awiki-data block"
    raw = m.group(1).replace("<\\/", "</")  # undo the breakout-escaping
    return json.loads(raw)


SURFACES = ["scouter", "report", "health", "plan", "pharmacy", "audit", "skills", "delivery"]


def test_registry_has_every_template():
    registry = json.loads((SKILL_ROOT / "registry.json").read_text(encoding="utf-8"))
    for surface, entry in registry["surfaces"].items():
        template = SKILL_ROOT / "templates" / entry["template"]
        assert template.is_file(), f"{surface}: template {entry['template']} missing"


@pytest.mark.parametrize("surface", SURFACES)
def test_renders_self_contained_document(surface):
    html = render.render(surface, _load(f"{surface}.json"))
    assert html.lstrip().lower().startswith("<!doctype html")
    assert "</html>" in html
    # No external network deps — fully self-contained artifact.
    assert "http://" not in html.split("<body")[0].replace("http://www.w3.org", "")


@pytest.mark.parametrize("surface", SURFACES)
def test_data_round_trips(surface):
    data = _load(f"{surface}.json")
    html = render.render(surface, data)
    assert _embedded_data(html) == data


@pytest.mark.parametrize("surface", SURFACES)
def test_has_copy_as_json_control(surface):
    html = render.render(surface, _load(f"{surface}.json"))
    assert 'id="awiki-copy"' in html


def test_data_cannot_break_out_of_script():
    # A malicious/embedded "</script>" in data must be neutralised.
    data = {"available_models": [], "note": "</script><script>alert(1)</script>"}
    html = render.render("scouter", data)
    block = re.search(r'id="awiki-data"[^>]*>(.*?)</script>', html, re.DOTALL).group(1)
    assert "</script>" not in block
    assert _embedded_data(html) == data


def test_unknown_surface_raises():
    with pytest.raises((KeyError, ValueError)):
        render.render("does-not-exist", {})


def test_graph_surface_renders_repo_graph():
    graph_path = REPO_ROOT / ".wiki-graph.json"
    if not graph_path.is_file():
        pytest.skip(".wiki-graph.json not built")
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    html = render.render("graph", data)
    assert html.lstrip().lower().startswith("<!doctype html")
    assert 'id="awiki-data"' in html


# ── parse-plan tests (written BEFORE parse_plan.py exists — Iron Law #1) ──────

# Plan files live in the global ~/.claude/plans/, not in the repo
_GLOBAL_PLANS = Path.home() / ".claude" / "plans"
PLAN_MD = _GLOBAL_PLANS / "a-wiki-parallel-gem.md"


def test_parse_plan_returns_required_keys():
    if not PLAN_MD.is_file():
        pytest.skip("plan file not present")
    data = parse_plan.parse(str(PLAN_MD))
    assert isinstance(data["title"], str) and data["title"]
    assert isinstance(data["sections"], list) and len(data["sections"]) >= 1
    assert isinstance(data["phases"], list)
    assert isinstance(data["verify_cmds"], list)
    assert data["generated_from"] == str(PLAN_MD)


def test_parse_plan_sections_have_heading_and_body():
    if not PLAN_MD.is_file():
        pytest.skip("plan file not present")
    data = parse_plan.parse(str(PLAN_MD))
    for sec in data["sections"]:
        assert "heading" in sec and sec["heading"]
        assert "body" in sec


def test_parse_plan_phases_have_id_name_detail_status():
    if not PLAN_MD.is_file():
        pytest.skip("plan file not present")
    data = parse_plan.parse(str(PLAN_MD))
    if not data["phases"]:
        pytest.skip("plan has no phases")
    for ph in data["phases"]:
        assert "id" in ph and "name" in ph and "detail" in ph
        assert ph["status"] == "pending"


def test_parse_plan_cli_outputs_valid_json():
    if not PLAN_MD.is_file():
        pytest.skip("plan file not present")
    result = subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "parse_plan.py"), str(PLAN_MD)],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    parsed = json.loads(result.stdout)
    assert "sections" in parsed


def test_plan_surface_renders_from_fixture():
    data = _load("plan.json")
    html = render.render("plan", data)
    assert html.lstrip().lower().startswith("<!doctype html")
    assert 'id="awiki-copy"' in html
    assert _embedded_data(html) == data


def test_plan_surface_has_reveal_animation_class():
    data = _load("plan.json")
    html = render.render("plan", data)
    assert 'class="reveal' in html or "reveal" in html


def test_plan_surface_has_phase_cards():
    data = _load("plan.json")
    html = render.render("plan", data)
    # Phase decision panel must be present
    assert "awiki-phase" in html or "phase-card" in html


# ── compare_delivery --json (written BEFORE the flag exists — Iron Law #1) ────

def test_compare_delivery_json_flag(tmp_path):
    """compare_delivery.py --json must emit the compare() dict as JSON, no text noise."""
    delivery = {
        "items": [
            {"seq": 1, "sch_code": "A1", "name": "Betadine 15ml", "qty": 1, "unit": "ขวด", "unit_price": 35},
            {"seq": 2, "sch_code": "A2", "name": "Paracetamol 500mg", "qty": 5, "unit": "เม็ด", "unit_price": 1},
        ]
    }
    dfile = tmp_path / "delivery.json"
    dfile.write_text(json.dumps(delivery, ensure_ascii=False), encoding="utf-8")

    script = REPO_ROOT / "scripts" / "compare_delivery.py"
    result = subprocess.run(
        [sys.executable, str(script), "--json", "--delivery", str(dfile)],
        input="betadine: 1\nparacetamol: 2\nzzzmissing: 3\n",
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    parsed = json.loads(result.stdout)  # must be clean JSON (no print noise)
    for key in ("received", "diff", "not_received", "extra"):
        assert key in parsed, f"missing key {key}"
