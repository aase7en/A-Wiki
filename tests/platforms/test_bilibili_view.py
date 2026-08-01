"""Tests for scripts/lib/platforms/bilibili_view.py.

Iron Law #1 — test written FIRST. Fixture `bilibili_view_bvid.json` captured
2026-08-01 from api.bilibili.com/x/web-interface/view?bvid=BV1xx411c7mD
(no auth required; dynamic stat fields redacted for fixture stability).

bilibili_view.py must:
- Extract bvid from a bilibili.com/video/BVxxx URL
- Hit https://api.bilibili.com/x/web-interface/view?bvid=<id> (no auth)
- Check `code == 0` in response; fail-soft otherwise
- Reshape to {title, author, bvid, aid, url, source, thumbnail}
- Send Referer: https://www.bilibili.com/ (Bilibili CDN sometimes 412 without it)
- Fail-soft: never raise — return {"error": "..."} on failure
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── bvid extraction (pure) ────────────────────────────────────────────────

class TestBvidExtraction:

    def test_module_importable(self):
        from platforms import bilibili_view
        assert hasattr(bilibili_view, "extract_bvid")

    @pytest.mark.parametrize("url,expected", [
        ("https://www.bilibili.com/video/BV1xx411c7mD",          "BV1xx411c7mD"),
        ("https://www.bilibili.com/video/BV1xx411c7mD/",         "BV1xx411c7mD"),
        ("https://www.bilibili.com/video/BV1xx411c7mD?t=30",     "BV1xx411c7mD"),
        ("https://b23.tv/BV1xx411c7mD",                          "BV1xx411c7mD"),
        ("https://m.bilibili.com/video/BV1xx411c7mD",            "BV1xx411c7mD"),
    ])
    def test_extracts_bvid_from_known_shapes(self, url, expected):
        from platforms.bilibili_view import extract_bvid
        assert extract_bvid(url) == expected

    @pytest.mark.parametrize("url", [
        "https://example.com/",
        "https://www.bilibili.com/",
        "not a url",
        "",
        "https://www.bilibili.com/video/abc",  # too short / not BV-prefixed
    ])
    def test_returns_none_for_non_video_urls(self, url):
        from platforms.bilibili_view import extract_bvid
        assert extract_bvid(url) is None


# ── reshape_view (pure) ──────────────────────────────────────────────────

class TestReshapeView:

    def test_reshapes_to_flat_dict_with_required_keys(self):
        from platforms.bilibili_view import reshape_view
        raw = _load_fixture("bilibili_view_bvid.json")
        raw = {k: v for k, v in raw.items() if not k.startswith("_")}
        result = reshape_view(raw, bvid="BV1xx411c7mD")
        for key in ("title", "author", "bvid", "aid", "url", "source", "thumbnail"):
            assert key in result
        assert result["source"] == "bilibili"
        assert result["bvid"] == "BV1xx411c7mD"
        assert isinstance(result["aid"], int) or result["aid"] == 0
        # Title from the captured fixture
        assert "字幕君" in result["title"]

    def test_handles_missing_owner_gracefully(self):
        from platforms.bilibili_view import reshape_view
        result = reshape_view({"code": 0, "data": {}}, bvid="BVxxx")
        assert result["author"] == ""
        assert result["title"] == ""


# ── fetch_metadata (network, mocked) ─────────────────────────────────────

class TestFetchMetadata:

    def test_hits_correct_endpoint_with_referer(self, monkeypatch):
        from platforms import bilibili_view
        captured = {}

        class FakeResp:
            def read(self):
                return json.dumps(_load_fixture("bilibili_view_bvid.json")).encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return FakeResp()

        monkeypatch.setattr(bilibili_view.urllib.request, "urlopen", fake_urlopen)
        bilibili_view.fetch_metadata("https://www.bilibili.com/video/BV1xx411c7mD")
        assert "api.bilibili.com/x/web-interface/view" in captured["url"]
        assert "BV1xx411c7mD" in captured["url"]
        # Referer is critical — Bilibili CDN sometimes 412s without it
        assert "bilibili.com" in captured["headers"].get("referer", "")

    def test_code_nonzero_returns_error_dict(self, monkeypatch):
        from platforms import bilibili_view
        # code: -400 with no data (we saw this in the wild when params are wrong)
        error_payload = {"code": -400, "message": "请求错误", "data": None}

        class FakeResp:
            def read(self): return json.dumps(error_payload).encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        monkeypatch.setattr(bilibili_view.urllib.request, "urlopen",
                            lambda req, timeout: FakeResp())
        result = bilibili_view.fetch_metadata("https://www.bilibili.com/video/BV1xx411c7mD")
        assert "error" in result

    def test_network_error_returns_error_dict(self, monkeypatch):
        import urllib.error
        from platforms import bilibili_view

        def boom(req, timeout):
            raise urllib.error.URLError("down")

        monkeypatch.setattr(bilibili_view.urllib.request, "urlopen", boom)
        result = bilibili_view.fetch_metadata("https://www.bilibili.com/video/BV1xx411c7mD")
        assert "error" in result

    def test_invalid_url_returns_error_dict_without_network(self, monkeypatch):
        from platforms import bilibili_view
        called = {"n": 0}

        def fake_urlopen(*a, **kw):
            called["n"] += 1

        monkeypatch.setattr(bilibili_view.urllib.request, "urlopen", fake_urlopen)
        result = bilibili_view.fetch_metadata("https://example.com/")
        assert "error" in result
        assert called["n"] == 0
