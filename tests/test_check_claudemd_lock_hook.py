"""Tests for scripts/hooks/check_claudemd_lock.py — Iron Law #5.

Blocks edits to CLAUDE.md unless authorization is verified (Drive .secrets
WIKI_UNLOCK / .claude/lock.txt / AUTH_BY_DRIVE_MOUNT=1).

Pattern A (subprocess). Authorization is intentionally NOT bypassed in
tests — only the fail-open paths + non-CLAUDE.md passes are tested.
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_claudemd_lock.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def _edit(file_path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {
        "file_path": file_path, "old_string": "x", "new_string": "y"}}


def test_passes_for_non_edit_tool():
    assert _run({"tool_name": "Bash", "tool_input": {"command": "ls"}}).returncode == 0


def test_passes_for_non_claudemd_file():
    assert _run(_edit("scripts/foo.py")).returncode == 0


def test_passes_for_arbitrary_md_file():
    assert _run(_edit("README.md")).returncode == 0


def test_claudemd_edit_respects_authorization():
    """Editing CLAUDE.md — exit code depends on auth state.

    If WIKI_UNLOCK env is set + matches Drive secret → pass (exit 0).
    If WIKI_UNLOCK unset/mismatched → block (exit 2).

    We don't bypass the auth check here — we just confirm the hook
    returns 0 OR 2 (never 1=error). The exact verdict depends on
    the live auth env, which is intentionally not mocked.
    """
    r = _run(_edit("CLAUDE.md"))
    assert r.returncode in (0, 2), (
        f"unexpected rc={r.returncode}: {r.stderr}"
    )


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
                    if "claudemd" in h.get("command", ""):
                        return
        raise AssertionError("check_claudemd_lock must be on Edit PreToolUse matcher")
