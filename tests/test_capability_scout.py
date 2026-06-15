"""Tests for the offline-first model-capability-scout."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCOUT = REPO_ROOT / "scripts" / "model-capability-scout.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("capability_scout", SCOUT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_offline_uses_committed_scores():
    mod = _load_module()
    cache = mod.build_cache(offline=True, timeout=1)
    committed = mod.load_scorecard()
    # glm reasoning must equal the committed value (no network overlay)
    assert cache["families"]["glm"]["reasoning"] == committed["families"]["glm"]["reasoning"]
    assert cache["offline"] is True
    for status in cache["sources_status"].values():
        assert status["status"] == "skipped-offline"


def test_bad_source_degrades_to_committed(monkeypatch):
    mod = _load_module()

    def boom(url, timeout):
        raise OSError("network down")

    monkeypatch.setattr(mod, "fetch_text", boom)
    cache = mod.build_cache(offline=False, timeout=1)
    committed = mod.load_scorecard()
    # All sources errored → committed values intact
    assert cache["families"]["glm"]["swe_bench"] == committed["families"]["glm"]["swe_bench"]
    for status in cache["sources_status"].values():
        assert status["status"] == "error"


def test_partial_merge_keeps_other_dimensions(monkeypatch):
    mod = _load_module()
    committed = mod.load_scorecard()
    orig_reasoning = committed["families"]["glm"]["reasoning"]

    # Return a markdown table that only updates swe_bench for glm
    def fake_fetch(url, timeout):
        if "swebench" in url:
            return "| GLM-4.6 | foo | 99 |\n"
        raise OSError("skip others")

    monkeypatch.setattr(mod, "fetch_text", fake_fetch)
    cache = mod.build_cache(offline=False, timeout=1)
    glm = cache["families"]["glm"]
    assert glm["swe_bench"] == 99, "swe_bench should be overlaid from source"
    assert glm["reasoning"] == orig_reasoning, "reasoning must be untouched"


def test_writes_cache_and_exits_zero(tmp_path):
    mod = _load_module()
    out = tmp_path / "cap-cache.json"
    rc = _run_main(mod, ["--offline", "--out", str(out), "--quiet"])
    assert rc == 0
    data = json.loads(out.read_text("utf-8"))
    assert "families" in data and "glm" in data["families"]


def _run_main(mod, argv):
    import sys
    old = sys.argv
    sys.argv = ["model-capability-scout.py"] + argv
    try:
        return mod.main()
    finally:
        sys.argv = old


def test_parse_markdown_scores_robust_to_no_table():
    mod = _load_module()
    fams = mod.load_scorecard()["families"]
    # Garbage with no table rows → empty dict, never raises
    assert mod._parse_markdown_scores("swe_bench", fams, "no tables here\njust prose") == {}
