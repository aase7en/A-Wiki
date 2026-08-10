"""Tests for scripts/hooks/check_output_format.py — 3-layer output protocol.

BLOCKs HTML written into source-of-truth dirs (wiki/, docs/, CLAUDE.md).
Allows compact JSON/CSV/JSONL. Allows HTML in exports/html/ (gitignored).

Pattern A (subprocess).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_output_format.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def _write(file_path: str, content: str = "<html></html>") -> dict:
    return {"tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": content}}


def test_passes_for_non_edit_tool():
    assert _run({"tool_name": "Bash", "tool_input": {}}).returncode == 0


def test_passes_for_markdown_in_wiki():
    r = _run(_write("wiki/foo.md", "# title\n"))
    assert r.returncode == 0


def test_passes_for_json_file():
    r = _run(_write("data/foo.json", "{}"))
    assert r.returncode == 0


def test_blocks_html_in_wiki():
    r = _run(_write("wiki/foo.html"))
    assert r.returncode == 2


def test_blocks_html_in_docs():
    r = _run(_write("docs/foo.html"))
    assert r.returncode == 2


def test_passes_for_html_in_exports():
    r = _run(_write("exports/html/foo.html"))
    assert r.returncode == 0


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
                    if "output-format" in h.get("command", "") or "output_format" in h.get("command", ""):
                        return
        raise AssertionError("check_output_format must be on Edit PreToolUse matcher")
