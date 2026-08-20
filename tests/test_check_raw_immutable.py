"""Tests for scripts/hooks/check_raw_immutable.py — Iron Law #4 gate.

Iron Law #4: raw/ is immutable — never edit or delete (hook-protected).
This hook blocks (exit 2) any Edit/Write/MultiEdit landing inside raw/.

Pattern A (subprocess) — mirrors tests/test_check_secret_leak.py.

Coverage:
  - Pass for non-gate tools (Read/Bash/Glob)
  - Pass when file_path is outside raw/
  - BLOCK when file_path is under raw/
  - BLOCK when file_path uses absolute path inside raw/
  - BLOCK when file_path uses drive/raw/ alias (junction-resolved)
  - Pass when file_path missing
  - Fail-open on non-JSON stdin
  - TestWiring: registered on PreToolUse Edit|Write|MultiEdit
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_raw_immutable.py"


def _run(payload: dict, *, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


def _edit(file_path: str) -> dict:
    return {"tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"}}


# ---------------------------------------------------------------------------
# 1. Pass cases
# ---------------------------------------------------------------------------
def test_passes_for_read_tool():
    payload = {"tool_name": "Read", "tool_input": {"file_path": "raw/foo.md"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_for_bash_tool():
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls raw/"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_for_grep_tool():
    payload = {"tool_name": "Grep", "tool_input": {"pattern": "x", "path": "raw/"}}
    r = _run(payload)
    assert r.returncode == 0


def test_passes_when_file_outside_raw():
    """Editing scripts/lib/foo.py → pass."""
    r = _run(_edit("scripts/lib/foo.py"))
    assert r.returncode == 0


def test_passes_when_wiki_sources():
    """Editing wiki/sources/foo.md → pass (not under raw/)."""
    r = _run(_edit("wiki/sources/foo.md"))
    assert r.returncode == 0


def test_passes_when_file_path_missing():
    """Edit payload without file_path → pass."""
    r = _run({"tool_name": "Write", "tool_input": {}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 2. BLOCK cases (Iron Law #4 violations)
# ---------------------------------------------------------------------------
def test_blocks_edit_to_raw_relative_path():
    """Editing raw/foo.md → block."""
    r = _run(_edit("raw/foo.md"))
    assert r.returncode == 2
    assert "immutable" in r.stderr.lower() or "raw" in r.stderr.lower()


def test_blocks_write_to_nested_raw_file():
    """Editing raw/sub/deep.md → block."""
    r = _run(_edit("raw/sub/deep.md"))
    assert r.returncode == 2


def test_blocks_multiedit_to_raw():
    """MultiEdit on raw/ → block."""
    payload = {"tool_name": "MultiEdit",
               "tool_input": {"file_path": "raw/foo.md", "edits": []}}
    r = _run(payload)
    assert r.returncode == 2


def test_blocks_absolute_path_under_raw():
    """Editing via absolute path /repo/raw/foo.md → block."""
    abs_raw = str(REPO_ROOT / "raw" / "foo.md").replace("\\", "/")
    r = _run(_edit(abs_raw))
    assert r.returncode == 2


def test_blocks_dot_slash_raw():
    """Editing ./raw/foo.md → block (path normalization)."""
    r = _run(_edit("./raw/foo.md"))
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 3. Fail-open
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin():
    env = dict(os.environ)
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{{{ broken json",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert r.returncode == 0


def test_fail_open_on_non_edit_payload():
    """A tool_name that's not Edit/Write/MultiEdit → pass."""
    r = _run({"tool_name": "WebFetch", "tool_input": {"file_path": "raw/foo.md"}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 4. TestWiring
# ---------------------------------------------------------------------------
