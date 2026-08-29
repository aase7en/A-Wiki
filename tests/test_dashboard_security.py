from __future__ import annotations

import http.client
import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / "scripts" / "live-dashboard" / "server.py"


def _server_module():
    spec = importlib.util.spec_from_file_location("awiki_live_security", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dashboard_bind_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("AWIKI_DASHBOARD_HOST", raising=False)
    monkeypatch.delenv("AWIKI_DASHBOARD_ALLOW_REMOTE", raising=False)
    module = _server_module()
    assert module.resolve_bind_host() == "127.0.0.1"


def test_dashboard_non_loopback_bind_is_rejected(monkeypatch):
    monkeypatch.setenv("AWIKI_DASHBOARD_HOST", "0.0.0.0")
    monkeypatch.delenv("AWIKI_DASHBOARD_ALLOW_REMOTE", raising=False)
    module = _server_module()
    with pytest.raises(RuntimeError, match="loopback-only"):
        module.resolve_bind_host()

def test_dashboard_non_loopback_bind_stays_blocked_even_with_legacy_opt_in(monkeypatch):
    monkeypatch.setenv("AWIKI_DASHBOARD_HOST", "0.0.0.0")
    monkeypatch.setenv("AWIKI_DASHBOARD_ALLOW_REMOTE", "1")
    module = _server_module()
    with pytest.raises(RuntimeError, match="loopback-only"):
        module.resolve_bind_host()


def test_server_start_uses_resolved_bind_host_not_wildcard_literal():
    text = SERVER.read_text(encoding="utf-8")
    assert 'ThreadingHTTPServer((BIND_HOST, PORT), Handler)' in text
    assert 'ThreadingHTTPServer(("0.0.0.0", PORT), Handler)' not in text


def test_browser_origin_policy_allows_only_local_dashboard_origins():
    module = _server_module()
    assert module.is_allowed_browser_origin(None) is True
    assert module.is_allowed_browser_origin("http://localhost:7790") is True
    assert module.is_allowed_browser_origin("http://127.0.0.1:7790") is True
    assert module.is_allowed_browser_origin("http://[::1]:7790") is True
    assert module.is_allowed_browser_origin("https://evil.example") is False
    assert module.is_allowed_browser_origin("null") is False


def test_state_changing_actions_are_post_only_in_server_dispatch():
    text = SERVER.read_text(encoding="utf-8")
    get_block = text.split("def do_GET(self):", 1)[1].split("def do_POST(self):", 1)[0]
    post_block = text.split("def do_POST(self):", 1)[1].split("def _read_body(self):", 1)[0]
    assert 'path == "/clear"' not in get_block
    assert 'path == "/clear"' in post_block
    assert 'path.startswith("/api/fixes/open")' not in get_block
    assert 'path.startswith("/api/fixes/open")' in post_block


def test_dashboard_ui_uses_post_for_state_changing_actions():
    graph = (REPO_ROOT / "scripts" / "live-dashboard" / "src" / "graph.js").read_text(encoding="utf-8")
    fixes = (REPO_ROOT / "scripts" / "live-dashboard" / "fixes.html").read_text(encoding="utf-8")
    assert "fetch('/clear',{method:'POST'" in graph.replace(" ", "")
    normalized = fixes.replace(" ", "").replace("\n", "")
    assert "fetch('/api/fixes/open?path='+encodeURIComponent(path),{method:'POST'" in normalized


def _run_http_server(module, tmp_path):
    module.AGENT_CONFIG_FILE = tmp_path / "agent-config.json"
    server = module.ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, module.AGENT_CONFIG_FILE


def _post_json(url: str, payload: dict, origin: str | None = None):
    headers = {"Content-Type": "application/json"}
    if origin is not None:
        headers["Origin"] = origin
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    return urllib.request.urlopen(request, timeout=3)


def test_cross_origin_browser_post_is_rejected_without_state_change(tmp_path):
    module = _server_module()
    server, config = _run_http_server(module, tmp_path)
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/agents"
        with pytest.raises(urllib.error.HTTPError) as exc:
            _post_json(url, {"workers": ["malicious"]}, origin="https://evil.example")
        assert exc.value.code == 403
        assert not config.exists()
    finally:
        server.shutdown()
        server.server_close()


def test_local_cli_post_without_origin_remains_supported(tmp_path):
    module = _server_module()
    server, config = _run_http_server(module, tmp_path)
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/agents"
        with _post_json(url, {"workers": ["local"]}) as response:
            assert response.status == 200
        assert json.loads(config.read_text(encoding="utf-8"))["workers"] == ["local"]
    finally:
        server.shutdown()
        server.server_close()


def test_browser_origin_rejects_other_local_web_port():
    module = _server_module()
    assert module.is_allowed_browser_origin("http://localhost:3000") is False
    assert module.is_allowed_browser_origin("http://127.0.0.1:3000") is False


def test_dashboard_package_lock_matches_manifest_root_contract():
    package_dir = REPO_ROOT / "scripts" / "live-dashboard"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((package_dir / "package-lock.json").read_text(encoding="utf-8"))
    root = lock["packages"][""]
    assert lock["name"] == manifest["name"]
    assert lock["version"] == manifest["version"]
    assert root["name"] == manifest["name"]
    assert root["version"] == manifest["version"]
    assert root.get("devDependencies", {}) == manifest.get("devDependencies", {})


def _multipart_body(filename: str, payload: bytes = b"data") -> tuple[bytes, str]:
    boundary = "awiki-test-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def test_upload_filename_cannot_escape_upload_dir(tmp_path):
    module = _server_module()
    module.UPLOAD_DIR = tmp_path / "uploads"
    server, _ = _run_http_server(module, tmp_path)
    body, boundary = _multipart_body("../escape.txt")
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/upload"
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request, timeout=3)
        assert exc.value.code == 400
        assert not (tmp_path / "escape.txt").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_upload_rejects_oversized_content_length_before_reading_body(tmp_path):
    module = _server_module()
    module.UPLOAD_DIR = tmp_path / "uploads"
    server, _ = _run_http_server(module, tmp_path)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        conn.putrequest("POST", "/api/upload")
        conn.putheader("Content-Type", "multipart/form-data; boundary=x")
        conn.putheader("Content-Length", str(module.MAX_UPLOAD_BYTES + 1))
        conn.endheaders()
        response = conn.getresponse()
        assert response.status == 413
        assert not module.UPLOAD_DIR.exists()
        response.read()
        conn.close()
    finally:
        server.shutdown()
        server.server_close()


def test_upload_allows_normal_basename_and_writes_inside_upload_dir(tmp_path):
    module = _server_module()
    module.REPO_ROOT = tmp_path
    module.UPLOAD_DIR = tmp_path / "uploads"
    server, _ = _run_http_server(module, tmp_path)
    body, boundary = _multipart_body("note.txt", b"safe")
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/upload"
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 200
        assert (module.UPLOAD_DIR / "note.txt").read_bytes() == b"safe"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize("filename", [r"..\escape.txt", "C:" + r"\fakepath\note.txt", "/tmp/note.txt"])
def test_upload_rejects_path_components(filename, tmp_path):
    module = _server_module()
    module.UPLOAD_DIR = tmp_path / "uploads"
    server, _ = _run_http_server(module, tmp_path)
    body, boundary = _multipart_body(filename)
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/upload"
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request, timeout=3)
        assert exc.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
