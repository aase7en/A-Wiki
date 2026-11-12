"""
test_scrape_defuddle.py — WO-AWIKI-DEFUDDLE-02: defuddle adapter in the router.

RED-first contract tests. Network-free: subprocess and shutil.which are
monkeypatched everywhere. Verbatim import pattern from test_scrape_advanced.py.
Jev decision record (jev-1.14.0): best_position=position_first (0.84),
blocked_pages_common=0.28 → defuddle is the FIRST method in auto order.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRAPE_MODULE_PATH = REPO_ROOT / "scripts" / "wiki" / "scrape-advanced.py"

_spec = importlib.util.spec_from_file_location("scrape_advanced_defuddle", SCRAPE_MODULE_PATH)
scrape_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scrape_mod)


DEFUDDLE_JSON_STDOUT = (
    '{"content": "Field measurements show a mean link budget of 138 dB.", '
    '"title": "LoRa Mesh Range", "wordCount": 84}'
)


def _ok_subprocess(stdout=DEFUDDLE_JSON_STDOUT, returncode=0, stderr=""):
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


class TestTierRegistration:
    def test_tiers_contains_defuddle_with_pinned_version(self):
        entries = [t for t in scrape_mod.TIERS if t["method"] == "defuddle"]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["devices"] == "all"
        assert "defuddle@0.19.6" in entry["desc"]

    def test_defuddle_is_first_method_in_auto_order(self):
        """Jev decision (2026-11-12): readable articles dominate (blocked 0.28),
        clean Markdown is the ingest goal → defuddle before curl-impersonate."""
        assert scrape_mod.TIERS[0]["method"] == "defuddle"

    def test_adapters_map_defuddle(self):
        assert "defuddle" in scrape_mod.ADAPTERS
        assert callable(scrape_mod.ADAPTERS["defuddle"])


class TestAdapterContract:
    def test_happy_path_returns_markdown_content(self):
        with patch("shutil.which", return_value="/usr/local/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=_ok_subprocess()):
            text = scrape_mod._scrape_defuddle("https://example.com/article")
        assert text == "Field measurements show a mean link budget of 138 dB."

    def test_argv_is_pinned_list_with_flags(self):
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=_ok_subprocess()) as run:
            scrape_mod._scrape_defuddle("https://example.com/a")
        argv = run.call_args[0][0]
        assert argv[:3] == ["npx", "-y", "defuddle@0.19.6"]
        assert "https://example.com/a" in argv
        assert "-m" in argv and "-j" in argv
        assert run.call_args[1].get("timeout", 0) > 0

    def test_npx_missing_raises_explicit_error_not_silent_none(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="npx not found"):
                scrape_mod._scrape_defuddle("https://example.com/a")

    def test_nonzero_exit_returns_none(self):
        proc = _ok_subprocess(stdout="", returncode=1,
                              stderr="Error: No content could be extracted")
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=proc):
            assert scrape_mod._scrape_defuddle("https://example.com/a") is None

    def test_empty_content_returns_none(self):
        proc = _ok_subprocess(stdout='{"content": "", "title": "t"}')
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=proc):
            assert scrape_mod._scrape_defuddle("https://example.com/a") is None

    def test_garbage_json_returns_none(self):
        proc = _ok_subprocess(stdout="not json at all")
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=proc):
            assert scrape_mod._scrape_defuddle("https://example.com/a") is None

    def test_timeout_propagates_to_dispatcher(self):
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=subprocess.TimeoutExpired("npx", 30)):
            with pytest.raises(subprocess.TimeoutExpired):
                scrape_mod._scrape_defuddle("https://example.com/a")


class TestDispatchIntegration:
    def test_npx_missing_records_error_status_and_falls_through(self):
        """When npx is absent the dispatcher must record an explicit
        not-available reason and continue to curl-impersonate."""
        with patch("shutil.which",
                          side_effect=lambda b: "/bin/curl-impersonate"
                          if b.startswith("curl-imp") else None), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=MagicMock(returncode=0,
                                                 stdout="<html>raw</html>",
                                                 stderr="")) as run:
            result = scrape_mod.scrape("https://example.com/a", method="auto",
                                       force_method=False, save_raw=False)
        statuses = {(m["method"], m["status"]) for m in result["methods_tried"]}
        assert any(m == "defuddle" and s == "error" for m, s in statuses), statuses
        assert result["method_used"] in ("curl-impersonate", None)
