"""Tests for ZCode Neural Spine hook wiring.

Iron Law #1: failing tests written FIRST.

ตรวจว่า .zcode/config.json (project-level) มี Neural Spine hooks ครบ
หลังจาก wiring:
  - hooks.enabled == true (ZCode ต้องการ flag นี้ — ต่างจาก Claude)
  - SessionStart: replay + reaper
  - PostToolUse Bash: memory-capture (commit auto-capture)
  - Stop: (optional — Stop ใน ZCode ไม่มี summary payload ที่ใช้ได้)

ZCode hook schema เหมือน Claude แต่ wrapper ต่างกัน:
  Claude: {"hooks": {"PreToolUse": [{"matcher":"Bash","hooks":[...]}]}}
  ZCode:  {"hooks": {"enabled": true, "events": {"PreToolUse": [...]}}}
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ZCODE_CONFIG = REPO_ROOT / ".zcode" / "config.json"


def _load_zcode_config() -> dict:
    if not ZCODE_CONFIG.is_file():
        pytest.skip(".zcode/config.json not present")
    return json.loads(ZCODE_CONFIG.read_text(encoding="utf-8"))


def _hook_commands(event: str) -> list[str]:
    """Return list of hook command strings for a given ZCode event."""
    cfg = _load_zcode_config()
    events = cfg.get("hooks", {}).get("events", {})
    cmds = []
    for group in events.get(event, []):
        for h in group.get("hooks", []):
            cmds.append(h.get("command", ""))
    return cmds


# ---------------------------------------------------------------------------
# 1. hooks.enabled must be true (ZCode-specific requirement)
# ---------------------------------------------------------------------------
def test_zcode_hooks_enabled():
    """ZCode disables configuration hooks by default. Must set enabled:true."""
    cfg = _load_zcode_config()
    assert cfg.get("hooks", {}).get("enabled") is True, (
        ".zcode/config.json hooks.enabled must be true — ZCode ignores hooks "
        "without this flag (pitfall #1 in diagnosing-hooks skill)"
    )


# ---------------------------------------------------------------------------
# 2. SessionStart — replay + reaper
# ---------------------------------------------------------------------------
def test_zcode_sessionstart_has_replay_and_reaper():
    cmds = _hook_commands("SessionStart")
    joined = " ".join(cmds)
    assert "session_start" in joined, (
        "SessionStart must call session_start.py for ledger replay + lease reaper"
    )


# ---------------------------------------------------------------------------
# 3. PostToolUse Bash — memory-capture (commit auto-capture)
# ---------------------------------------------------------------------------
def test_zcode_posttooluse_bash_has_memory_capture():
    """PostToolUse on Bash must include memory-capture so commits auto-save."""
    cfg = _load_zcode_config()
    events = cfg.get("hooks", {}).get("events", {})
    bash_cmds = []
    for group in events.get("PostToolUse", []):
        matcher = group.get("matcher", "")
        if "Bash" in matcher or matcher == "":
            for h in group.get("hooks", []):
                bash_cmds.append(h.get("command", ""))
    joined = " ".join(bash_cmds)
    assert "memory-capture" in joined or "memory_capture" in joined, (
        "PostToolUse Bash must call memory-capture hook so commits are "
        "auto-captured to the Memory Ledger"
    )


# ---------------------------------------------------------------------------
# 4. MCP servers preserved (don't break existing awiki + others)
# ---------------------------------------------------------------------------
def test_zcode_mcp_servers_preserved():
    """Wiring hooks must not break the existing MCP servers."""
    cfg = _load_zcode_config()
    servers = cfg.get("mcp", {}).get("servers", {})
    # Critical servers that existed before
    for required in ("awiki", "filesystem"):
        assert required in servers, f"MCP server {required!r} must still exist after wiring"


# ---------------------------------------------------------------------------
# 5. JSON remains valid
# ---------------------------------------------------------------------------
def test_zcode_config_is_valid_json():
    cfg = _load_zcode_config()
    assert isinstance(cfg, dict)
    assert "mcp" in cfg
    assert "hooks" in cfg
