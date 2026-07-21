"""
Tests for Live Dashboard auto-start on SessionStart (session_start.py).

The dashboard auto-launches a detached, idempotent server via
``_ensure_dashboard()`` → ``dashboard-ensure.sh`` → ``server.py --daemonize``.
Must be opt-out-able (``AWIKI_DISABLE_DASHBOARD_AUTOSTART=1``) and must never
spawn a duplicate server (dashboard-ensure.sh is itself PID-guarded).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_START = REPO_ROOT / "scripts" / "hooks" / "session_start.py"
ENSURE_SH = REPO_ROOT / "scripts" / "dashboard-ensure.sh"
SERVER_PY = REPO_ROOT / "scripts" / "live-dashboard" / "server.py"


def _mod():
    spec = importlib.util.spec_from_file_location("session_start_mod", SESSION_START)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Dummy:
    pid = 12345


def _disable(monkeypatch):
    monkeypatch.setenv("AWIKI_DISABLE_DASHBOARD_AUTOSTART", "1")


def _enable(monkeypatch):
    monkeypatch.delenv("AWIKI_DISABLE_DASHBOARD_AUTOSTART", raising=False)


def test_autostart_disabled_does_not_spawn(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or _Dummy())
    _disable(monkeypatch)
    mod._ensure_dashboard()
    assert calls == []


def test_autostart_noop_when_ensure_script_missing(monkeypatch, tmp_path):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or _Dummy())
    _enable(monkeypatch)
    # Point REPO_ROOT's ensure script path somewhere that doesn't exist
    monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path))
    mod._ensure_dashboard()
    assert calls == []


def test_autostart_spawns_dashboard_ensure_when_enabled(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or _Dummy())
    _enable(monkeypatch)
    mod._ensure_dashboard()
    assert len(calls) == 1
    argv = calls[0][0][0]
    assert any("dashboard-ensure.sh" in str(x) for x in argv), argv
    # Must detach so it survives the session hook process. session_start.py
    # picks the platform-correct detachment strategy: start_new_session=True
    # on POSIX, creationflags=CREATE_NO_WINDOW on Windows (start_new_session
    # raises on Windows and would flash a console window). Both are valid
    # "detach from session" strategies — accept either.
    kwargs = calls[0][1]
    if sys.platform == "win32":
        assert kwargs.get("creationflags") is not None, kwargs
    else:
        assert kwargs.get("start_new_session") is True, kwargs


def test_dashboard_ensure_script_is_pid_guarded():
    """dashboard-ensure.sh must refuse to spawn a duplicate (PID file check)."""
    text = ENSURE_SH.read_text(encoding="utf-8")
    assert "PID_FILE" in text and "kill -0" in text, "ensure script must PID-guard"


def test_server_supports_daemonize_and_no_browser():
    """server.py must daemonize (used by ensure.sh) and allow suppressing browser."""
    text = SERVER_PY.read_text(encoding="utf-8")
    assert "--daemonize" in text
    assert "--no-browser" in text
