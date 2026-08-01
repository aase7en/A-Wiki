"""Tests for scripts/lib/platforms/jina_reader.py.

Iron Law #1 — test written FIRST. Pattern borrowed from Agent-Reach
(channels/web.py:24-34, MIT, 2026 Pnant/Panniantong) — adapted to A-Wiki
conventions (fail-soft, real UA, prefix normalization).

jina_reader.py must:
- Wrap https://r.jina.ai/{url} → Markdown conversion (no auth, free tier)
- Normalize http(s):// prefix (prepend https:// if missing)
- Return Markdown text on success
- Fail-soft: never raise — return {"error": "..."} dict on failure
"""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ── read(url) ────────────────────────────────────────────────────────────

class TestRead:

    def test_module_importable(self):
        from platforms import jina_reader
        assert hasattr(jina_reader, "read")

    def test_hits_jina_prefix(self, monkeypatch):
        from platforms import jina_reader
        captured = {}

        class FakeResp:
            def read(self): return b"# Example Domain\n\nhello"
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            return FakeResp()

        monkeypatch.setattr(jina_reader.urllib.request, "urlopen", fake_urlopen)
        jina_reader.read("https://example.com/")
        assert captured["url"].startswith("https://r.jina.ai/")
        assert "example.com" in captured["url"]

    def test_prepends_https_when_scheme_missing(self, monkeypatch):
        """Agent-Reach's web.py normalizes bare domains — we keep that contract."""
        from platforms import jina_reader
        captured = {}

        class FakeResp:
            def read(self): return b"# X"
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            return FakeResp()

        monkeypatch.setattr(jina_reader.urllib.request, "urlopen", fake_urlopen)
        jina_reader.read("example.com/page")
        assert "https://example.com/page" in captured["url"]

    def test_returns_markdown_text_on_success(self, monkeypatch):
        from platforms import jina_reader

        class FakeResp:
            def read(self): return b"# Title\n\nBody text".encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        monkeypatch.setattr(jina_reader.urllib.request, "urlopen",
                            lambda req, timeout: FakeResp())
        result = jina_reader.read("https://example.com/")
        assert isinstance(result, str)
        assert "Title" in result

    def test_network_error_returns_error_dict(self, monkeypatch):
        import urllib.error
        from platforms import jina_reader

        def boom(req, timeout):
            raise urllib.error.URLError("down")

        monkeypatch.setattr(jina_reader.urllib.request, "urlopen", boom)
        result = jina_reader.read("https://example.com/")
        assert isinstance(result, dict)
        assert "error" in result

    def test_uses_real_user_agent(self, monkeypatch):
        from platforms import jina_reader
        captured = {}

        class FakeResp:
            def read(self): return b"x"
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured.update({k.lower(): v for k, v in req.header_items()})
            return FakeResp()

        monkeypatch.setattr(jina_reader.urllib.request, "urlopen", fake_urlopen)
        jina_reader.read("https://example.com/")
        ua = captured.get("user-agent", "")
        assert "A-Wiki" in ua, f"UA missing A-Wiki prefix: {ua!r}"
