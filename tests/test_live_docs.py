"""live_docs — Slice C: grill against LIVE upstream documentation.

Skills that wrap external tools declare `docs: <raw-markdown-url>` in
frontmatter; the grill stage fetches it (cache TTL 7d, offline-soft) so
clarifying questions cite the CURRENT version, not training-data memory.
"""
from __future__ import annotations

import json
import sys
import time
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
