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
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import render  # noqa: E402  (path injected above)


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


SURFACES = ["scouter", "report", "health"]


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
