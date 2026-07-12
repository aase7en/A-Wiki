"""
Tests for the Live Dashboard Council pane backend: GET /api/council and
GET /api/council/<id>.

Council rounds are written by scripts/lib/council_room.py to
.tmp/council/<id>.json (see tests/test_council_room.py). This file only
tests the dashboard's read-side HTTP surface — offline, real HTTP requests
against a ThreadingHTTPServer bound to an ephemeral port so status codes and
Content-Type headers can be asserted directly (mirrors the endpoint-level
intent of tests/test_dashboard_capabilities.py, but that file calls internal
functions directly; here we need real headers, so we spin the actual
server.Handler on 127.0.0.1:0 and tear it down per test).
"""
from __future__ import annotations

import http.server
import importlib.util
import json
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = REPO_ROOT / "scripts" / "live-dashboard" / "server.py"


def _load_server():
    """Fresh module load per test — same pattern as test_dashboard_capabilities.py."""
    spec = importlib.util.spec_from_file_location("ld_server_council", SERVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_transcript(council_dir: Path, council_id: str, **overrides) -> dict:
    council_dir.mkdir(parents=True, exist_ok=True)
    transcript = {
        "id": council_id,
        "question": "What should we build next?",
        "task_type": "reason",
        "created_at": datetime(2026, 7, 12, 14, 43, 2, tzinfo=timezone.utc).isoformat(),
        "participants": [
            {"engine": "GEMINI", "status": "ok", "answer": "Do X.", "latency_s": 1.2},
            {"engine": "GROQ", "status": "fail", "answer": "timeout after 90s", "latency_s": 90.0},
        ],
        "synthesis": None,
        "status": "ok",
    }
    transcript.update(overrides)
    (council_dir / f"{council_id}.json").write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return transcript


@pytest.fixture
def council_server(tmp_path, monkeypatch):
    """Spin up server.Handler on an ephemeral port with council_room pointed at tmp_path."""
    mod = _load_server()
    council_dir = tmp_path / "council"
    monkeypatch.setattr(mod.council_room, "COUNCIL_DIR", council_dir)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), mod.Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield mod, f"http://127.0.0.1:{port}", council_dir
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _get(url):
    """GET url, returning (status, headers, parsed_json) even on 4xx/5xx."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), json.loads(e.read().decode("utf-8"))


# ── GET /api/council (list) ─────────────────────────────────────────────


def test_list_empty_when_no_council_dir(council_server):
    _mod, base, _council_dir = council_server
    status, headers, body = _get(f"{base}/api/council")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert body == {"councils": []}


def test_list_populated_newest_first(council_server):
    _mod, base, council_dir = council_server
    _write_transcript(
        council_dir, "council-20260712-100000-aaaa",
        created_at=datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        question="older question",
    )
    _write_transcript(
        council_dir, "council-20260712-150000-bbbb",
        created_at=datetime(2026, 7, 12, 15, 0, 0, tzinfo=timezone.utc).isoformat(),
        question="newer question",
    )
    status, _headers, body = _get(f"{base}/api/council")
    assert status == 200
    ids = [c["id"] for c in body["councils"]]
    assert ids == ["council-20260712-150000-bbbb", "council-20260712-100000-aaaa"]


def test_list_summary_fields(council_server):
    _mod, base, council_dir = council_server
    _write_transcript(council_dir, "council-20260712-090000-cccc")
    status, _headers, body = _get(f"{base}/api/council")
    assert status == 200
    summary = body["councils"][0]
    assert summary["id"] == "council-20260712-090000-cccc"
    assert summary["question"] == "What should we build next?"
    assert summary["participants_ok"] == 1
    assert summary["participants_total"] == 2
    assert summary["has_synthesis"] is False


def test_list_reflects_synthesis_flag(council_server):
    _mod, base, council_dir = council_server
    _write_transcript(
        council_dir, "council-20260712-090000-dddd",
        synthesis={"text": "verdict", "author": "primary-agent", "added_at": "2026-07-12T09:05:00+00:00"},
    )
    status, _headers, body = _get(f"{base}/api/council")
    assert body["councils"][0]["has_synthesis"] is True


# ── GET /api/council/<id> (detail) ──────────────────────────────────────


def test_detail_happy_path_returns_full_transcript(council_server):
    _mod, base, council_dir = council_server
    written = _write_transcript(council_dir, "council-20260712-090000-eeee")
    status, headers, body = _get(f"{base}/api/council/council-20260712-090000-eeee")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert body == written


def test_detail_includes_synthesis_when_present(council_server):
    _mod, base, council_dir = council_server
    synth = {"text": "verdict text", "author": "primary-agent", "added_at": "2026-07-12T09:05:00+00:00"}
    _write_transcript(council_dir, "council-20260712-090000-ffff", synthesis=synth)
    status, _headers, body = _get(f"{base}/api/council/council-20260712-090000-ffff")
    assert status == 200
    assert body["synthesis"] == synth


def test_detail_404_on_unknown_id(council_server):
    _mod, base, council_dir = council_server
    council_dir.mkdir(parents=True, exist_ok=True)
    status, _headers, body = _get(f"{base}/api/council/council-20260101-000000-0000")
    assert status == 404
    assert "error" in body


def test_detail_404_on_path_traversal_id(council_server):
    _mod, base, _council_dir = council_server
    # ".." is sent over the wire unmodified by both http.client and urllib
    # (verified: neither normalizes dot-segments client-side), so this
    # actually exercises council_room.COUNCIL_ID_RE rejecting the id before
    # any filesystem access.
    status, _headers, body = _get(f"{base}/api/council/../evil")
    assert status == 404
    assert "error" in body


def test_detail_404_on_malformed_id_shape(council_server):
    _mod, base, _council_dir = council_server
    status, _headers, body = _get(f"{base}/api/council/not-a-council-id")
    assert status == 404
    assert "error" in body


def test_list_endpoint_content_type_json(council_server):
    _mod, base, _council_dir = council_server
    status, headers, _body = _get(f"{base}/api/council")
    assert status == 200
    assert headers["Content-Type"] == "application/json"


def test_detail_ignores_corrupt_sibling_transcript(council_server):
    """list_councils() skips unparsable files — detail lookup for the good
    id must still succeed even with a corrupt sibling on disk."""
    _mod, base, council_dir = council_server
    council_dir.mkdir(parents=True, exist_ok=True)
    (council_dir / "council-20260712-090000-1111.json").write_text("{not json", encoding="utf-8")
    written = _write_transcript(council_dir, "council-20260712-090000-2222")
    status, _headers, body = _get(f"{base}/api/council/council-20260712-090000-2222")
    assert status == 200
    assert body == written
