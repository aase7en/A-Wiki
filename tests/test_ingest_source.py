"""
test_ingest_source.py — Coverage for scripts/wiki/ingest-source.py.

Pure-function tests (slugify / frontmatter / abstract / concepts / links)
and integration tests for ingest_source() using a monkeypatched SOURCES_DIR.
"""

from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_path = REPO_ROOT / "scripts" / "wiki" / "ingest-source.py"
_spec = importlib.util.spec_from_file_location("ingest_source", _path)
ingest_source_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingest_source_mod)


# ── Pure helpers ──────────────────────────────────────────────────────

class TestSlugify:
    def test_basic_english(self):
        assert ingest_source_mod.slugify("Hello World") == "hello-world"

    def test_strips_punctuation(self):
        assert ingest_source_mod.slugify("LoRa: Long-Range IoT!") == "lora-long-range-iot"

    def test_thai_normalized_to_empty_keeps_ascii(self):
        out = ingest_source_mod.slugify("MQTT คืออะไร")
        assert "mqtt" in out
        assert " " not in out

    def test_collapses_whitespace(self):
        assert ingest_source_mod.slugify("a   b\tc") == "a-b-c"


class TestFrontmatter:
    def test_yaml_delimiters(self):
        out = ingest_source_mod.frontmatter(title="X", tags=["a", "b"])
        lines = out.splitlines()
        assert lines[0] == "---"
        assert lines[-1] == "---"

    def test_list_serialization(self):
        out = ingest_source_mod.frontmatter(tags=["iot", "lora"])
        assert 'tags: ["iot", "lora"]' in out

    def test_bool_serialization(self):
        out = ingest_source_mod.frontmatter(reviewed=True, draft=False)
        assert "reviewed: true" in out
        assert "draft: false" in out


class TestGenerateAbstract:
    def test_short_text_returned_verbatim(self):
        text = "A short abstract."
        assert ingest_source_mod.generate_abstract(text, max_len=200) == "A short abstract."

    def test_strips_code_blocks(self):
        text = "Before ```code block``` After"
        out = ingest_source_mod.generate_abstract(text)
        assert "code block" not in out
        assert "Before" in out and "After" in out

    def test_strips_markdown_syntax(self):
        text = "**Bold** and *italic* and [link](http://x)."
        out = ingest_source_mod.generate_abstract(text)
        assert "**" not in out
        assert "(http" not in out

    def test_truncates_at_sentence_boundary(self):
        text = "First sentence. " + ("filler word " * 50) + "End."
        out = ingest_source_mod.generate_abstract(text, max_len=50)
        assert len(out) <= 55  # rough bound; sentence-cut may overshoot slightly


class TestExtractKeyConcepts:
    def test_picks_repeated_capitalized_phrases(self):
        text = "Edge Computing is great. Edge Computing scales. Edge Computing rocks."
        concepts = ingest_source_mod.extract_key_concepts(text)
        assert "Edge Computing" in concepts

    def test_ignores_single_occurrences(self):
        text = "Edge Computing appears once."
        concepts = ingest_source_mod.extract_key_concepts(text)
        assert concepts == []

    def test_respects_max_concepts(self):
        # 5 distinct phrases × 2 occurrences each → all qualify
        text = " ".join([f"Concept Alpha{i} appears here. Concept Alpha{i} again." for i in range(10)])
        concepts = ingest_source_mod.extract_key_concepts(text, max_concepts=3)
        assert len(concepts) <= 3


class TestExtractLinks:
    def test_markdown_links(self):
        text = "See [docs](https://example.com/x) and [other](https://example.org/y)."
        links = ingest_source_mod.extract_links(text)
        assert "https://example.com/x" in links
        assert "https://example.org/y" in links

    def test_bare_urls(self):
        text = "Visit https://bare.example.com/page for details."
        links = ingest_source_mod.extract_links(text)
        assert any("bare.example.com" in l for l in links)

    def test_deduplicates(self):
        text = "[a](https://x.com) and https://x.com again."
        links = ingest_source_mod.extract_links(text)
        assert links.count("https://x.com") == 1


# ── Integration: ingest_source / create_source_entry ──────────────────

class TestCreateSourceEntry:
    def test_returns_markdown_with_metadata(self):
        out = ingest_source_mod.create_source_entry(
            title="Test Title",
            domain="iot",
            source_type="article",
            abstract="An abstract.",
            ref="https://x.com",
            tags=["mqtt", "esp32"],
            key_concepts=["MQTT Protocol"],
            related_links=["https://x.com/spec"],
            quality="seed",
        )
        assert "# Test Title" in out
        assert "**Type:** article" in out
        assert "**Domain:** IoT" in out  # mapped via DOMAIN_TITLES
        assert "**Ref:** https://x.com" in out
        assert "An abstract." in out
        assert "**MQTT Protocol**" in out
        assert "https://x.com/spec" in out

    def test_no_concepts_shows_placeholder(self):
        out = ingest_source_mod.create_source_entry(
            title="T", domain="iot", source_type="article",
            abstract="A.", ref="r", tags=[], key_concepts=[], related_links=[],
        )
        assert "auto-extract failed" in out

    def test_no_tags_shows_none(self):
        out = ingest_source_mod.create_source_entry(
            title="T", domain="iot", source_type="article",
            abstract="A.", ref="r", tags=[],
        )
        assert "**Tags:** (none)" in out


