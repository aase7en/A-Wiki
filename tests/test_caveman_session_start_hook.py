"""Tests for scripts/hooks/caveman_session_start.py — Iron Law #7b.

SessionStart hook: ensure .tmp/caveman.flag = 'on' on every session start.
User can opt-out via /verbose command (writes 'off').

Pattern B (import) + TestWiring class.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import caveman_session_start as cs  # noqa: E402


# ---------------------------------------------------------------------------
# 1. ensure_flag — creates flag if missing
# ---------------------------------------------------------------------------
def test_ensure_flag_creates_default_on(tmp_path):
    """Missing flag → created with value 'on'."""
    flag = tmp_path / "caveman.flag"
    cs.ensure_flag(flag)
    assert flag.read_text(encoding="utf-8").strip() == "on"


def test_ensure_flag_preserves_off(tmp_path):
    """Existing 'off' flag is NOT overwritten."""
    flag = tmp_path / "caveman.flag"
    flag.write_text("off", encoding="utf-8")
    cs.ensure_flag(flag)
    assert flag.read_text(encoding="utf-8").strip() == "off"


def test_ensure_flag_preserves_on(tmp_path):
    flag = tmp_path / "caveman.flag"
    flag.write_text("on", encoding="utf-8")
    cs.ensure_flag(flag)
    assert flag.read_text(encoding="utf-8").strip() == "on"


# ---------------------------------------------------------------------------
# 2. is_caveman_on — reads flag state
# ---------------------------------------------------------------------------
def test_is_caveman_on_when_flag_on(tmp_path):
    flag = tmp_path / "caveman.flag"
    flag.write_text("on", encoding="utf-8")
    assert cs.is_caveman_on(flag) is True


def test_is_caveman_on_when_flag_off(tmp_path):
    flag = tmp_path / "caveman.flag"
    flag.write_text("off", encoding="utf-8")
    assert cs.is_caveman_on(flag) is False


def test_is_caveman_on_when_flag_missing(tmp_path):
    """Missing flag → default is 'on' (caveman is the default since 2026-08-11)."""
    flag = tmp_path / "missing.flag"
    assert cs.is_caveman_on(flag) is True


# ---------------------------------------------------------------------------
# 3. rules_blob — returns the caveman rules text for injection
# ---------------------------------------------------------------------------
def test_rules_blob_returns_string():
    rules = cs.rules_blob()
    assert isinstance(rules, str)
    assert len(rules) > 0


def test_rules_blob_mentions_key_rules():
    """The injected rules must mention the core caveman rules."""
    rules = cs.rules_blob()
    assert "preamble" in rules.lower() or "ตัด" in rules
    assert "bullet" in rules.lower() or "บรรทัด" in rules


# ---------------------------------------------------------------------------
# 4. main — exit 0 always (advisory, never block SessionStart)
# ---------------------------------------------------------------------------
def test_main_exits_zero(monkeypatch, tmp_path):
    """SessionStart hooks must never block startup."""
    flag = tmp_path / "caveman.flag"
    monkeypatch.setattr(cs, "FLAG_PATH", flag)
    assert cs.main() == 0


def test_main_creates_flag_if_missing(monkeypatch, tmp_path):
    flag = tmp_path / "caveman.flag"
    monkeypatch.setattr(cs, "FLAG_PATH", flag)
    cs.main()
    assert flag.exists()
    assert flag.read_text(encoding="utf-8").strip() == "on"


# ---------------------------------------------------------------------------
# 5. TestWiring — must be registered on SessionStart
# ---------------------------------------------------------------------------
class TestWiring:
    def test_registered_on_sessionstart_claude(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("SessionStart", []):
            for h in grp.get("hooks", []):
                if "caveman_session_start" in h.get("command", ""):
                    return
        raise AssertionError(
            "caveman_session_start.py must be registered on SessionStart "
            "in .claude/settings.json"
        )

    def test_registered_on_sessionstart_codex(self):
        cfg = json.loads(
            (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("SessionStart", []):
            for h in grp.get("hooks", []):
                if "caveman_session_start" in h.get("command", ""):
                    return
        raise AssertionError(
            "caveman_session_start.py must be registered on SessionStart "
            "in .codex/hooks.json (cross-agent parity)"
        )

    def test_wired_direct_not_via_hooks_runner(self):
        """SessionStart advisory hooks must be wired DIRECT — runner swallows
        exit-0 stdout (the caveman rules injection)."""
        for cfg_path in [REPO_ROOT / ".claude" / "settings.json",
                         REPO_ROOT / ".codex" / "hooks.json"]:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            for grp in cfg["hooks"].get("SessionStart", []):
                for h in grp.get("hooks", []):
                    c = h.get("command", "")
                    if "caveman_session_start" in c:
                        assert "hooks_runner" not in c, (
                            f"caveman_session_start in {cfg_path.name} must be "
                            "wired DIRECT — runner swallows exit-0 stdout"
                        )
