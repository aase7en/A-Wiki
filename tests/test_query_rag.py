"""
test_query_rag.py — Coverage for scripts/wiki/query-rag.py pure helpers.

Avoids FAISS / sentence-transformers (would download ~80MB model and slow CI).
Tests parse_doc_frontmatter, load_all_documents (via monkeypatched dirs),
generate_query_variants, format_results, format_json.
"""

from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_path = REPO_ROOT / "scripts" / "wiki" / "query-rag.py"
_spec = importlib.util.spec_from_file_location("query_rag", _path)
query_rag_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(query_rag_mod)


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def source_doc_text() -> str:
    return """# MQTT Protocol Overview

> **Type:** documentation
> **Domain:** iot
> **Quality:** curated
> **Tags:** mqtt, pub-sub, iot-protocol

## Abstract

MQTT is a lightweight publish-subscribe network protocol.

## Key Concepts

- **Broker** — Routes messages between publishers and subscribers
- **Topic** — Hierarchical channel for message routing
"""


@pytest.fixture
def synthesis_doc_text() -> str:
    return """# IoT Network Infrastructure

> **Domain:** synthesis
> **Generated:** 2026-05-25
> **Sources:** 5

## Overview

A cross-domain synthesis of IoT networking concepts.

- **Edge Computing** — Local processing on sensor devices
"""


# ── parse_doc_frontmatter ──────────────────────────────────────────────

class TestParseDocFrontmatter:
    def test_extracts_title(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert doc["title"] == "MQTT Protocol Overview"

    def test_extracts_domain_and_quality(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert doc["domain"] == "iot"
        assert doc["quality"] == "curated"

    def test_lowercases_and_splits_tags(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert "mqtt" in doc["tags"]
        assert "pub-sub" in doc["tags"]
        assert "iot-protocol" in doc["tags"]
        # All lowercased
        assert all(t == t.lower() for t in doc["tags"])

    def test_extracts_concepts(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert "Broker" in doc["concepts"]
        assert "Topic" in doc["concepts"]

    def test_preserves_doc_type(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert doc["type"] == "source"
        doc2 = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "synthesis")
        assert doc2["type"] == "synthesis"

    def test_strips_metadata_from_content(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        # Body should not contain the blockquote metadata header lines
        assert "**Domain:**" not in doc["content"]
        # But should still contain abstract body
        assert "lightweight" in doc["content"]

    def test_records_content_length(self, source_doc_text: str):
        doc = query_rag_mod.parse_doc_frontmatter(source_doc_text, "x.md", "source")
        assert doc["content_len"] > 0
        assert doc["content_len"] == len(doc["content"])


# ── load_all_documents ─────────────────────────────────────────────────

class TestLoadAllDocuments:
    def test_empty_dirs_returns_empty_list(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(query_rag_mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(query_rag_mod, "SOURCES_DIR", tmp_path / "wiki" / "sources")
        monkeypatch.setattr(query_rag_mod, "SYNTHESIS_DIR", tmp_path / "wiki" / "synthesis")
        docs = query_rag_mod.load_all_documents()
        assert docs == []

    def test_loads_sources_and_syntheses(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        source_doc_text: str,
        synthesis_doc_text: str,
    ):
        sources_dir = tmp_path / "wiki" / "sources"
        synthesis_dir = tmp_path / "wiki" / "synthesis"
        (sources_dir / "iot").mkdir(parents=True)
        (sources_dir / "iot" / "mqtt.md").write_text(source_doc_text, encoding="utf-8")
        synthesis_dir.mkdir(parents=True)
        (synthesis_dir / "iot-network.md").write_text(synthesis_doc_text, encoding="utf-8")

        monkeypatch.setattr(query_rag_mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(query_rag_mod, "SOURCES_DIR", sources_dir)
        monkeypatch.setattr(query_rag_mod, "SYNTHESIS_DIR", synthesis_dir)

        docs = query_rag_mod.load_all_documents()
        assert len(docs) == 2
        types = {d["type"] for d in docs}
        assert types == {"source", "synthesis"}


# ── generate_query_variants ────────────────────────────────────────────

class TestGenerateQueryVariants:
    def test_includes_original_query(self):
        variants = query_rag_mod.generate_query_variants("MQTT vs LoRaWAN")
        assert "MQTT vs LoRaWAN" in variants

    def test_returns_capped_list(self):
        variants = query_rag_mod.generate_query_variants("test")
        assert len(variants) <= 5
        assert len(variants) >= 2  # original + at least one rewrite

    def test_adds_prefix_variants(self):
        variants = query_rag_mod.generate_query_variants("edge ML")
        joined = " || ".join(variants)
        # At least one prefix variant should appear
        assert any(p in joined for p in ["Explain", "What is", "Compare and contrast", "Describe"])

    def test_skips_redundant_prefix(self):
        variants = query_rag_mod.generate_query_variants("Explain MQTT")
        # Should not produce "Explain Explain MQTT"
        assert not any(v.startswith("Explain Explain") for v in variants)


# ── format_results ─────────────────────────────────────────────────────

class TestFormatResults:
    def test_empty_results(self):
        assert query_rag_mod.format_results([]) == "No results found."

    def test_renders_result_fields(self):
        results = [{
            "rank": 1,
            "score": 0.85,
            "title": "MQTT Overview",
            "path": "wiki/sources/iot/mqtt.md",
            "type": "source",
            "domain": "iot",
            "tags": ["mqtt", "pub-sub"],
            "concepts": ["Broker", "Topic"],
            "quality": "curated",
            "content_len": 1234,
        }]
        out = query_rag_mod.format_results(results)
        assert "MQTT Overview" in out
        assert "wiki/sources/iot/mqtt.md" in out
        assert "iot" in out
        assert "curated" in out
        assert "mqtt" in out
        assert "Broker" in out


# ── format_json ────────────────────────────────────────────────────────

class TestFormatJson:
    def test_returns_valid_json(self):
        results = [{"rank": 1, "score": 0.9, "title": "A"}]
        out = query_rag_mod.format_json(results)
        parsed = json.loads(out)
        assert parsed == results

    def test_preserves_unicode(self):
        results = [{"title": "ทดสอบ"}]
        out = query_rag_mod.format_json(results)
        assert "ทดสอบ" in out  # ensure_ascii=False preserves utf-8
