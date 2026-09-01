"""Tests for scripts/setup-zcode-hooks.py — ZCode user-level hook installer.

Iron Law #1: failing tests FIRST.

Installer contract:
  - build_hooks_block(): ZCode-schema hooks block wiring the A-Wiki stack
    (SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/Stop) through the
    machine-local loader; every entry is a `process` hook (no shell →
    cross-platform safe on Windows).
  - merge_hooks_config(): idempotent upsert into ~/.zcode/cli/config.json —
    re-running replaces our loader-referencing entries, preserves any foreign
    hooks the user already has, never drops unrelated config keys.
  - install(): copies the loader + writes config; --dry-run writes nothing.

Why user-level: ZCode ignores workspace .zcode/config.json hooks (verified
2026-09-01, zcode.z.ai/en/docs/hooks) — A-Wiki's repo-level wiring never
fires; this installer is the supported path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import setup_zcode_hooks as szh  # noqa: E402 -- module under test


def test_build_hooks_block_covers_all_events():
    block = szh.build_hooks_block("C:/py/python.exe", "C:/u/.zcode/hooks/awiki_hook_loader.py")
    events = block["events"]
    for ev in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
        assert ev in events, f"missing event {ev}"
    assert block["enabled"] is True


def test_build_hooks_block_uses_process_type_and_loader():
    python_exe = "C:/py/python.exe"
    loader = "C:/u/.zcode/hooks/awiki_hook_loader.py"
    block = szh.build_hooks_block(python_exe, loader)
    n = 0
    for groups in block["events"].values():
        for group in groups:
            for hook in group["hooks"]:
                assert hook["type"] == "process", "process hooks avoid shell/portability traps"
                assert hook["command"] == python_exe
                assert hook["args"][0] == loader
                assert "${ZCODE_PROJECT_DIR}" in hook["args"][1]
                n += 1
    assert n >= 8, f"expected the full stack wired, got {n} hook entries"


def test_build_hooks_block_routes_stop_and_ssot():
    loader = "L"
    block = szh.build_hooks_block("P", loader)
    stop_targets = [h["args"][1] for g in block["events"]["Stop"] for h in g["hooks"]]
    assert any("a_loop_continue" in t for t in stop_targets), "Stop must drive continuation"
    ss_targets = [h["args"][1] for g in block["events"]["SessionStart"] for h in g["hooks"]]
    assert any("a_loop_ssot" in t for t in ss_targets), "SessionStart must inject SSoT"
    assert any("hooks_runner" in t for t in ss_targets), "existing runner stack stays wired"


def test_merge_hooks_config_idempotent_and_preserves_foreign():
    block = szh.build_hooks_block("P", "L")
    existing = {
        "plugins": {"enabledPlugins": {"x": True}},
        "hooks": {"enabled": True, "events": {
            "Stop": [{"matcher": "", "hooks": [
                {"type": "command", "command": "echo mine"}]}],
            "Custom": [{"matcher": "", "hooks": [
                {"type": "command", "command": "echo keep"}]}],
        }},
    }
    merged = szh.merge_hooks_config(existing, block)
    # idempotent: second merge changes nothing
    assert szh.merge_hooks_config(merged, block) == merged
    # foreign hooks preserved, unrelated keys preserved
    cmds = [h.get("command") for g in merged["hooks"]["events"]["Stop"] for h in g["hooks"]]
    assert "echo mine" in cmds
    assert any(g for g in merged["hooks"]["events"].get("Custom", []))
    assert merged["plugins"] == existing["plugins"]
    # ours present exactly once per target (no duplicates on re-run)
    ours = [c for c in cmds if c == "P"]
    assert len(ours) == len(block["events"]["Stop"][0]["hooks"])


def test_install_copies_loader_and_writes_config(tmp_path):
    zcode_home = tmp_path / ".zcode"
    # pre-existing config → second install must back it up before mutating
    (zcode_home / "cli").mkdir(parents=True)
    (zcode_home / "cli" / "config.json").write_text(
        json.dumps({"plugins": {}}), encoding="utf-8")
    report = szh.install(repo_root=REPO_ROOT, zcode_home=zcode_home)
    assert report["loader_installed"] is True
    loader = zcode_home / "hooks" / "awiki_hook_loader.py"
    assert loader.is_file(), "loader must be installed at the ZCode home"
    cfg = json.loads((zcode_home / "cli" / "config.json").read_text("utf-8"))
    assert cfg["hooks"]["enabled"] is True
    assert cfg["plugins"] == {}, "unrelated config keys must survive"
    assert "SessionStart" in cfg["hooks"]["events"]
    # backup written before mutating an existing config
    assert any(p.name.startswith("config.json.bak") for p in (zcode_home / "cli").glob("*"))


def test_install_dry_run_writes_nothing(tmp_path):
    zcode_home = tmp_path / ".zcode"
    szh.install(repo_root=REPO_ROOT, zcode_home=zcode_home, dry_run=True)
    assert not (zcode_home / "cli" / "config.json").exists()
    assert not (zcode_home / "hooks" / "awiki_hook_loader.py").exists()
