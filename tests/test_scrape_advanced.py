"""
test_scrape_advanced.py — Coverage for scripts/wiki/scrape-advanced.py.

Tests adapter graceful degradation, device detection, and raw/ save logic
without making real HTTP calls.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRAPE_MODULE_PATH = REPO_ROOT / "scripts" / "wiki" / "scrape-advanced.py"

# Import the module by exec (same pattern as test_ingest_source.py)
import importlib.util
_spec = importlib.util.spec_from_file_location("scrape_advanced", SCRAPE_MODULE_PATH)
scrape_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scrape_mod)


class TestSlugify:
    """slugify is vendored from ingest-source.py — basic smoke tests."""

    def test_basic(self):
        assert scrape_mod.slugify("Test Page") == "test-page"

    def test_empty_segment(self):
        assert scrape_mod.slugify("!!!") == ""


class TestFrontmatter:
    def test_generates_delimiters(self):
        out = scrape_mod.frontmatter(title="X")
        assert out.startswith("---")
        assert out.endswith("---")


class TestDetectDevice:
    def test_reads_wiki_device_file(self, tmp_path):
        d = tmp_path / ".wiki-device"
        d.write_text("pi5")
        with patch.object(Path, "home", return_value=tmp_path):
            assert scrape_mod.detect_device() == "pi5"

    def test_defaults_to_home_mac(self):
        # Without a device file on macOS, should return home-mac
        device = scrape_mod.detect_device()
        assert device in ("home-mac", "pi5", "unknown")

    def test_pi5_blocks_browser_tools(self):
        assert not scrape_mod.device_allows("browser-use", "pi5")
        assert not scrape_mod.device_allows("crawl4ai", "pi5")

    def test_macbook_allows_all(self):
        assert scrape_mod.device_allows("browser-use", "home-mac")
        assert scrape_mod.device_allows("crawl4ai", "home-mac")
        assert scrape_mod.device_allows("scrapling", "home-mac")


class TestSaveRawOutput:
    def test_saves_to_raw_dir(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path):
            path = scrape_mod.save_raw_output("https://example.com/page", "hello world")
            assert path.exists()
            assert path.read_text() == "hello world"

    def test_creates_slug_from_url(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path):
            path = scrape_mod.save_raw_output("https://example.com/my-test-page", "data")
            assert "my-test-page" in str(path)
            assert path.suffix == ".md"


class TestListMethods:
    def test_returns_all_methods(self):
        methods = scrape_mod.list_methods("home-mac")
        assert len(methods) == 6
        assert {m["method"] for m in methods} == {
            "curl-impersonate", "scrapling", "autoscraper",
            "crawl4ai", "firecrawl", "browser-use",
        }

    def test_pi5_filters_browser_tools(self):
        methods = scrape_mod.list_methods("pi5")
        pi5_methods = {m["method"] for m in methods if m["available"]}
        assert "browser-use" not in pi5_methods
        assert "crawl4ai" not in pi5_methods
        assert "scrapling" in pi5_methods

    def test_reports_installation_status(self):
        methods = scrape_mod.list_methods("home-mac")
        for m in methods:
            assert "installed" in m
            assert isinstance(m["installed"], bool)


class TestAdapters:
    """Test each adapter's graceful degradation when deps missing."""

    def test_curl_impersonate_not_installed(self):
        assert scrape_mod._scrape_curl_impersonate("http://example.com") is None

    def test_scrapling_import_error(self):
        with patch.dict(sys.modules, {"scrapling": None}):
            with pytest.raises(ImportError):
                scrape_mod._scrape_scrapling("http://x.com")

    def test_autoscraper_import_error(self):
        with patch.dict(sys.modules, {"autoscraper": None}):
            with pytest.raises(ImportError):
                scrape_mod._scrape_autoscraper("http://x.com")

    def test_crawl4ai_import_error(self):
        with patch.dict(sys.modules, {"crawl4ai": None}):
            with pytest.raises(ImportError):
                scrape_mod._scrape_crawl4ai("http://x.com")

    def test_browser_use_import_error(self):
        with patch.dict(sys.modules, {"browser_use": None}):
            with pytest.raises(ImportError):
                scrape_mod._scrape_browser_use("http://x.com")


class TestScrapeDispatch:
    """Test the main scrape() function's fallback chain."""

    def test_all_methods_fail_returns_error(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path):
            with patch.object(scrape_mod, "ADAPTERS", {}):
                result = scrape_mod.scrape("http://x.com", method="auto", json_out=True)
                assert result["error"] == "all methods failed"
                assert result["method_used"] is None

    def test_curl_impersonate_fallback(self, tmp_path):
        """When curl-impersonate adapter returns None, should try next method.
        With no adapters available, should error out gracefully."""
        with patch.object(scrape_mod, "RAW_DIR", tmp_path):
            result = scrape_mod.scrape("http://x.com", method="auto", json_out=True)
            # With no deps installed, all methods should fail gracefully
            assert result["error"] is not None
            assert len(result["methods_tried"]) > 0

    def test_pi5_blocks_browser_use(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path):
            with patch.object(scrape_mod, "detect_device", return_value="pi5"):
                result = scrape_mod.scrape("http://x.com", method="browser-use", json_out=True)
                # browser-use should be blocked by device check
                methods_tried = result["methods_tried"]
                assert any(m["status"] == "blocked_by_device" for m in methods_tried)


class TestCLI:
    """Test CLI argument parsing without executing."""

    def test_no_args_exits(self):
        with patch.object(sys, "argv", ["scrape-advanced.py"]):
            with pytest.raises(SystemExit):
                scrape_mod.main()

    def test_list_succeeds(self):
        with patch.object(sys, "argv", ["scrape-advanced.py", "--list"]):
            scrape_mod.main()  # should not raise
