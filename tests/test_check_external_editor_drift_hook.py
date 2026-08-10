"""Tests for scripts/hooks/check_external_editor_drift.py — Iron Law #7.

Prevents accidental downgrade of files whose source of truth lives in
external editors (userscripts in Tampermonkey). Requires
USERSCRIPT_SYNC_OK=<version> env var matching the file's @version header.

Pattern A (subprocess).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_external_editor_drift.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def _edit(file_path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {
        "file_path": file_path, "old_string": "x", "new_string": "y"}}


def test_passes_for_non_edit_tool():
    assert _run({"tool_name": "Bash", "tool_input": {}}).returncode == 0


def test_passes_for_non_userscript_file():
    assert _run(_edit("scripts/foo.py")).returncode == 0


def test_passes_for_readme_md():
    assert _run(_edit("README.md")).returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0


class TestWiring:
    def test_registered_in_pretooluse_edit_matcher(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PreToolUse", []):
            if "Edit" in grp.get("matcher", ""):
                for h in grp.get("hooks", []):
                    if "external-editor" in h.get("command", "") or "external_editor" in h.get("command", ""):
                        return
        raise AssertionError("check_external_editor_drift must be on Edit PreToolUse matcher")
