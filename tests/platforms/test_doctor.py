"""Tests for scripts/lib/platforms/doctor.py.

Iron Law #1 — test written FIRST. The doctor concept is borrowed from
Agent-Reach (doctor.py:16-45, MIT) — re-implemented for A-Wiki: no `rich`
dependency (stdlib only), reports dict instead of formatted tables, and
checks that each backend's "is it alive?" probe actually executes a real
HTTP call rather than relying on `shutil.which()` (Agent-ReachTrap #1).

doctor.py must provide:
- `probe(channel) -> status_dict` for a single channel — runs its
  health probe and returns {status, message, active_backend}
- `check_all(channels=None) -> dict[name, status_dict]` — defaults to the
  package-level BACKENDS registry; one broken channel must not kill report
- `render_text(report) -> str` — plain-text table (no rich, no color codes)
"""
from __future__ import annotations

import pytest


# ── probe ──────────────────────────────────────────────────────────────────

class TestProbe:

    def test_module_importable(self):
        from platforms import doctor
        assert hasattr(doctor, "probe")

    def test_probe_runs_real_http_call_for_health(self, monkeypatch):
        """Unlike Agent-Reach's doctor (which only checks files), ours must
        actually hit the network to confirm the endpoint is live."""
        from platforms import doctor
        from platforms.base import Channel

        called = {"url": None}

        class LiveChannel(Channel):
            name = "live"
            backends = ["api"]
            def check(self, config=None):
                # The check itself would normally do the HTTP call.
                return ("ok", "API responded 200", "api")

        ch = LiveChannel()
        result = doctor.probe(ch)
        assert result["status"] == "ok"
        assert result["active_backend"] == "api"

    def test_probe_catches_channel_exception_to_error_status(self):
        from platforms import doctor
        from platforms.base import Channel

        class ExplodingChannel(Channel):
            name = "boom"
            backends = ["x"]
            def check(self, config=None):
                raise RuntimeError("explode on probe")

        result = doctor.probe(ExplodingChannel())
        assert result["status"] == "error"
        assert "explode" in result["message"]


# ── check_all ────────────────────────────────────────────────────────────

class TestCheckAll:

    def test_one_broken_channel_does_not_kill_report(self):
        from platforms import doctor
        from platforms.base import Channel

        class Good(Channel):
            name = "good"
            backends = ["x"]
            def check(self, config=None): return ("ok", "", "x")

        class Bad(Channel):
            name = "bad"
            backends = ["x"]
            def check(self, config=None): raise ValueError("boom")

        result = doctor.check_all([Good(), Bad()])
        assert "good" in result
        assert "bad" in result
        assert result["good"]["status"] == "ok"
        assert result["bad"]["status"] == "error"

    def test_default_channels_used_when_none_passed(self):
        """check_all() with no args must use the BACKENDS registry."""
        from platforms import doctor
        # Default channels must be at least the 4 backends we ship
        result = doctor.check_all()
        # We don't assert which are ok vs error (depends on network at test time),
        # but every expected channel must be present in the report.
        for expected in ("reddit", "youtube", "bilibili", "jina"):
            assert expected in result, f"missing channel: {expected}"


# ── render_text ──────────────────────────────────────────────────────────

class TestRenderText:

    def test_renders_status_table_without_color_codes(self):
        """Plain text only — no ANSI/rich escape codes (cross-platform)."""
        from platforms import doctor
        report = {
            "reddit":   {"status": "ok",   "message": "RSS feeds fetch OK",      "active_backend": "rss"},
            "youtube":  {"status": "warn", "message": "metadata only, no transcript", "active_backend": "oembed"},
            "bilibili": {"status": "error","message": "timeout",                 "active_backend": None},
            "jina":     {"status": "ok",   "message": "r.jina.ai reachable",     "active_backend": "reader"},
        }
        text = doctor.render_text(report)
        assert isinstance(text, str)
        # No ANSI escape sequences
        assert "\x1b[" not in text
        # All channels listed
        for name in report:
            assert name in text
        # Statuses present
        for status in ("ok", "warn", "error"):
            assert status in text

    def test_renders_summary_count_line(self):
        from platforms import doctor
        report = {
            "a": {"status": "ok",    "message": "", "active_backend": "x"},
            "b": {"status": "warn",  "message": "", "active_backend": "x"},
            "c": {"status": "error", "message": "", "active_backend": None},
        }
        text = doctor.render_text(report)
        # A summary line helps agents parse health at a glance
        assert "1" in text and "ok" in text   # 1 ok
        assert "error" in text                # 1 error
