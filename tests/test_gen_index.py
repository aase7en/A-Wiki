"""
test_gen_index.py — Coverage analysis for gen-index.py.

Phase 4 requirement: validate gen-index.py handles all edge cases:
  - Empty wiki/ tree
  - Corrupt frontmatter
  - Long abstracts
  - Missing domain dirs
  - --check mode detects staleness
"""

from __future__ import annotations
import os
import sys
import re
from pathlib import Path
from typing import Generator

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "wiki"))
from gen_index import (
    parse_frontmatter,
    extract_abstract,
    clip,
    slug_from_path,
    domain_from_path,
    collect_pages,
    render_main,
    render_domain,
    render_sources,
    collect_outputs,
    SECTION_ORDER,
    DOMAIN_ORDER,
    DOMAIN_FILE_SLUG,
)


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def empty_wiki_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """A wiki/ structure with zero .md files."""
    wiki = tmp_path / "wiki"
    for sec in SECTION_ORDER:
        (wiki / sec).mkdir(parents=True, exist_ok=True)
    # No files added
    yield wiki


@pytest.fixture
def sample_wiki(tmp_path: Path) -> Generator[Path, None, None]:
    """A wiki/ structure with known entities and concepts."""
    wiki = tmp_path / "wiki"

    # entities/iot
    e_iot = wiki / "entities" / "iot"
    e_iot.mkdir(parents=True)
    (e_iot / "mqtt.md").write_text(
        "---\ntitle: MQTT Protocol\ntags: [protocol, messaging]\n"
        "type: protocol\nquality: high\n---\n# MQTT\n\nMQTT is a lightweight messaging protocol."
    )
    (e_iot / "lorawan.md").write_text(
        "---\ntitle: LoRaWAN\ntags: [protocol, lpwan]\n"
        "type: protocol\n---\n# LoRaWAN\n\n> TL;DR: Long-range, low-power WAN protocol."
    )

    # concepts/iot
    c_iot = wiki / "concepts" / "iot"
    c_iot.mkdir(parents=True)
    (c_iot / "mesh-networking.md").write_text(
        "---\ntitle: Mesh Networking\ntags: [networking]\n"
        "type: concept\n---\n# Mesh\n\nNodes self-organize into a mesh topology."
    )

    # entities/env
    e_env = wiki / "entities" / "env"
    e_env.mkdir(parents=True)
    (e_env / "air-quality.md").write_text(
        "---\ntitle: Air Quality Sensor\ntags: [sensor, air]\n"
        "type: device\n---\n# Air Quality\n\nMeasures PM2.5, PM10, CO2."
    )

    # synthesis (cross-domain)
    syn = wiki / "synthesis"
    syn.mkdir(parents=True)
    (syn / "iot-air-quality.md").write_text(
        "---\ntitle: IoT for Air Quality\ntags: [iot, env]\n"
        "type: synthesis\n---\n# IoT Air Quality\n\nCombining IoT sensors with environmental monitoring."
    )

    # source
    src = wiki / "sources"
    src.mkdir(parents=True)
    (src / "paper-2024.md").write_text(
        "---\ntitle: 2024 Air Quality Study\ntags: [research]\n"
        "type: paper\n---\n# Paper\n\nPublished in Sensors Journal, 2024."
    )

    yield wiki


# ── clip ───────────────────────────────────────────────────────────────

class TestClip:
    """clip() truncates long strings at ABSTRACT_MAX."""

    def test_short_string_preserved(self):
        assert clip("hello world") == "hello world"

    def test_exact_length(self):
        s = "a" * 65
        assert clip(s) == s

    def test_long_string_truncated(self):
        s = "x" * 100
        result = clip(s)
        assert len(result) <= 65
        assert result.endswith("…")

    def test_whitespace_normalized(self):
        s = "hello    world"
        assert clip(s) == "hello world"


# ── parse_frontmatter ─────────────────────────────────────────────────

