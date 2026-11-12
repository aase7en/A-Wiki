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
        tried = result["methods_tried"]
        assert [m["method"] for m in tried][:2] == ["defuddle", "curl-impersonate"], tried
        assert tried[0]["status"] == "error" and "npx not found" in tried[0].get("detail", ""), tried[0]
        assert tried[1]["status"] == "success", tried[1]
        assert result["method_used"] == "curl-impersonate"
        assert result["error"] is None
        assert run.call_count >= 1  # curl-impersonate actually invoked


class TestReviewRepairs:
    """R81-1/2/3: option-like sources, CLI choices, malformed payloads."""

    def test_option_like_source_raises_value_error(self):
        with patch("shutil.which", return_value="/usr/bin/npx"):
            with pytest.raises(ValueError, match="option-like source"):
                scrape_mod._scrape_defuddle("--help")

    def test_cli_accepts_defuddle_method_choice(self):
        cmd = [sys.executable, str(SCRAPE_MODULE_PATH), "--list", "--method", "defuddle"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr

    def test_cli_rejects_unknown_method(self):
        cmd = [sys.executable, str(SCRAPE_MODULE_PATH), "--list", "--method", "bogus"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 2

    def test_whitespace_content_returns_none(self):
        proc = _ok_subprocess(stdout='{"content": "   \n\t  ", "title": "t"}')
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=proc):
            assert scrape_mod._scrape_defuddle("https://example.com/a") is None

    def test_non_dict_json_returns_none(self):
        proc = _ok_subprocess(stdout='[1, 2, 3]')
        with patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run", return_value=proc):
            assert scrape_mod._scrape_defuddle("https://example.com/a") is None


class TestOriginalSidecar:
    """WO-AWIKI-INGEST-04: keep the ORIGINAL fetch bytes when defuddle wins.

    Jev (jev-1.14.0): original_is_true_source 0.90; sidecar_html layout.
    Best-effort plain curl sidecar — failures never fail the scrape.
    """

    def test_defuddle_win_records_original_fetch(self, tmp_path):
        def which_side(name):
            return "/usr/bin/npx" if name == "npx" else "/usr/bin/curl"
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", side_effect=which_side), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=lambda argv, **kw: (
                              _ok_subprocess() if "defuddle@" in argv[2]
                              else _ok_subprocess(stdout=b"<html>orig</html>"))):
            result = scrape_mod.scrape("https://example.com/article",
                                       method="auto", save_raw=True,
                                       json_out=True)
        assert result["method_used"] == "defuddle"
        assert result["original_fetch"]["status"] == "saved"
        assert result["raw_file"].endswith(".md")

    def test_sidecar_helper_writes_html_and_returns_path(self, tmp_path):
        raw_dir = tmp_path / "raw"
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess(stdout=b"<html>orig</html>")):
            side = scrape_mod._save_original_sidecar(
                "https://example.com/post-x", "post-x")
        assert side is not None and side.name == "post-x.html"
        assert side.read_bytes() == b"<html>orig</html>"

    def test_sidecar_curl_failure_records_not_raises(self, tmp_path):
        raw_dir = tmp_path / "raw"
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess(stdout="", returncode=7)):
            side = scrape_mod._save_original_sidecar(
                "https://example.com/post-x", "post-x")
        assert side is None

    def test_sidecar_skipped_when_curl_missing(self, tmp_path):
        raw_dir = tmp_path / "raw"
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", return_value=None):
            side = scrape_mod._save_original_sidecar(
                "https://example.com/post-x", "post-x")
        assert side is None

    def test_dispatch_wires_sidecar_only_for_defuddle(self, tmp_path):
        raw_dir = tmp_path / "raw"
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess()), \
             patch.object(scrape_mod, "_save_original_sidecar",
                          return_value=None) as sidecar:
            scrape_mod.scrape("https://example.com/a", method="auto",
                              save_raw=True, json_out=True)
        assert sidecar.call_count == 1
        assert sidecar.call_args[0][0] == "https://example.com/a"


