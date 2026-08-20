"""Tests for scripts/hooks/check_test_before_code.py — Iron Law #1 gate.

Iron Law #1: NO production code without a failing test first.
This hook turns the soft prompt-rule into a PreToolUse hard-enforce gate.

Pattern A (subprocess) — mirrors tests/test_a_focus_hook.py.

Coverage:
  - Pass when no new public symbol (refactor/docstring/config)
  - Block when new def/class added without test in working tree
  - Pass when a tests/test_*.py is also staged
  - Whitelist: __init__.py, conftest.py, *.config.py
  - HOOK_SKIP override (substring, comma-separated)
  - Test files themselves are not gated
  - Fail-open on non-JSON stdin / parse errors
  - TestWiring: hook is registered in .claude/settings.json PreToolUse
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_test_before_code.py"


def run_hook(
    payload: dict,
    *,
    env_extra: dict | None = None,
    staged_files: list[str] | None = None,
) -> subprocess.CompletedProcess:
    """Invoke the hook as a subprocess with the PreToolUse payload on stdin.

    `staged_files` — when provided, monkeypatches `git diff --name-only`
    by writing the list to a sidecar that the hook reads via env var
    AWIKI_STAGED_FILES (used for testing without touching the real git index).
    """
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env.update(env_extra or {})
    if staged_files is not None:
        # The hook honors AWIKI_STAGED_FILES override (newline-separated)
        # so tests do not need to actually stage git files.
        env["AWIKI_STAGED_FILES"] = "\n".join(staged_files)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )


def write_payload(file_path: str, content: str = "", *, tool: str = "Write",
                  old_string: str = "", new_string: str = "") -> dict:
    """Build a PreToolUse payload for Write or Edit."""
    tool_input: dict = {"file_path": file_path}
    if tool == "Write":
        tool_input["content"] = content
    else:  # Edit / MultiEdit
        tool_input["old_string"] = old_string
        tool_input["new_string"] = new_string
    return {"tool_name": tool, "tool_input": tool_input}


# ---------------------------------------------------------------------------
# 1. Pass cases (no new public symbol → not subject to Iron Law #1)
# ---------------------------------------------------------------------------
def test_passes_when_edit_has_no_new_symbol():
    """Editing an existing function body (no new def/class) → pass."""
    payload = write_payload(
        "scripts/lib/example.py",
        tool="Edit",
        old_string="return 1",
        new_string="return 2",
    )
    r = run_hook(payload)
    assert r.returncode == 0, f"expected pass, got block: {r.stderr}"


def test_passes_when_only_docstring_added():
    """Adding a docstring (no def/class) → pass."""
    payload = write_payload(
        "scripts/lib/example.py",
        content='"""Module docstring only."""\n',
    )
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 2. Block cases (new public symbol + no test in working tree)
# ---------------------------------------------------------------------------
def test_blocks_new_public_function_without_test():
    """Writing a new public def in scripts/lib/*.py with no test → block (exit 2)."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="def public_function():\n    return 42\n",
    )
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    assert r.returncode == 2, (
        f"expected block (exit 2), got {r.returncode}; "
        f"stderr={r.stderr!r}"
    )
    assert "Iron Law #1" in r.stderr or "test" in r.stderr.lower()


def test_blocks_new_class_without_test():
    """Writing a new class in scripts/lib/*.py with no test → block."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="class MyClass:\n    pass\n",
    )
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    assert r.returncode == 2


def test_blocks_async_def_without_test():
    """Writing a new async def → block."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="async def fetch():\n    return 1\n",
    )
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    assert r.returncode == 2


def test_allows_private_function_without_test():
    """A leading-underscore def (_private) is convention-private → allow.

    Iron Law #1 is about public API surface; private helpers that get
    exercised via the public API's tests are fine.
    """
    payload = write_payload(
        "scripts/lib/example.py",
        content="def _helper():\n    return 0\n",
    )
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    # _helper is convention-private → not subject to gate
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 3. Pass when test is in working tree
# ---------------------------------------------------------------------------
def test_passes_when_test_file_is_staged_alongside():
    """New public function + tests/test_example.py in staged → pass."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="def public_function():\n    return 42\n",
    )
    r = run_hook(
        payload,
        staged_files=["scripts/lib/example.py", "tests/test_example.py"],
    )
    assert r.returncode == 0


def test_passes_when_test_file_has_different_name_pattern():
    """Test files matching tests/test_*.py or tests/**/test_*.py → pass."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="def public_function():\n    return 42\n",
    )
    r = run_hook(
        payload,
        staged_files=["scripts/lib/example.py", "tests/sub/test_example.py"],
    )
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 4. Whitelist (false-positive prevention)
# ---------------------------------------------------------------------------
def test_whitelist_init_py():
    """__init__.py edits are config/import reorganization → not gated."""
    payload = write_payload(
        "scripts/lib/__init__.py",
        content="from .example import public_function\n",
    )
    r = run_hook(payload, staged_files=["scripts/lib/__init__.py"])
    assert r.returncode == 0


