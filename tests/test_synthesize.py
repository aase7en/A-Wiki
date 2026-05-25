"""
test_synthesize.py — Coverage for scripts/wiki/synthesize.py.

Tests parse_source, find_bridge_sources, generate_domain_synthesis,
generate_cross_domain_synthesis, and write_synthesis with rebuild semantics.
"""

from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_path = REPO_ROOT / "scripts" / "wiki" / "synthesize.py"
_spec = importlib.util.spec_from_file_location("synthesize", _path)
synthesize_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(synthesize_mod)


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_source_text() -> str:
    """A well-formed source markdown text."""
    return """# LoRaWAN Architecture

> **Type:** documentation
> **Domain:** iot
> **Ref:** https://example.com/lora
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** lora, lpwan, iot-protocol

## Abstract

LoRaWAN is a low-power wide-area network protocol.

## Key Concepts

- **Gateway** — Receives radio packets from end devices
- **Network Server** — Routes traffic between gateways and applications
- **End Device** — Battery-powered IoT sensor

---
"""


@pytest.fixture
def sources_two_domains() -> dict[str, list[dict[str, Any]]]:
    """Two domains, each with two parsed sources, sharing one concept."""
    return {
        "iot": [
            {
                "path": "wiki/sources/iot/lora.md",
                "title": "LoRa Basics",
                "type": "article",
                "abstract": "...",
                "concepts": [
                    {"name": "Edge Computing", "description": "On-device compute"},
                    {"name": "LoRa", "description": "Long-range radio"},
                ],
                "tags": ["iot", "lora"],
                "quality": "seed",
                "domain": "iot",
            },
            {
                "path": "wiki/sources/iot/mqtt.md",
                "title": "MQTT Protocol",
                "type": "article",
                "abstract": "...",
                "concepts": [
                    {"name": "Pub-Sub", "description": "Publish-subscribe pattern"},
                ],
                "tags": ["iot", "mqtt"],
                "quality": "seed",
                "domain": "iot",
            },
        ],
        "env": [
            {
                "path": "wiki/sources/env/aq.md",
                "title": "Air Quality",
                "type": "article",
                "abstract": "...",
                "concepts": [
                    {"name": "Edge Computing", "description": "Local sensor processing"},
                    {"name": "PM2.5", "description": "Particulate matter"},
                ],
                "tags": ["air-quality", "env"],
                "quality": "seed",
                "domain": "env",
            },
            {
                "path": "wiki/sources/env/water.md",
                "title": "Water Quality",
                "type": "article",
                "abstract": "...",
                "concepts": [
                    {"name": "Sensors", "description": "Measurement devices"},
                ],
                "tags": ["water", "env"],
                "quality": "seed",
                "domain": "env",
            },
        ],
    }


# ── parse_source ───────────────────────────────────────────────────────

class TestParseSource:
    def test_extracts_title(self, sample_source_text: str):
        parsed = synthesize_mod.parse_source(sample_source_text, "wiki/sources/iot/lora.md")
        assert parsed["title"] == "LoRaWAN Architecture"

    def test_extracts_metadata(self, sample_source_text: str):
        parsed = synthesize_mod.parse_source(sample_source_text, "wiki/sources/iot/lora.md")
        assert parsed["type"] == "documentation"
        assert parsed["domain"] == "iot"
        assert parsed["quality"] == "curated"
        assert "lora" in parsed["tags"]
        assert "lpwan" in parsed["tags"]

    def test_extracts_abstract(self, sample_source_text: str):
        parsed = synthesize_mod.parse_source(sample_source_text, "wiki/sources/iot/lora.md")
        assert "low-power wide-area network" in parsed["abstract"]

    def test_extracts_concepts(self, sample_source_text: str):
        parsed = synthesize_mod.parse_source(sample_source_text, "wiki/sources/iot/lora.md")
        names = [c["name"] for c in parsed["concepts"]]
        assert "Gateway" in names
        assert "Network Server" in names
        assert "End Device" in names

    def test_handles_minimal_input(self):
        parsed = synthesize_mod.parse_source("# Just A Title\n", "wiki/sources/x/y.md")
        assert parsed is not None
        assert parsed["title"] == "Just A Title"
        # Falls back to defaults
        assert parsed["domain"] == "general"
        assert parsed["concepts"] == []


