"""live_docs — Slice C: grill against LIVE upstream documentation.

Skills that wrap external tools declare `docs: <raw-markdown-url>` in
frontmatter; the grill stage fetches it (cache TTL 7d, offline-soft) so
clarifying questions cite the CURRENT version, not training-data memory.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from live_docs import fetch_doc, skill_docs_url  # noqa: E402


def _ok(text):
    def get(url, timeout):
        return text
    return get


def _boom(url, timeout):
    raise OSError("network down")


def test_fetch_live_then_cache(tmp_path):
    calls = []
    def get(url, timeout):
        calls.append(url)
        return "# Lib vX\n\nAPI changed today\n"
    r1 = fetch_doc("https://example.com/docs.md", tmp_path, http_get=get)
    assert r1["source"] == "live" and "API changed today" in r1["content"]
    r2 = fetch_doc("https://example.com/docs.md", tmp_path, http_get=get)
    assert r2["source"] == "cache" and calls == [r1["url"]] or len(calls) == 1


def test_ttl_expires_and_refetches(tmp_path):
    calls = []
    def get(url, timeout):
        calls.append(url)
        return "body"
    fetch_doc("https://x/d.md", tmp_path, http_get=get)
    # age the cache beyond TTL
    cf = next((tmp_path / "docs-cache").glob("*.json"))
    data = json.loads(cf.read_text(encoding="utf-8"))
    data["fetched_at"] = time.time() - 8 * 86400
    cf.write_text(json.dumps(data), encoding="utf-8")
    r = fetch_doc("https://x/d.md", tmp_path, http_get=get)
    assert r["source"] == "live" and len(calls) == 2


def test_offline_falls_back_to_stale_cache(tmp_path):
    def get(url, timeout):
        return "fresh body"
    fetch_doc("https://x/d.md", tmp_path, http_get=get)
    cf = next((tmp_path / "docs-cache").glob("*.json"))
    data = json.loads(cf.read_text(encoding="utf-8"))
    data["fetched_at"] = time.time() - 8 * 86400
    cf.write_text(json.dumps(data), encoding="utf-8")
    r = fetch_doc("https://x/d.md", tmp_path, http_get=_boom)
    assert r["source"] == "cache-stale" and r["content"] == "fresh body"


def test_offline_no_cache_is_unavailable_not_crash(tmp_path):
    r = fetch_doc("https://never-seen/x.md", tmp_path, http_get=_boom)
    assert r["source"] == "unavailable" and r["content"] == ""
    assert "network down" in r["reason"]


def test_skill_docs_url_reads_frontmatter(tmp_path):
    sk = tmp_path / "SKILL.md"
    sk.write_text("---\nname: x\ndocs: https://raw.example.com/lib/v9/doc.md\n"
                  "---\n\n# x\n", encoding="utf-8")
    assert skill_docs_url(sk) == "https://raw.example.com/lib/v9/doc.md"
    assert skill_docs_url(tmp_path / "missing.md") is None
    plain = tmp_path / "plain.md"
    plain.write_text("---\nname: y\n---\n", encoding="utf-8")
    assert skill_docs_url(plain) is None


class _FakeHeaders(dict):
    def get_content_type(self):
        return self.get("Content-Type", "text/plain").split(";", 1)[0].strip().lower()

    def get_content_charset(self):
        return None


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str = "text/plain"):
        self._body = body
        self._offset = 0
        self.headers = _FakeHeaders({"Content-Type": content_type})

    def read(self, size=-1):
        if size < 0:
            size = len(self._body) - self._offset
        chunk = self._body[self._offset:self._offset + size]
        self._offset += len(chunk)
        return chunk


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "http://example.com/docs.md",
    "ftp://example.com/docs.md",
])
def test_fetch_rejects_non_https_before_custom_transport(tmp_path, url):
    calls = []

    def get(target, timeout):
        calls.append(target)
        return "unsafe"

    result = fetch_doc(url, tmp_path, http_get=get)
    assert result["source"] == "unavailable"
    assert calls == []
    assert "https" in result["reason"].lower()


def test_fetch_rejects_missing_hostname_before_custom_transport(tmp_path):
    calls = []

    def get(target, timeout):
        calls.append(target)
        return "unsafe"

    result = fetch_doc("https:///docs.md", tmp_path, http_get=get)
    assert result["source"] == "unavailable"
    assert calls == []
    assert "hostname" in result["reason"].lower()


@pytest.mark.parametrize("host", [
    "127.0.0.1",
    "10.0.0.1",
    "169.254.1.1",
    "224.0.0.1",
    "192.0.2.1",
    "0.0.0.0",
    "[::1]",
    "[::]",
    "[ff02::1]",
    "[2001:db8::1]",
])
def test_fetch_rejects_blocked_literal_targets_before_custom_transport(tmp_path, host):
    calls = []

    def get(target, timeout):
        calls.append(target)
        return "unsafe"

    result = fetch_doc(f"https://{host}/docs.md", tmp_path, http_get=get)
    assert result["source"] == "unavailable"
    assert calls == []
    assert "target" in result["reason"].lower()


def test_request_once_rejects_dns_name_resolving_to_loopback(monkeypatch):
    import live_docs

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))
        ],
    )
    monkeypatch.setattr(
        live_docs,
        "_open_pinned_https",
        lambda *args, **kwargs: pytest.fail("blocked DNS answer must not be connected"),
        raising=False,
    )
    with pytest.raises(ValueError, match="blocked|non-global|target"):
        live_docs._request_once("https://example.com/docs.md", time.monotonic() + 1)


def test_request_once_rejects_mixed_public_private_dns_answers(monkeypatch):
    import live_docs

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443)),
        ],
    )
    monkeypatch.setattr(
        live_docs,
        "_open_pinned_https",
        lambda *args, **kwargs: pytest.fail("mixed DNS answer must fail closed"),
        raising=False,
    )
    with pytest.raises(ValueError, match="blocked|non-global|target"):
        live_docs._request_once("https://example.com/docs.md", time.monotonic() + 1)


def test_default_get_revalidates_redirect_target(monkeypatch):
    import live_docs

    calls = []

    def request_once(url, deadline):
        calls.append(url)
        if len(calls) > 1:
            pytest.fail("blocked redirect target must fail before second request")
        return 302, {"Location": "https://127.0.0.1/internal"}, b""

    monkeypatch.setattr(live_docs, "_request_once", request_once, raising=False)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("default transport must not delegate redirects to urlopen"),
    )
    with pytest.raises(ValueError, match="blocked|non-global|target"):
        live_docs._default_get("https://example.com/docs.md", 2)
    assert calls == ["https://example.com/docs.md"]


def test_default_get_caps_redirect_hops(monkeypatch):
    import live_docs

    calls = []

    def request_once(url, deadline):
        calls.append(url)
        return 302, {"Location": "/again"}, b""

    monkeypatch.setattr(live_docs, "_request_once", request_once, raising=False)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("urlopen redirect handling must not be used"),
    )
    with pytest.raises(ValueError, match="redirect"):
        live_docs._default_get("https://example.com/docs.md", 2)
    assert 2 <= len(calls) <= 6


def test_streamed_body_enforces_response_size_cap():
    import live_docs

    body = b"x" * (2 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="size|large|bytes"):
        live_docs._read_limited_body(_FakeResponse(body), time.monotonic() + 2)


def test_rejects_binary_content_type():
    import live_docs

    with pytest.raises(ValueError, match="content|type"):
        live_docs._validate_content_type(_FakeHeaders({"Content-Type": "application/octet-stream"}))


def test_default_get_enforces_total_deadline_before_request(monkeypatch):
    import live_docs

    ticks = iter([100.0, 116.0])
    monkeypatch.setattr(live_docs.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(
        live_docs,
        "_request_once",
        lambda *args, **kwargs: pytest.fail("deadline expiry must stop before request"),
        raising=False,
    )
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("urlopen must not bypass total deadline"),
    )
    with pytest.raises(TimeoutError, match="deadline|timeout"):
        live_docs._default_get("https://example.com/docs.md", 15)


def test_cache_write_is_atomic(tmp_path, monkeypatch):
    calls = []
    real_replace = os.replace

    def replace(src, dst):
        calls.append((Path(src), Path(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", replace)
    result = fetch_doc("https://example.com/docs.md", tmp_path, http_get=_ok("body"))
    assert result["source"] == "live"
    assert len(calls) == 1
    cache_file = next((tmp_path / "docs-cache").glob("*.json"))
    assert json.loads(cache_file.read_text(encoding="utf-8"))["content"] == "body"


def test_cache_directory_failure_does_not_break_live_fetch(tmp_path, monkeypatch):
    real_mkdir = Path.mkdir

    def mkdir(path, *args, **kwargs):
        if path.name == "docs-cache":
            raise OSError("read-only cache")
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)
    result = fetch_doc("https://example.com/docs.md", tmp_path, http_get=_ok("body"))
    assert result["source"] == "live"
    assert result["content"] == "body"



def test_legacy_cache_without_security_policy_is_not_trusted(tmp_path):
    import live_docs

    url = "https://example.com/docs.md"
    cp = live_docs._cache_path(url, tmp_path)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({
        "url": url,
        "content": "legacy-untrusted",
        "fetched_at": time.time(),
    }), encoding="utf-8")
    calls = []

    def get(target, timeout):
        calls.append(target)
        return "fresh-secure"

    result = fetch_doc(url, tmp_path, http_get=get)
    assert result["source"] == "live"
    assert result["content"] == "fresh-secure"
    assert calls == [url]


def test_cache_payload_url_must_match_requested_url(tmp_path):
    import live_docs

    url = "https://example.com/docs.md"
    cp = live_docs._cache_path(url, tmp_path)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({
        "policy": "public-https-pinned-v1",
        "url": "https://other.example/docs.md",
        "content": "wrong-url-cache",
        "fetched_at": time.time(),
    }), encoding="utf-8")
    result = fetch_doc(url, tmp_path, http_get=_ok("fresh-secure"))
    assert result["source"] == "live"
    assert result["content"] == "fresh-secure"