class TestSidecarRepairR83:
    """Terra findings R83-1..4: honest sidecar evidence + failure coverage."""

    def test_save_raw_false_never_calls_sidecar(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess()), \
             patch.object(scrape_mod, "_save_original_sidecar",
                          return_value=None) as sidecar:
            result = scrape_mod.scrape("https://example.com/a",
                                       method="auto", save_raw=False,
                                       json_out=True)
        assert sidecar.call_count == 0
        assert "original_fetch" not in result

    def test_sidecar_write_error_scrape_still_succeeds(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess()), \
             patch.object(scrape_mod, "_save_original_sidecar",
                          side_effect=OSError("disk full")):
            result = scrape_mod.scrape("https://example.com/a",
                                       method="auto", save_raw=True,
                                       json_out=True)
        assert result["method_used"] == "defuddle"  # scrape survives
        assert result["original_fetch"]["status"] == "unavailable"

    def test_curl_timeout_returns_none(self, tmp_path):
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=subprocess.TimeoutExpired("curl", 30)):
            assert scrape_mod._save_original_sidecar(
                "https://example.com/a", "a") is None

    def test_http_error_page_not_recorded_as_saved(self, tmp_path):
        """curl -f makes HTTP >= 400 a curl failure — must be unavailable,
        never saved (R83-2)."""
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess(stdout=b"", returncode=22)):
            assert scrape_mod._save_original_sidecar(
                "https://example.com/404", "x") is None

    def test_stale_sidecar_flagged_when_fetch_fails(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "old-page.html").write_bytes(b"<html>old</html>")
        with patch.object(scrape_mod, "RAW_DIR", raw_dir), \
             patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=lambda argv, **kw: (
                              _ok_subprocess() if "defuddle@" in argv[2]
                              else _ok_subprocess(stdout=b"", returncode=22))):
            result = scrape_mod.scrape("https://example.com/old-page",
                                       method="auto", save_raw=True,
                                       json_out=True)
        fetch = result["original_fetch"]
        assert fetch["status"] == "unavailable"
        assert fetch["stale_sidecar_possible"] is True

    def test_saved_carries_honest_note(self, tmp_path):
        def which_side(name):
            return "/usr/bin/npx" if name == "npx" else "/usr/bin/curl"
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", side_effect=which_side), \
             patch.object(scrape_mod.subprocess, "run",
                          side_effect=lambda argv, **kw: (
                              _ok_subprocess() if "defuddle@" in argv[2]
                              else _ok_subprocess(stdout=b"<html>ok</html>"))):
            result = scrape_mod.scrape("https://example.com/ok",
                                       method="auto", save_raw=True,
                                       json_out=True)
        note = result["original_fetch"]["note"]
        assert "best-effort" in note

    def test_sidecar_argv_pins_fail_flag(self, tmp_path):
        """R83-4: -f must stay in argv (HTTP error pages never recorded)."""
        captured = {}
        def capture(argv, **kw):
            captured["argv"] = argv
            return _ok_subprocess(stdout=b"<html>ok</html>")
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run", side_effect=capture):
            scrape_mod._save_original_sidecar("https://example.com/a", "a")
        assert "-fsL" in captured["argv"]  # combined: fail-flag + follow + silent
        assert "--max-time" in captured["argv"]

    def test_sidecar_mkdir_failure_returns_none(self, tmp_path):
        """R83-4: mkdir OSError is contained — helper returns None."""
        fake_raw = MagicMock()
        fake_raw.mkdir.side_effect = OSError("permission denied")
        with patch.object(scrape_mod, "RAW_DIR", fake_raw), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess(stdout=b"<html>x</html>")):
            assert scrape_mod._save_original_sidecar(
                "https://example.com/a", "a") is None

    def test_sidecar_write_bytes_failure_returns_none(self, tmp_path):
        """R83-4: write_bytes OSError is contained — helper returns None."""
        side = MagicMock()
        side.write_bytes.side_effect = OSError("disk full")
        fake_raw = MagicMock()
        fake_raw.__truediv__ = lambda self, name: side
        with patch.object(scrape_mod, "RAW_DIR", fake_raw), \
             patch("shutil.which", return_value="/usr/bin/curl"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess(stdout=b"<html>x</html>")):
            assert scrape_mod._save_original_sidecar(
                "https://example.com/a", "a") is None

    def test_stale_probe_oserror_scrape_still_succeeds(self, tmp_path):
        """R83-1 round 2: even the stale exists() probe raising must not
        abort a successful scrape."""
        class BoomPath(str):
            pass
        with patch.object(scrape_mod, "RAW_DIR", tmp_path / "raw"), \
             patch("shutil.which", return_value="/usr/bin/npx"), \
             patch.object(scrape_mod.subprocess, "run",
                          return_value=_ok_subprocess()), \
             patch.object(Path, "exists",
                          side_effect=OSError("probe denied")):
            result = scrape_mod.scrape("https://example.com/a",
                                       method="auto", save_raw=True,
                                       json_out=True)
        assert result["method_used"] == "defuddle"
        assert result["original_fetch"]["status"] == "unavailable"
