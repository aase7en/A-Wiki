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

    def test_reads_utf16_bom_wiki_device_file(self, tmp_path):
        """Windows PowerShell writes .wiki-device as UTF-16LE BOM.

        Reproduces the live failure seen on this Windows machine:
        detect_device() must not raise UnicodeDecodeError on a UTF-16 file
        (PowerShell's default for `Out-File`/redirect without `-Encoding utf8`).
        """
        d = tmp_path / ".wiki-device"
        # PowerShell-shaped bytes: UTF-16LE BOM + "work-pc\r\n"
        d.write_bytes(b"\xff\xfe" + "work-pc\r\n".encode("utf-16-le"))
        with patch.object(Path, "home", return_value=tmp_path):
            assert scrape_mod.detect_device() == "work-pc"

    def test_defaults_to_home_mac(self, tmp_path):
        # Without a device file anywhere, fall back to platform default.
        # Must patch Path.home() to a tmp dir without .wiki-device — otherwise
        # this test silently couples to the host machine's real device file
        # (and fails on any box where ~/.wiki-device exists).
        with patch.object(Path, "home", return_value=tmp_path):
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
        assert len(methods) == 7  # WO-AWIKI-DEFUDDLE-02 added defuddle
        assert {m["method"] for m in methods} == {
            "defuddle", "curl-impersonate", "scrapling", "autoscraper",
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


class TestSaveRawOverride:
    """WO-AWIKI-SCRAPE-05: --save-raw <path> must override the raw output path.

    Jev (jev-1.14.0): path_override 0.59; raw_preservation_is_default 0.79 —
    default stays always-save; no CLI opt-out (API save_raw=False remains)."""

    def test_save_raw_output_override_writes_exact_path(self, tmp_path):
        target = tmp_path / "custom" / "note.md"
        out = scrape_mod.save_raw_output(
            "https://example.com/deep/page-x", "hello",
            override=target)
        assert out == target and target.read_text(encoding="utf-8") == "hello"

    def test_save_raw_output_default_unchanged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(scrape_mod, "RAW_DIR", tmp_path / "raw")
        out = scrape_mod.save_raw_output(
            "https://example.com/page-y", "body")
        assert out.parent == tmp_path / "raw"
        assert out.name == "page-y.md"

    def test_scrape_raw_path_override_flows_through(self, tmp_path):
        target = tmp_path / "ovr" / "result.md"
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", side_effect=lambda n:
                   "/usr/bin/npx" if n == "npx" else None), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=MagicMock(returncode=0,
                                                 stdout='{"content": "text body", "title": "t"}',
                                                 stderr="")):
            result = scrape_mod.scrape("https://example.com/page-z",
                                       method="auto", save_raw=True,
                                       json_out=True,
                                       raw_path_override=target)
        assert result["raw_file"] == str(target)
        assert target.read_text(encoding="utf-8") == "text body"

    def test_cli_save_raw_flag_real_e2e(self, tmp_path):
        # R84-T3 (terra P2): cwd-independent (absolute fixture path, cwd=
        # tmp_path) and offline-tolerant (npx fetch/network failure skips;
        # real code defects still fail). Pollution guard: nothing may land
        # in the checkout's real raw/ dir.
        import shutil as _shutil
        import subprocess as _sp
        import sys as _sys
        if _shutil.which("npx") is None:
            import pytest as _pytest
            _pytest.skip("npx not installed")
        target = tmp_path / "e2e.md"
        fixture = (Path(__file__).resolve().parent / "fixtures" /
                   "defuddle" / "article-noisy-en.html")
        # R84 r2-1: the CLI's stderr cannot carry npx failure detail (the
        # adapter swallows it), so offline detection uses a canary running
        # the EXACT pinned parse command — canary success means any later
        # CLI failure is a real defect and must fail, not skip.
        canary = _sp.run(
            ["npx", "-y", "defuddle@0.19.6", "parse", str(fixture), "-m", "-j"],
            capture_output=True, text=True, timeout=120)
        if canary.returncode != 0 or not canary.stdout.strip():
            import pytest as _pytest
            _pytest.skip("defuddle/npx unavailable (offline or registry blocked)")
        # R84 r2-2: AWIKI_RAW_DIR isolates sidecar/raw writes into tmp —
        # checkout pollution is structurally impossible, no post-hoc guard.
        import os as _os
        proc = _sp.run(
            [_sys.executable, str(SCRAPE_MODULE_PATH),
             "--url", str(fixture),
             "--method", "defuddle", "--save-raw", str(target), "--json"],
            capture_output=True, text=True, timeout=120,
            cwd=str(tmp_path),
            env={**_os.environ, "AWIKI_RAW_DIR": str(tmp_path / "raw")})
        assert proc.returncode == 0, proc.stderr
        assert target.is_file() and "Ladprao" in target.read_text(encoding="utf-8")

    def test_r84_sidecar_diverts_when_override_is_sidecar_path(self, tmp_path):
        # R84-T1 (terra P1): a --save-raw override landing on the sidecar's own
        # path (raw/<stem>.html) must not be clobbered by the original fetch;
        # the sidecar diverts to <stem>.original.html so both contracts hold.
        raw_dir = tmp_path / "raw"
        target = raw_dir / "x.html"
        defuddle_run = MagicMock(returncode=0,
                                 stdout='{"content": "extracted body", "title": "t"}',
                                 stderr="")
        curl_run = MagicMock(returncode=0, stdout=b"<html>original</html>", stderr=b"")
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", side_effect=lambda n:
                   "/usr/bin/npx" if n == "npx" else
                   "/usr/bin/curl" if n == "curl" else None), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=[defuddle_run, curl_run]):
            result = scrape_mod.scrape("https://example.com/x",
                                       method="defuddle", save_raw=True,
                                       json_out=True,
                                       raw_path_override=target)
        assert result["raw_file"] == str(target)
        assert target.read_text(encoding="utf-8") == "extracted body"
        diverted = raw_dir / "x.original.html"
        assert diverted.read_bytes() == b"<html>original</html>"

    def test_r84_scrape_positional_compat_json_out_seventh(self, tmp_path):
        # R84-T2 (terra P2): raw_path_override must sit AFTER json_out so the
        # historical positional order (url..save_raw, json_out) keeps working.
        import inspect
        params = list(inspect.signature(scrape_mod.scrape).parameters)
        assert params[:7] == ["url", "method", "force_method", "wizard",
                              "domain", "save_raw", "json_out"]
        run = MagicMock(returncode=0,
                        stdout='{"content": "positional body", "title": "t"}',
                        stderr="")
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", side_effect=lambda n:
                   "/usr/bin/npx" if n == "npx" else None), \
             patch.object(scrape_mod.subprocess, "run", return_value=run):
            result = scrape_mod.scrape("https://example.com/p", "auto",
                                       False, False, None, True, True)
        assert result["url"] == "https://example.com/p"
        assert result["raw_file"] is not None

    def test_r84_raw_dir_env_override(self, tmp_path):
        # R84-T4 (terra r2 P2): AWIKI_RAW_DIR structurally isolates every raw
        # write (tests, sandboxes) from the checkout's raw/ dir. Fresh module
        # from spec (scrape_mod is not in sys.modules, reload() unusable).
        import importlib.util as _ilu
        import os as _os
        island = tmp_path / "island"
        _os.environ["AWIKI_RAW_DIR"] = str(island)
        try:
            spec = _ilu.spec_from_file_location("scrape_advanced_env", SCRAPE_MODULE_PATH)
            fresh = _ilu.module_from_spec(spec)
            spec.loader.exec_module(fresh)
            out = fresh.save_raw_output("https://example.com/env-page", "text")
            assert out.parent == island
        finally:
            _os.environ.pop("AWIKI_RAW_DIR", None)
