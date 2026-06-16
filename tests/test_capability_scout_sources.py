"""Tests for model-capability-scout.py SOURCES registry + offline-first safety."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCOUT = REPO_ROOT / "scripts" / "model-capability-scout.py"
SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("model_capability_scout", SCOUT)
scout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scout)


def test_sources_registered():
    keys = set(scout.SOURCES.keys())
    for required in ("swe_bench", "terminal_bench", "nl2repobench",
                     "aider_polyglot", "livecodebench"):
        assert required in keys, f"missing benchmark source {required}"
        assert "url" in scout.SOURCES[required]
        assert scout.SOURCES[required]["url"].startswith("https://")


def test_sources_have_labels():
    for key, src in scout.SOURCES.items():
        assert "label" in src and src["label"], f"{key} missing label"


def test_build_cache_offline_safe():
    cache = scout.build_cache(offline=True, timeout=1)
    assert "families" in cache
    for status in cache.get("sources_status", {}).values():
        assert status["status"] in ("skipped-offline", "skipped", "error", "unparseable", "ok")
    # offline must never mark any source as 'ok' (no network attempted)
    for status in cache.get("sources_status", {}).values():
        assert status["status"] != "ok"


def test_build_cache_never_raises_on_bad_scorecard(tmp_path):
    bad = tmp_path / "nope.json"
    bad.write_text("{not json", encoding="utf-8")
    original = scout.SCORECARD
    scout.SCORECARD = bad
    try:
        cache = scout.build_cache(offline=True, timeout=1)
        assert "families" in cache
    finally:
        scout.SCORECARD = original


def test_scorecard_has_new_source_urls():
    data = json.loads(SCORECARD.read_text(encoding="utf-8"))
    urls = data.get("source_urls", {})
    for required in ("aider_polyglot", "livecodebench"):
        assert required in urls, f"scorecard source_urls missing {required}"
