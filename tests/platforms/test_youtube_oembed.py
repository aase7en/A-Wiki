"""Tests for scripts/lib/platforms/youtube_oembed.py.

Iron Law #1 — test written FIRST. Fixture `youtube_oembed.json` captured
2026-08-01 from youtube.com/oembed for video dQw4w9WgXcQ (no auth required).

youtube_oembed.py must:
- Extract video ID from a youtube.com/watch?v= or youtu.be/ URL
- Hit https://www.youtube.com/oembed?url=...&format=json (no auth)
- Reshape response to {title, author, thumbnail, url, source}
- Fail-soft on network error (return {"error": ...} dict, never raise)
- Fail-soft on non-200 (return {"error": "HTTP NNN: ..."})
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── URL → video id extraction (pure) ──────────────────────────────────────

class TestVideoIdExtraction:

    def test_module_importable(self):
        from platforms import youtube_oembed
        assert hasattr(youtube_oembed, "extract_video_id")

    @pytest.mark.parametrize("url,expected", [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ",          "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ",                         "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",    "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ",            "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ",            "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ",           "dQw4w9WgXcQ"),
    ])
    def test_extracts_id_from_known_shapes(self, url, expected):
        from platforms.youtube_oembed import extract_video_id
        assert extract_video_id(url) == expected

    @pytest.mark.parametrize("url", [
        "https://example.com/",
        "not a url",
        "",
        "https://www.youtube.com/",
        "https://www.youtube.com/feed/subscriptions",
    ])
    def test_returns_none_for_non_video_urls(self, url):
        from platforms.youtube_oembed import extract_video_id
        assert extract_video_id(url) is None


# ── reshape_oembed (pure) ────────────────────────────────────────────────

class TestReshapeOembed:

    def test_reshapes_to_flat_dict_with_required_keys(self):
        from platforms.youtube_oembed import reshape_oembed
        raw = _load_fixture("youtube_oembed.json")
        # Strip our _capture metadata before passing to reshape
        raw = {k: v for k, v in raw.items() if not k.startswith("_")}
        result = reshape_oembed(raw, video_url="https://youtu.be/dQw4w9WgXcQ")
        for key in ("title", "author", "thumbnail", "url", "source"):
            assert key in result
        assert result["source"] == "youtube"
        assert "dQw4w9WgXcQ" in result["url"]

    def test_handles_missing_thumbnail_gracefully(self):
        from platforms.youtube_oembed import reshape_oembed
        result = reshape_oembed({"title": "x", "author_name": "y"}, video_url="u")
        assert result["thumbnail"] == ""


# ── fetch_metadata (network, mocked) ─────────────────────────────────────

class TestFetchMetadata:

    def test_hits_oembed_endpoint(self, monkeypatch):
        from platforms import youtube_oembed
        captured = {}

        class FakeResp:
            def read(self):
                return json.dumps(_load_fixture("youtube_oembed.json")).encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            return FakeResp()

        monkeypatch.setattr(youtube_oembed.urllib.request, "urlopen", fake_urlopen)
        youtube_oembed.fetch_metadata("https://youtu.be/dQw4w9WgXcQ")
        assert "youtube.com/oembed" in captured["url"]
        assert "dQw4w9WgXcQ" in captured["url"]

    def test_network_error_returns_error_dict(self, monkeypatch):
        import urllib.error
        from platforms import youtube_oembed

        def boom(req, timeout):
            raise urllib.error.URLError("down")

        monkeypatch.setattr(youtube_oembed.urllib.request, "urlopen", boom)
        result = youtube_oembed.fetch_metadata("https://youtu.be/dQw4w9WgXcQ")
        assert isinstance(result, dict)
        assert "error" in result

    def test_non_200_returns_error_dict(self, monkeypatch):
        import urllib.error
        from platforms import youtube_oembed

        def http_404(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, b"{}")

        monkeypatch.setattr(youtube_oembed.urllib.request, "urlopen", http_404)
        result = youtube_oembed.fetch_metadata("https://youtu.be/dQw4w9WgXcQ")
        assert "error" in result
        assert "404" in result["error"]

    def test_invalid_video_url_returns_error_dict(self, monkeypatch):
        """Non-video URL should not even hit the network."""
        from platforms import youtube_oembed
        called = {"n": 0}

        def fake_urlopen(*a, **kw):
            called["n"] += 1

        monkeypatch.setattr(youtube_oembed.urllib.request, "urlopen", fake_urlopen)
        result = youtube_oembed.fetch_metadata("https://example.com/")
        assert "error" in result
        assert called["n"] == 0
