"""
test_auto_synthesize.py — Coverage for scripts/wiki/auto-synthesize.py.

Tests state hash round-trip, source analysis, synthesis-status detection,
and the human-readable report. Does NOT call subprocess (run_synthesis /
run_index_rebuild) since those shell out to other scripts.
"""

from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_path = REPO_ROOT / "scripts" / "wiki" / "auto-synthesize.py"
_spec = importlib.util.spec_from_file_location("auto_synthesize", _path)
auto_synth_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(auto_synth_mod)


# ── Fixtures ───────────────────────────────────────────────────────────

def _make_source(domain_dir: Path, slug: str, quality: str = "seed") -> Path:
    """Write a minimal valid source file in a domain dir."""
    domain_dir.mkdir(parents=True, exist_ok=True)
    path = domain_dir / f"{slug}.md"
    path.write_text(
        f"# {slug.replace('-', ' ').title()}\n\n"
        f"> **Quality:** {quality}\n"
        f"> **Tags:** tag-a, tag-b\n\n"
        f"## Abstract\n\nBody content.\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point auto_synth_mod's globals at a temp repo."""
    monkeypatch.setattr(auto_synth_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(auto_synth_mod, "SOURCES_DIR", tmp_path / "wiki" / "sources")
    monkeypatch.setattr(auto_synth_mod, "SYNTHESIS_DIR", tmp_path / "wiki" / "synthesis")
    monkeypatch.setattr(auto_synth_mod, "STATE_FILE", tmp_path / ".auto-synthesize-state.json")
    return tmp_path


# ── State ──────────────────────────────────────────────────────────────

class TestState:
    def test_load_state_defaults_when_missing(self, isolated_repo: Path):
        state = auto_synth_mod.load_state()
        assert state["last_run"] is None
        assert state["source_counts"] == {}
        assert state["last_source_hashes"] == {}
        assert state["synthesis_timestamps"] == {}

    def test_save_then_load_roundtrip(self, isolated_repo: Path):
        original = {
            "last_run": None,
            "source_counts": {"iot": 3},
            "last_source_hashes": {"a.md": "abc"},
            "synthesis_timestamps": {"iot": "2026-05-25T10:00:00"},
        }
        auto_synth_mod.save_state(original)
        loaded = auto_synth_mod.load_state()
        # save_state sets last_run; everything else preserved
        assert loaded["source_counts"] == {"iot": 3}
        assert loaded["last_source_hashes"] == {"a.md": "abc"}
        assert loaded["synthesis_timestamps"] == {"iot": "2026-05-25T10:00:00"}
        assert loaded["last_run"] is not None

    def test_load_state_recovers_from_invalid_json(self, isolated_repo: Path):
        auto_synth_mod.STATE_FILE.write_text("{not valid json", encoding="utf-8")
        state = auto_synth_mod.load_state()
        # Falls back to defaults
        assert state["last_run"] is None


# ── File hashing ───────────────────────────────────────────────────────

class TestGetFileHash:
    def test_same_content_same_hash(self, tmp_path: Path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("content", encoding="utf-8")
        b.write_text("content", encoding="utf-8")
        assert auto_synth_mod.get_file_hash(a) == auto_synth_mod.get_file_hash(b)

    def test_different_content_different_hash(self, tmp_path: Path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("content one", encoding="utf-8")
        b.write_text("content two", encoding="utf-8")
        assert auto_synth_mod.get_file_hash(a) != auto_synth_mod.get_file_hash(b)


# ── analyze_sources ────────────────────────────────────────────────────

class TestAnalyzeSources:
    def test_empty_dir_returns_zero(self, isolated_repo: Path):
        result = auto_synth_mod.analyze_sources()
        assert result["total"] == 0
        assert result["new_files"] == []
        assert result["changed_files"] == []

    def test_counts_sources_by_domain(self, isolated_repo: Path):
        sources = isolated_repo / "wiki" / "sources"
        _make_source(sources / "iot", "lora")
        _make_source(sources / "iot", "mqtt")
        _make_source(sources / "env", "air-quality")

        result = auto_synth_mod.analyze_sources()
        assert result["total"] == 3
        assert len(result["by_domain"]["iot"]) == 2
        assert len(result["by_domain"]["env"]) == 1

    def test_first_scan_marks_files_as_new(self, isolated_repo: Path):
        _make_source(isolated_repo / "wiki" / "sources" / "iot", "lora")
        result = auto_synth_mod.analyze_sources()
        assert len(result["new_files"]) == 1
        assert result["new_files"][0]["domain"] == "iot"

    def test_quality_distribution(self, isolated_repo: Path):
        sources = isolated_repo / "wiki" / "sources"
        _make_source(sources / "iot", "a", quality="seed")
        _make_source(sources / "iot", "b", quality="curated")
        _make_source(sources / "iot", "c", quality="curated")

        result = auto_synth_mod.analyze_sources()
        assert result["quality_distribution"]["seed"] == 1
        assert result["quality_distribution"]["curated"] == 2


# ── check_synthesis_status ─────────────────────────────────────────────

class TestCheckSynthesisStatus:
    def test_insufficient_when_below_threshold(self, isolated_repo: Path):
        sources = isolated_repo / "wiki" / "sources"
        _make_source(sources / "iot", "only-one")  # < MIN_SOURCES_FOR_SYNTHESIS=2

        analysis = auto_synth_mod.analyze_sources()
        status = auto_synth_mod.check_synthesis_status(analysis)
        assert "iot" in status["insufficient"]
        assert "iot" not in status["needs_update"]

    def test_needs_update_when_synthesis_missing(self, isolated_repo: Path):
        sources = isolated_repo / "wiki" / "sources"
        _make_source(sources / "iot", "a")
        _make_source(sources / "iot", "b")

        analysis = auto_synth_mod.analyze_sources()
        status = auto_synth_mod.check_synthesis_status(analysis)
        assert "iot" in status["needs_update"]


# ── print_report ───────────────────────────────────────────────────────

class TestPrintReport:
    def test_runs_without_error(self, isolated_repo: Path, capsys):
        sources = isolated_repo / "wiki" / "sources"
        _make_source(sources / "iot", "a")
        _make_source(sources / "iot", "b")
        analysis = auto_synth_mod.analyze_sources()
        status = auto_synth_mod.check_synthesis_status(analysis)

        auto_synth_mod.print_report(analysis, status)
        captured = capsys.readouterr()
        assert "Auto-Synthesis Status Report" in captured.out
        assert "Total sources:  2" in captured.out
        assert "iot" in captured.out