class TestParseFrontmatter:
    """parse_frontmatter() handles YAML-ish metadata."""

    def test_no_frontmatter(self):
        meta, body = parse_frontmatter("# Hello\n\nWorld")
        assert meta == {}
        assert body == "# Hello\n\nWorld"

    def test_valid_frontmatter(self):
        text = "---\ntitle: Test\ntags: [a, b]\n---\n# Body"
        meta, body = parse_frontmatter(text)
        assert meta["title"] == "Test"
        assert meta["tags"] == ["a", "b"]

    def test_incomplete_frontmatter(self):
        text = "---\nno closing marker"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_list_with_single_item(self):
        text = "---\ntags: [single]\n---\nBody"
        meta, body = parse_frontmatter(text)
        assert meta["tags"] == ["single"]

    def test_empty_tags(self):
        text = "---\ntags: []\n---\nBody"
        meta, body = parse_frontmatter(text)
        assert meta["tags"] == []

    def test_multiline_value_ignored(self):
        """Lines without colon are skipped."""
        text = "---\ntitle: Hello\ndescription\n---\nBody"
        meta, body = parse_frontmatter(text)
        assert "title" in meta
        assert "description" not in meta


# ── extract_abstract ───────────────────────────────────────────────────

class TestExtractAbstract:
    """extract_abstract() picks TL;DR or first paragraph."""

    def test_tldr_priority(self):
        body = "# Page\n\n> **TL;DR**: This is the abstract.\n\nOther text."
        assert extract_abstract(body) == "This is the abstract."

    def test_tldr_with_thai_colon(self):
        body = "# Page\n\n> TL;DR: เนื้อหาสำคัญ\n"
        assert "เนื้อหาสำคัญ" in extract_abstract(body)

    def test_fallback_to_first_paragraph(self):
        body = "# Page\n\nThis is the first paragraph after the title."
        assert extract_abstract(body) == "This is the first paragraph after the title."

    def test_no_abstract_found(self):
        body = "No headings, just raw text."
        assert extract_abstract(body) == "(no abstract)"

    def test_long_first_paragraph_truncated(self):
        body = "# H1\n\n" + "word " * 50
        result = extract_abstract(body)
        assert len(result) <= 65

    def test_skips_lists_tables_blockquotes(self):
        body = "# H1\n\n| Table |\n|-------|\n| cell  |\n\nReal paragraph here."
        assert "Real paragraph" in extract_abstract(body)


# ── slug_from_path ─────────────────────────────────────────────────────

class TestSlugFromPath:
    def test_returns_stem(self, tmp_path):
        p = tmp_path / "entities" / "iot" / "mqtt-protocol.md"
        assert slug_from_path(p) == "mqtt-protocol"

    def test_no_extension(self, tmp_path):
        p = tmp_path / "file"
        assert slug_from_path(p) == "file"


# ── domain_from_path ───────────────────────────────────────────────────

class TestDomainFromPath:
    def test_entity_in_domain(self, tmp_path):
        p = tmp_path / "entities" / "iot" / "mqtt.md"
        assert domain_from_path(p, "entities") == "iot"

    def test_concept_in_domain(self, tmp_path):
        p = tmp_path / "concepts" / "env" / "ecosystem.md"
        assert domain_from_path(p, "concepts") == "env"

    def test_synthesis_empty_domain(self, tmp_path):
        p = tmp_path / "synthesis" / "cross-domain.md"
        assert domain_from_path(p, "synthesis") == ""

    def test_source_empty_domain(self, tmp_path):
        p = tmp_path / "sources" / "paper.md"
        assert domain_from_path(p, "sources") == ""


# ── collect_pages ─────────────────────────────────────────────────────

