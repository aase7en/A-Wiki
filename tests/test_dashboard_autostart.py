"""
Tests for Live Dashboard auto-start on SessionStart (session_start.py).

Convenience-first: every session auto-launches the dashboard server (detached,
idempotent) and opens it once. Must be opt-out-able and must never spawn a
duplicate server. Iron Law #1: tests precede implementation.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_START = REPO_ROOT / "scripts" / "hooks" / "session_start.py"


def _mod():
    spec = importlib.util.spec_from_file_location("session_start_mod", SESSION_START)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Dummy:
    pid = 12345


def test_autostart_disabled_does_not_spawn(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append(a) or _Dummy())
    monkeypatch.setenv("AWIKI_DASHBOARD_AUTOSTART", "0")
    mod.maybe_autostart_dashboard(str(REPO_ROOT))
    assert calls == []


def test_autostart_skips_when_already_running(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod, "_port_open", lambda *a, **k: True)
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append(a) or _Dummy())
    monkeypatch.delenv("AWIKI_DASHBOARD_AUTOSTART", raising=False)
    monkeypatch.delenv("CI", raising=False)
    mod.maybe_autostart_dashboard(str(REPO_ROOT))
    assert calls == []  # never spawn a duplicate server


def test_autostart_spawns_server_when_not_running(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod, "_port_open", lambda *a, **k: False)
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or _Dummy())
    monkeypatch.delenv("AWIKI_DASHBOARD_AUTOSTART", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("AWIKI_DASHBOARD_NO_BROWSER", "1")
    mod.maybe_autostart_dashboard(str(REPO_ROOT))
    assert len(calls) == 1
    argv = calls[0][0][0]
    assert any("server.py" in str(x) for x in argv)
    # browser-open is delegated to the server via env (set after it binds)
    env = calls[0][1].get("env", {})
    assert env.get("AWIKI_DASHBOARD_OPEN") == "0"  # NO_BROWSER honoured


def test_autostart_sets_open_flag_for_browser(monkeypatch):
    mod = _mod()
    calls = []
    monkeypatch.setattr(mod, "_port_open", lambda *a, **k: False)
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or _Dummy())
    monkeypatch.delenv("AWIKI_DASHBOARD_AUTOSTART", raising=False)
    monkeypatch.delenv("AWIKI_DASHBOARD_NO_BROWSER", raising=False)
    monkeypatch.delenv("CI", raising=False)
    mod.maybe_autostart_dashboard(str(REPO_ROOT))
    env = calls[0][1].get("env", {})
    assert env.get("AWIKI_DASHBOARD_OPEN") == "1"


def test_server_opens_browser_after_bind_guarded():
    # server.py must only auto-open when explicitly told to (set after it binds),
    # so it never hijacks the browser when run manually.
    text = (REPO_ROOT / "scripts" / "live-dashboard" / "server.py").read_text(encoding="utf-8")
    assert "AWIKI_DASHBOARD_OPEN" in text
    assert "webbrowser" in text
