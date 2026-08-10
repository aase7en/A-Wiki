"""Tests for scripts/hooks/post_wiki_edit.py — PostToolUse advisory.

Triggers gen-index.py after WriteToFile/ReplaceInFile on wiki/ paths.
Never blocks (exit 0 always).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "post_wiki_edit.py"


def _run(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=os.environ, cwd=str(REPO_ROOT), timeout=60)


def test_always_exits_zero_for_wiki_edit():
    payload = {"tool_name": "WriteToFile",
               "tool_input": {"file_path": "wiki/test.md", "content": "x"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_for_non_wiki_path():
    payload = {"tool_name": "WriteToFile",
               "tool_input": {"file_path": "scripts/foo.py", "content": "x"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_for_non_write_tool():
    r = _run({"tool_name": "Read", "tool_input": {}})
    assert r.returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(HOOK)], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=60)
    assert r.returncode == 0


class TestWiring:
    def test_registered_on_posttooluse(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PostToolUse", []):
            for h in grp.get("hooks", []):
                if "post-wiki-edit" in h.get("command", "") or "post_wiki_edit" in h.get("command", ""):
                    return
        raise AssertionError("post_wiki_edit must be registered on PostToolUse")