class TestIngestSource:
    def test_invalid_domain_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
        monkeypatch.setattr(ingest_source_mod, "SOURCES_DIR", tmp_path / "sources")
        result = ingest_source_mod.ingest_source(
            title="Test", domain="not-a-domain", source_type="article",
            ref="r", tags=[], raw_text="content",
        )
        assert result is None
        captured = capsys.readouterr()
        assert "invalid domain" in captured.err

    def test_empty_text_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(ingest_source_mod, "SOURCES_DIR", tmp_path / "sources")
        result = ingest_source_mod.ingest_source(
            title="T", domain="iot", source_type="article",
            ref="r", tags=[], raw_text="",
        )
        assert result is None

    def test_creates_file_in_domain_subdir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(ingest_source_mod, "SOURCES_DIR", tmp_path / "sources")
        result = ingest_source_mod.ingest_source(
            title="My Test Source", domain="iot", source_type="article",
            ref="https://x.com", tags=["mqtt"],
            raw_text="# My Test Source\n\nSome content here.\n",
        )
        assert result is not None
        assert result.exists()
        assert result.parent.name == "iot"
        assert result.stem == "my-test-source"

    def test_does_not_overwrite_existing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
        monkeypatch.setattr(ingest_source_mod, "SOURCES_DIR", tmp_path / "sources")
        # First write
        path = ingest_source_mod.ingest_source(
            title="Dup", domain="iot", source_type="article",
            ref="r", tags=[], raw_text="content one",
        )
        assert path is not None
        original = path.read_text(encoding="utf-8")

        # Second write — same title → same slug → should refuse
        result2 = ingest_source_mod.ingest_source(
            title="Dup", domain="iot", source_type="article",
            ref="r", tags=[], raw_text="content two",
        )
        assert result2 is None
        assert path.read_text(encoding="utf-8") == original
        captured = capsys.readouterr()
        assert "already exists" in captured.err


# ── B6: trader source-domain — Iron Law #1 (test written FIRST, must fail before code change) ──

def _load_module(rel_path: str, mod_name: str):
    """Load a hyphenated script as a module via importlib (same pattern as ingest_source_mod)."""
    spec = importlib.util.spec_from_file_location(mod_name, REPO_ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTraderDomain:
    """B6 — trader domain must work end-to-end across the ingest pipeline.

    The skill registry already has `trader` as a classification domain
    (scripts/skills_registry/__init__.py), but the wiki ingest pipeline
    (4 files duplicating VALID_DOMAINS) does NOT. This inconsistency blocks
    proper trader/quant source ingestion. These tests pin the contract;
    they must FAIL before the 4-file code change and PASS after.
    """

    def test_trader_in_ingest_valid_domains(self):
        """ingest-source.py must accept 'trader'."""
        assert "trader" in ingest_source_mod.VALID_DOMAINS

    def test_trader_has_domain_title(self):
        """DOMAIN_TITLES must have a display title for trader."""
        assert ingest_source_mod.DOMAIN_TITLES.get("trader") == "Trading & Finance"

    def test_trader_creates_file_in_subdir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """End-to-end: ingesting with domain='trader' must land in sources/trader/<slug>.md."""
        monkeypatch.setattr(ingest_source_mod, "SOURCES_DIR", tmp_path / "sources")
        result = ingest_source_mod.ingest_source(
            title="MC Portfolio Sim", domain="trader", source_type="article",
            ref="https://example.com", tags=["monte-carlo"],
            raw_text="# MC Portfolio Sim\n\nSynthetic data demo.\n",
        )
        assert result is not None
        assert result.exists()
        assert result.parent.name == "trader"
        assert result.stem == "mc-portfolio-sim"

    def test_trader_in_scrape_advanced_domains(self):
        """scrape-advanced.py duplicates VALID_DOMAINS — must stay consistent."""
        mod = _load_module(Path("scripts") / "wiki" / "scrape-advanced.py", "scrape_advanced")
        assert "trader" in mod.VALID_DOMAINS

    def test_trader_in_batch_prompt_template(self):
        """batch/prompt_template.py duplicates VALID_DOMAINS AND mentions domains in SYSTEM_PROMPT text."""
        mod = _load_module(Path("scripts") / "batch" / "prompt_template.py", "prompt_template")
        assert "trader" in mod.VALID_DOMAINS
        assert "trader" in mod.SYSTEM_PROMPT