def test_whitelist_conftest_py():
    """conftest.py edits are pytest fixtures → not gated."""
    payload = write_payload(
        "tests/conftest.py",
        content="import pytest\n",
    )
    r = run_hook(payload, staged_files=["tests/conftest.py"])
    assert r.returncode == 0


def test_whitelist_test_files_themselves():
    """Editing a tests/*.py file → not gated (it IS a test)."""
    payload = write_payload(
        "tests/test_example.py",
        content="def test_foo():\n    assert True\n",
    )
    r = run_hook(payload, staged_files=["tests/test_example.py"])
    assert r.returncode == 0


def test_whitelist_non_python_files():
    """Editing a .md, .json, .yaml file → not gated."""
    payload = write_payload(
        "README.md",
        content="# docs\n",
    )
    r = run_hook(payload, staged_files=["README.md"])
    assert r.returncode == 0


def test_whitelist_outside_lib_dir():
    """Editing a python file OUTSIDE scripts/lib/ and scripts/hooks/ → not gated."""
    payload = write_payload(
        "docs/gen.py",
        content="def gen():\n    return 0\n",
    )
    r = run_hook(payload, staged_files=["docs/gen.py"])
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 5. HOOK_SKIP override (substring, comma-separated)
# ---------------------------------------------------------------------------
def test_hook_skip_exact_match():
    """HOOK_SKIP=check_test_before_code → skip."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="def public_function():\n    return 42\n",
    )
    r = run_hook(
        payload,
        env_extra={"HOOK_SKIP": "check_test_before_code"},
        staged_files=["scripts/lib/example.py"],
    )
    assert r.returncode == 0


def test_hook_skip_substring_in_comma_list():
    """HOOK_SKIP='check_test_before_code,other_hook' → also skip."""
    payload = write_payload(
        "scripts/lib/example.py",
        content="def public_function():\n    return 42\n",
    )
    r = run_hook(
        payload,
        env_extra={"HOOK_SKIP": "check_test_before_code,other_hook"},
        staged_files=["scripts/lib/example.py"],
    )
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 6. Fail-open (parse errors, non-edit tools)
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin(tmp_path):
    """Garbage stdin → pass (never crash a PreToolUse gate on bad input)."""
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not valid json {{{",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    assert r.returncode == 0


def test_passes_for_read_tool():
    """Read/Glob/Grep tools are never gated (navigation, not authoring)."""
    payload = {"tool_name": "Read", "tool_input": {"file_path": "scripts/lib/example.py"}}
    r = run_hook(payload)
    assert r.returncode == 0


def test_passes_for_bash_tool():
    """Bash tool is never gated."""
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    r = run_hook(payload)
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 7. File-path field variants (tools use different keys)
# ---------------------------------------------------------------------------
def test_passes_with_path_field_instead_of_file_path():
    """Some tools use 'path' instead of 'file_path' → still parsed."""
    payload = {
        "tool_name": "Write",
        "tool_input": {"path": "scripts/lib/example.py", "content": "x = 1\n"},
    }
    r = run_hook(payload, staged_files=["scripts/lib/example.py"])
    # x = 1 has no new def/class → pass
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 8. TestWiring — hook must be registered in settings.json PreToolUse
# ---------------------------------------------------------------------------
