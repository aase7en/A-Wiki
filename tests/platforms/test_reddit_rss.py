"""Tests for scripts/lib/platforms/reddit_rss.py.

Iron Law #1 — test written FIRST. These tests must FAIL until reddit_rss.py
is implemented in chunk 2. The fixture `reddit_worldnews.rss` was captured
from the real reddit.com/r/worldnews/.rss endpoint on 2026-08-01 (Iron Law #7
provenance — saved to tests/platforms/fixtures/reddit_worldnews.rss).

The reddit_rss module must:
- Parse a valid Atom/RSS feed from reddit.com/r/<sub>/.rss (HTTP 200, verified alive)
- Reshape entries into flat dicts: {title, url, summary, published, source}
- Cap entries per fetch (default 25, matching Reddit's page size)
- Use a real User-Agent (Reddit rejects anonymous UAs)
- Fail-soft: never raise — return [{"error": "..."}] on failure
- Return [{"error": "feedparser not installed"}] when feedparser is None
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ── fixture loading ──────────────────────────────────────────────────────

def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ── parse_shape: reddit_rss.parse_feed(xml_text) -> list[dict] ───────────

class TestParseFeed:
    """parse_feed(xml_text) → list[dict] is the pure parser (no I/O)."""

    def test_module_importable(self):
        from platforms import reddit_rss
        assert hasattr(reddit_rss, "parse_feed")

    def test_returns_list_of_dicts(self):
        from platforms.reddit_rss import parse_feed
        xml = _load_fixture("reddit_worldnews.rss")
        result = parse_feed(xml)
        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert isinstance(item, dict)

    def test_entry_has_required_keys(self):
        from platforms.reddit_rss import parse_feed
        xml = _load_fixture("reddit_worldnews.rss")
        result = parse_feed(xml)
        first = result[0]
        for key in ("title", "url", "summary", "published", "source"):
            assert key in first, f"missing key: {key}"
            assert isinstance(first[key], str)

    def test_url_is_absolute_https(self):
        """Reddit RSS gives absolute https URLs — never relative."""
        from platforms.reddit_rss import parse_feed
        xml = _load_fixture("reddit_worldnews.rss")
        result = parse_feed(xml)
        for item in result:
            assert item["url"].startswith("https://"), item["url"]

    def test_source_field_identifies_subreddit(self):
        from platforms.reddit_rss import parse_feed
        xml = _load_fixture("reddit_worldnews.rss")
        result = parse_feed(xml)
        assert result[0]["source"] == "reddit"

    def test_summary_is_truncated(self):
        """Long HTML summaries must be truncated to keep token cost bounded."""
        from platforms.reddit_rss import parse_feed, MAX_SUMMARY_CHARS
        xml = _load_fixture("reddit_worldnews.rss")
        result = parse_feed(xml)
        for item in result:
            assert len(item["summary"]) <= MAX_SUMMARY_CHARS

    def test_empty_xml_returns_empty_list(self):
        from platforms.reddit_rss import parse_feed
        assert parse_feed("") == []

    def test_garbage_xml_returns_empty_list_not_raise(self):
        """Fail-soft: corrupt XML → [] not exception."""
        from platforms.reddit_rss import parse_feed
        assert parse_feed("not xml at all <><>") == []


# ── fetch_posts: reddit_rss.fetch_posts(subreddit, limit=25) -> list[dict] ─

class TestFetchPosts:
    """fetch_posts() is the network entry point. Tests mock urllib."""

    def test_uses_real_user_agent(self, monkeypatch):
        """Reddit rejects anonymous UAs (verified). Must send a descriptive UA."""
        from platforms import reddit_rss
        captured_headers = {}

        class FakeResp:
            def read(self): return _load_fixture("reddit_worldnews.rss").encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured_headers.update(req.headers)
            return FakeResp()

        monkeypatch.setattr(reddit_rss.urllib.request, "urlopen", fake_urlopen)
        reddit_rss.fetch_posts("worldnews", limit=5)
        ua = captured_headers.get("User-agent") or captured_headers.get("User-Agent")
        assert ua and "A-Wiki" in ua, f"UA missing A-Wiki prefix: {ua!r}"

    def test_hits_correct_url(self, monkeypatch):
        from platforms import reddit_rss
        captured_url = {}

        class FakeResp:
            def read(self): return _load_fixture("reddit_worldnews.rss").encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout):
            captured_url["url"] = req.full_url
            return FakeResp()

        monkeypatch.setattr(reddit_rss.urllib.request, "urlopen", fake_urlopen)
        reddit_rss.fetch_posts("worldnews", limit=5)
        assert "reddit.com/r/worldnews/.rss" in captured_url["url"]

    def test_limit_caps_results(self, monkeypatch):
        from platforms import reddit_rss

        class FakeResp:
            def read(self): return _load_fixture("reddit_worldnews.rss").encode("utf-8")
            def __enter__(self): return self
            def __exit__(self, *a): pass

        monkeypatch.setattr(reddit_rss.urllib.request, "urlopen",
                            lambda req, timeout: FakeResp())
        result = reddit_rss.fetch_posts("worldnews", limit=3)
        assert len(result) == 3

    def test_network_error_returns_error_dict_not_raise(self, monkeypatch):
        """Fail-soft: network down → [{"error": ...}], not exception."""
        from platforms import reddit_rss
        import urllib.error

        def boom(req, timeout):
            raise urllib.error.URLError("network down")

        monkeypatch.setattr(reddit_rss.urllib.request, "urlopen", boom)
        result = reddit_rss.fetch_posts("worldnews")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]


# ── feedparser-not-installed path ─────────────────────────────────────────

class TestFeedparserOptional:
    """feedparser is optional. Module must degrade gracefully if missing."""

    def test_returns_error_when_feedparser_none(self, monkeypatch):
        from platforms import reddit_rss
        monkeypatch.setattr(reddit_rss, "feedparser", None)
        result = reddit_rss.fetch_posts("worldnews")
        assert len(result) == 1 and "error" in result[0]