# ── find_bridge_sources ────────────────────────────────────────────────

class TestFindBridgeSources:
    def test_returns_fallback_when_no_explicit_match(
        self, sources_two_domains: dict[str, list[dict[str, Any]]]
    ):
        bridges = synthesize_mod.find_bridge_sources("iot", "env", sources_two_domains)
        # No tag/title overlap → fallback to top 3 from each
        assert len(bridges) >= 1
        # Includes sources from both domains
        paths = {b["path"] for b in bridges}
        assert any("iot" in p for p in paths)
        assert any("env" in p for p in paths)


# ── generate_domain_synthesis ──────────────────────────────────────────

class TestGenerateDomainSynthesis:
    def test_empty_sources_returns_none(self):
        assert synthesize_mod.generate_domain_synthesis("iot", []) is None

    def test_renders_title_and_sources(
        self, sources_two_domains: dict[str, list[dict[str, Any]]]
    ):
        out = synthesize_mod.generate_domain_synthesis("iot", sources_two_domains["iot"])
        assert out is not None
        assert "# IoT — Knowledge Synthesis" in out
        # Each source must appear in the inventory table
        assert "LoRa Basics" in out
        assert "MQTT Protocol" in out

    def test_includes_concept_frequency_table(
        self, sources_two_domains: dict[str, list[dict[str, Any]]]
    ):
        out = synthesize_mod.generate_domain_synthesis("iot", sources_two_domains["iot"])
        assert "Key Concepts (by frequency)" in out
        assert "**Edge Computing**" in out  # appears in one IoT source


# ── generate_cross_domain_synthesis ────────────────────────────────────

class TestGenerateCrossDomainSynthesis:
    def test_empty_domain_returns_none(self, sources_two_domains):
        out = synthesize_mod.generate_cross_domain_synthesis(
            "iot", "missing-domain", "Topic", "Desc", sources_two_domains
        )
        assert out is None

    def test_detects_shared_concept(
        self, sources_two_domains: dict[str, list[dict[str, Any]]]
    ):
        out = synthesize_mod.generate_cross_domain_synthesis(
            "iot", "env", "IoT × Env", "Bridging IoT and environment", sources_two_domains
        )
        assert out is not None
        # "Edge Computing" is in both iot/lora.md and env/aq.md → must surface as overlap
        assert "Edge Computing" in out
        # Both domain titles appear in header
        assert "IoT" in out and "Environmental Health" in out


# ── write_synthesis ────────────────────────────────────────────────────

class TestWriteSynthesis:
    def test_writes_new_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(synthesize_mod, "REPO_ROOT", tmp_path)
        out_path = tmp_path / "wiki" / "synthesis" / "new.md"
        ok = synthesize_mod.write_synthesis(out_path, "content here", rebuild=False)
        assert ok is True
        assert out_path.read_text(encoding="utf-8") == "content here"

    def test_skips_existing_without_rebuild(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(synthesize_mod, "REPO_ROOT", tmp_path)
        out_path = tmp_path / "wiki" / "synthesis" / "existing.md"
        out_path.parent.mkdir(parents=True)
        out_path.write_text("original", encoding="utf-8")

        ok = synthesize_mod.write_synthesis(out_path, "new content", rebuild=False)
        assert ok is False
        assert out_path.read_text(encoding="utf-8") == "original"

    def test_overwrites_with_rebuild(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(synthesize_mod, "REPO_ROOT", tmp_path)
        out_path = tmp_path / "wiki" / "synthesis" / "existing.md"
        out_path.parent.mkdir(parents=True)
        out_path.write_text("original", encoding="utf-8")

        ok = synthesize_mod.write_synthesis(out_path, "new content", rebuild=True)
        assert ok is True
        assert out_path.read_text(encoding="utf-8") == "new content"
