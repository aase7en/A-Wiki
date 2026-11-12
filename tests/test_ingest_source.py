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


# ── F8: dedup VALID_DOMAINS to shared lib (Iron Law #1 — test written FIRST) ──

class TestDomainDedup:
    """F8 — VALID_DOMAINS should be imported from scripts/lib/wiki_domains.py,
    not defined inline in each of the 3 wiki-script files.

    These tests pin the refactor contract: they FAIL before the lib exists
    (or before the 3 files import from it), and PASS after.
    """

    def test_lib_wiki_domains_exists(self):
        """scripts/lib/wiki_domains.py must exist and expose VALID_DOMAINS."""
        import importlib
        # lib.wiki_domains resolves because tests/conftest.py adds scripts/ to sys.path
        mod = importlib.import_module("lib.wiki_domains")
        assert hasattr(mod, "VALID_DOMAINS")
        assert "trader" in mod.VALID_DOMAINS

    def test_lib_wiki_domains_has_domain_titles(self):
        import importlib
        mod = importlib.import_module("lib.wiki_domains")
        assert hasattr(mod, "DOMAIN_TITLES")
        assert mod.DOMAIN_TITLES.get("trader") == "Trading & Finance"

    def test_ingest_source_imports_from_lib(self):
        """ingest-source.py must import VALID_DOMAINS from lib.wiki_domains, not define inline."""
        src = (REPO_ROOT / "scripts" / "wiki" / "ingest-source.py").read_text(encoding="utf-8")
        assert "from lib.wiki_domains import" in src
        # The inline definition must be gone
        assert 'VALID_DOMAINS = ("iot"' not in src

    def test_scrape_advanced_imports_from_lib(self):
        """scrape-advanced.py must import VALID_DOMAINS from lib.wiki_domains."""
        src = (REPO_ROOT / "scripts" / "wiki" / "scrape-advanced.py").read_text(encoding="utf-8")
        assert "from lib.wiki_domains import" in src
        assert 'VALID_DOMAINS = ("iot"' not in src

    def test_prompt_template_imports_from_lib(self):
        """batch/prompt_template.py must import VALID_DOMAINS from lib.wiki_domains."""
        src = (REPO_ROOT / "scripts" / "batch" / "prompt_template.py").read_text(encoding="utf-8")
        assert "from lib.wiki_domains import" in src
        assert 'VALID_DOMAINS = ("iot"' not in src

    def test_lib_domains_match_ingest_source(self):
        """The imported lib values must equal what ingest-source uses at runtime."""
        import importlib
        lib_mod = importlib.import_module("lib.wiki_domains")
        assert lib_mod.VALID_DOMAINS == ingest_source_mod.VALID_DOMAINS
        assert lib_mod.DOMAIN_TITLES == ingest_source_mod.DOMAIN_TITLES


# ── WO-AWIKI-INGEST-03: hash, dedup, dry-run ──────────────────────────