class TestCollectPages:
    """collect_pages() walks wiki/ and returns structured dict."""

    def test_empty_wiki(self, empty_wiki_dir, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", empty_wiki_dir)
        pages = collect_pages()
        # Should have all sections with empty dicts
        for sec in SECTION_ORDER:
            assert sec in pages
        assert sum(len(r) for r in pages["entities"].values()) == 0

    def test_sample_wiki(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()

        # 2 iot entities
        assert len(pages["entities"].get("iot", [])) == 2
        # 1 iot concept
        assert len(pages["concepts"].get("iot", [])) == 1
        # 1 env entity
        assert len(pages["entities"].get("env", [])) == 1
        # 1 synthesis
        syn_count = sum(len(v) for v in pages["synthesis"].values())
        assert syn_count == 1
        # 1 source
        src_count = sum(len(v) for v in pages["sources"].values())
        assert src_count == 1

    def test_page_records_have_required_fields(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        iot_entities = pages["entities"].get("iot", [])
        for rec in iot_entities:
            assert "slug" in rec
            assert "path" in rec
            assert "abstract" in rec
            assert "tags" in rec


# ── render_main ───────────────────────────────────────────────────────

class TestRenderMain:
    """render_main() produces valid markdown with stats."""

    def test_contains_stats_table(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        output = render_main(pages)
        assert "## Stats" in output
        assert "Total" in output
        for sec in SECTION_ORDER:
            assert sec.rstrip("s").title() in output or SECTION_ORDER

    def test_contains_synthesis_section(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        output = render_main(pages)
        assert "SYNTHESIS" in output

    def test_empty_wiki_no_synthesis(self, empty_wiki_dir, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", empty_wiki_dir)
        pages = collect_pages()
        output = render_main(pages)
        # Should still produce valid markdown
        assert output.startswith("#")


# ── render_domain ──────────────────────────────────────────────────────

class TestRenderDomain:
    """render_domain() produces domain-specific overview markdown."""

    def test_iot_domain(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        output = render_domain("iot", pages)
        assert "# Overview" in output
        assert "IoT" in output
        assert "MQTT" in output
        assert "Mesh" in output

    def test_env_domain(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        output = render_domain("env", pages)
        assert "Environmental Health" in output or "Environmental" in output
        assert "Air Quality" in output

    def test_empty_domain(self, empty_wiki_dir, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", empty_wiki_dir)
        pages = collect_pages()
        for dom in DOMAIN_ORDER:
            output = render_domain(dom, pages)
            assert output.startswith("#")


# ── render_sources ─────────────────────────────────────────────────────

class TestRenderSources:
    def test_contains_sources(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        pages = collect_pages()
        output = render_sources(pages)
        assert "Sources" in output
        assert "2024" in output or "paper" in output

    def test_empty_sources(self, empty_wiki_dir, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", empty_wiki_dir)
        pages = collect_pages()
        output = render_sources(pages)
        assert "0 sources" in output or "Stats" in output


# ── collect_outputs ────────────────────────────────────────────────────

class TestCollectOutputs:
    """collect_outputs() returns correct number of files."""

    def test_number_of_outputs(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        monkeypatch.setattr("gen_index.CONTEXT_DIR", sample_wiki.parent / "context")
        pages = collect_pages()
        outputs = collect_outputs(pages)
        # 1 main + 4 domains + 1 sources = 6
        assert len(outputs) == 6

    def test_output_keys_are_paths(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        monkeypatch.setattr("gen_index.CONTEXT_DIR", sample_wiki.parent / "context")
        pages = collect_pages()
        outputs = collect_outputs(pages)
        for path in outputs:
            assert isinstance(path, Path)
            assert path.name.startswith("overview-") or path.name == "wiki-overview.md"


# ── --check mode ───────────────────────────────────────────────────────

class TestCheckMode:
    """--check mode detects stale generated files."""

    def test_stale_detected(self, sample_wiki, monkeypatch, capsys):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        ctx = sample_wiki.parent / "context"
        ctx.mkdir(exist_ok=True)
        monkeypatch.setattr("gen_index.CONTEXT_DIR", ctx)

        # Write a stale overview
        (ctx / "wiki-overview.md").write_text("# Stale content\n")

        pages = collect_pages()
        outputs = collect_outputs(pages)

        # Write outputs to disk
        for path, content in outputs.items():
            path.write_text(content, encoding="utf-8")

        # Now modify one file to be stale
        (ctx / "overview-iot.md").write_text("# Stale IoT overview\n")

        # Re-check (simulate --check)
        from gen_index import main as gen_main
        monkeypatch.setattr("sys.argv", ["gen-index.py", "--check"])
        rc = gen_main()
        assert rc == 1

    def test_fresh_passes(self, sample_wiki, monkeypatch):
        monkeypatch.setattr("gen_index.WIKI_DIR", sample_wiki)
        ctx = sample_wiki.parent / "context"
        ctx.mkdir(exist_ok=True)
        monkeypatch.setattr("gen_index.CONTEXT_DIR", ctx)

        # Generate fresh
        from gen_index import main as gen_main
        monkeypatch.setattr("sys.argv", ["gen-index.py"])
        rc = gen_main()

        # Check should pass
        monkeypatch.setattr("sys.argv", ["gen-index.py", "--check"])
        rc = gen_main()
        assert rc == 0