class TestHashDedupDryRun:
    """content_sha256 frontmatter, cross-note duplicate detection, --dry-run.

    Jev record (jev-1.14.0, 2026-11-12): cross_domain_policy split 0.41/0.37
    (confidence 0.11), same_content_different_purpose 0.48 — state did not
    settle the question, so code chooses the fail-safe branch: block with
    pointer + explicit --allow-duplicate escape hatch (writes duplicate_of).
    """

    RAW = "Unique ingestion content for hash dedup testing. " * 3

    def _ingest(self, tmp_sources, title, raw=None, **kw):
        import hashlib
        ingest_source_mod.SOURCES_DIR = tmp_sources
        return ingest_source_mod.ingest_source(
            title=title, domain="general", source_type="article",
            ref="https://example.com/hash-dedup", tags=["test"],
            raw_text=raw or self.RAW, **kw)

    def test_hash_and_source_url_in_frontmatter(self, tmp_path):
        import hashlib
        out = self._ingest(tmp_path, "Hash Note One")
        assert out is not None and out.is_file()
        text = out.read_text(encoding="utf-8")
        expect = hashlib.sha256(self.RAW.encode("utf-8")).hexdigest()
        assert f"content_sha256: {expect}" in text
        assert "source_url: https://example.com/hash-dedup" in text

    def test_file_ref_has_no_source_url(self, tmp_path):
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="File Ref Note", domain="general", source_type="other",
            ref="/abs/path/file.pdf", tags=[], raw_text=self.RAW)
        assert out is not None
        assert "source_url:" not in out.read_text(encoding="utf-8")

    def test_duplicate_content_refused_with_pointer(self, tmp_path, capsys):
        first = self._ingest(tmp_path, "First Title")
        assert first is not None
        second = self._ingest(tmp_path, "Second Different Title")
        assert second is None
        err = capsys.readouterr().err
        assert "duplicate" in err.lower() and str(first) in err

    def test_allow_duplicate_writes_portable_relative_marker(self, tmp_path):
        first = self._ingest(tmp_path, "First Title")
        second = self._ingest(tmp_path, "Second Different Title",
                               allow_duplicate=True)
        assert second is not None and second.is_file()
        marker_line = next(
            line for line in second.read_text(encoding="utf-8").splitlines()
            if line.startswith("duplicate_of:"))
        marker = marker_line.split(":", 1)[1].strip()
        assert not marker.startswith("/")  # R82-2: never machine-absolute
        assert marker == "general/first-title.md"  # sources-relative, portable

    def test_dry_run_creates_no_directories(self, tmp_path, capsys):
        out = self._ingest(tmp_path, "Mkdir Guard Note", dry_run=True)
        assert out is not None and not out.exists()
        assert not (tmp_path / "general").exists()  # R82-1b: no mkdir either

    def test_grandfather_notes_without_hash_ignored(self, tmp_path):
        legacy = tmp_path / "general" / "legacy-note.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text("---\ntype: source\ntitle: Legacy\n---\n"
                          + self.RAW, encoding="utf-8")
        out = self._ingest(tmp_path, "Fresh Title")  # same content, no hash in legacy
        assert out is not None

    def test_dry_run_writes_nothing(self, tmp_path, capsys):
        out = self._ingest(tmp_path, "Dry Run Note", dry_run=True)
        assert out is not None and not out.exists()
        assert "dry-run" in capsys.readouterr().out.lower()

    def test_dry_run_still_reports_duplicate(self, tmp_path, capsys):
        first = self._ingest(tmp_path, "First Title")
        assert first is not None
        again = self._ingest(tmp_path, "Other Title", dry_run=True)
        assert again is None
        assert "duplicate" in capsys.readouterr().err.lower()

    def test_cli_exposes_new_flags(self):
        import subprocess, sys
        proc = subprocess.run(
            [sys.executable, str(_path), "--help"],
            capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0
        assert "--dry-run" in proc.stdout and "--allow-duplicate" in proc.stdout


class TestReviewRepairsIngest03:
    """R82-1..4 negative fixtures from the PR #82 independent review."""

    RAW = "Review probe content for ingestion hardening. " * 2

    def _write_note(self, tmp_path, rel, body):
        note = tmp_path / rel
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(body, encoding="utf-8")
        return note

    def _mk_sources_with_one(self, tmp_path):
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Seed Note", domain="general", source_type="article",
            ref="https://example.com/seed", tags=[], raw_text=self.RAW)
        assert out is not None
        return out

    def test_markitdown_success_respects_write_raw_false(self, tmp_path, monkeypatch):
        """R82-1: the helper itself must not write raw when write_raw=False."""
        ingest_source_mod.SOURCES_DIR = tmp_path
        calls = {}

        class FakeResult:
            text_content = "converted body"

        class FakeConverter:
            def convert(self, path):
                calls["converted"] = True
                return FakeResult()

        import types as _types
        fake_mod = _types.ModuleType("markitdown")
        fake_mod.MarkItDown = lambda: FakeConverter()
        monkeypatch.setitem(__import__("sys").modules, "markitdown", fake_mod)
        src = tmp_path / "input.pdf"
        src.write_bytes(b"%PDF-1.4 fake")
        monkeypatch.setattr(ingest_source_mod, "REPO_ROOT", tmp_path)
        text = ingest_source_mod.extract_text_from_file(
            str(src), slug="probe", write_raw=False)
        assert text == "converted body"
        assert not (tmp_path / "raw").exists()

    def test_legacy_body_needle_never_matches(self, tmp_path):
        import hashlib
        other_raw = "Completely different retry content for the legacy-body probe."
        needle = f"content_sha256: {hashlib.sha256(other_raw.encode()).hexdigest()}"
        self._write_note(tmp_path, "general/doc-about-hashing.md",
                         "---\ntitle: Doc\n---\nbody mentions " + needle + " in prose")
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Legacy Probe", domain="general", source_type="article",
            ref="https://example.com/legacy", tags=[], raw_text=other_raw)
        assert out is not None  # body prose must not trigger dedup

    def test_prefixed_key_and_suffixed_value_never_match(self, tmp_path):
        import hashlib
        other_raw = "Distinct content for prefixed-key and suffixed-value probes."
        digest = hashlib.sha256(other_raw.encode()).hexdigest()
        self._write_note(tmp_path, "general/a.md",
                         "---\nnot_content_sha256: " + digest + "suffix\ntitle: A\n---\nbody")
        self._write_note(tmp_path, "general/b.md",
                         "---\ntitle: B\ncontent_sha256x: " + digest + "\n---\nbody")
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Prefix Probe", domain="general", source_type="article",
            ref="https://example.com/prefix", tags=[], raw_text=other_raw)
        assert out is not None

    def test_late_frontmatter_hash_after_long_metadata_still_matches(self, tmp_path):
        ingest_source_mod.SOURCES_DIR = tmp_path
        long_tag = "x" * 2100
        first = ingest_source_mod.ingest_source(
            title="Long Meta Note", domain="general", source_type="article",
            ref="https://example.com/long", tags=[long_tag], raw_text=self.RAW)
        assert first is not None
        again = ingest_source_mod.ingest_source(
            title="Short Title Retry", domain="general", source_type="article",
            ref="https://example.com/long", tags=[], raw_text=self.RAW)
        assert again is None  # R82-4: no fixed cutoff — hash must be seen


    def test_unclosed_frontmatter_never_matches(self, tmp_path):
        import hashlib
        other_raw = "Content probing the unclosed-frontmatter edge case."
        digest = hashlib.sha256(other_raw.encode()).hexdigest()
        self._write_note(tmp_path, "general/unclosed.md",
                         "---\ncontent_sha256: " + digest)  # no closing delimiter
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Unclosed Probe", domain="general", source_type="article",
            ref="https://example.com/unclosed", tags=[], raw_text=other_raw)
        assert out is not None

    def test_indented_block_scalar_needle_never_matches(self, tmp_path):
        import hashlib
        other_raw = "Content probing indented YAML block scalar needles."
        digest = hashlib.sha256(other_raw.encode()).hexdigest()
        self._write_note(tmp_path, "general/blocks.md",
                         "---\ntitle: B\ndescription: |\n  content_sha256: "
                         + digest + "\n---\nbody")
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Block Scalar Probe", domain="general", source_type="article",
            ref="https://example.com/block", tags=[], raw_text=other_raw)
        assert out is not None

    def test_suffixed_value_never_matches(self, tmp_path):
        import hashlib
        other_raw = "Content probing a suffixed hash value."
        digest = hashlib.sha256(other_raw.encode()).hexdigest()
        self._write_note(tmp_path, "general/suffix.md",
                         "---\ntitle: S\ncontent_sha256: " + digest + "-extra\n---\nbody")
        ingest_source_mod.SOURCES_DIR = tmp_path
        out = ingest_source_mod.ingest_source(
            title="Suffix Probe", domain="general", source_type="article",
            ref="https://example.com/suffix", tags=[], raw_text=other_raw)
        assert out is not None
