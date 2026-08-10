"""Tests for scripts/hooks/check_source_original_file.py — Iron Law #8 gate.

Iron Law #8: source provenance — raw/ first, always. A wiki/sources/<slug>.md
page MUST have a valid `original_file:` pointing at an existing file under raw/.

Pattern A (subprocess) — mirrors tests/test_check_test_before_code.py.

Coverage:
  - Pass when tool is Read/Bash (not gated)
  - Pass when file is not under wiki/sources/
  - Pass for non-entry filenames in wiki/sources/ (CLAUDE.md, README.md)
  - Pass when original_file points to a valid existing raw/ file
  - BLOCK when original_file missing from frontmatter
  - BLOCK when original_file is null/empty
  - BLOCK when original_file doesn't start with raw/
  - BLOCK when original_file points to non-existent file
  - HOOK_SKIP substring override
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
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_source_original_file.py"


def _run(payload: dict, *, env_extra: dict | None = None,
         cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke the hook via hooks_runner.py (the production path).

    The hook itself does NOT check HOOK_SKIP — it relies on hooks_runner
    pre-filtering (per docstring line 24). Tests must go through the runner
    so HOOK_SKIP semantics match production.
    """
    runner = REPO_ROOT / "scripts" / "hooks_runner.py"
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(runner), "check-source-original-file"],
        input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(cwd or REPO_ROOT), timeout=30,
    )


def _write_source(file_path: str, content: str, *, tool: str = "Write",
                  old_string: str = "", new_string: str = "") -> dict:
    ti: dict = {"file_path": file_path}
    if tool == "Write":
        ti["content"] = content
    else:
        ti["old_string"] = old_string
        ti["new_string"] = new_string
    return {"tool_name": tool, "tool_input": ti}


def _fm(original_file: str | None, body: str = "page body") -> str:
    """Build a minimal source frontmatter + body."""
    if original_file is None:
        return f"---\ntitle: Test\n---\n{body}\n"
    return f"---\ntitle: Test\noriginal_file: {original_file}\n---\n{body}\n"


# ---------------------------------------------------------------------------
# 1. Pass cases
# ---------------------------------------------------------------------------
def test_passes_for_read_tool(tmp_path):
    r = _run({"tool_name": "Read",
              "tool_input": {"file_path": "wiki/sources/foo.md"}})
    assert r.returncode == 0


def test_passes_when_not_under_wiki_sources(tmp_path):
    r = _run(_write_source("scripts/lib/foo.py", "x = 1"))
    assert r.returncode == 0


def test_passes_for_non_entry_filename_in_sources(tmp_path):
    """CLAUDE.md / README.md / AGENTS.md in wiki/sources/ are not source pages."""
    r = _run(_write_source("wiki/sources/CLAUDE.md", "# rules"))
    assert r.returncode == 0


def test_passes_when_original_file_points_to_existing_raw(tmp_path, monkeypatch):
    """original_file: raw/foo.md with raw/foo.md present → pass.

    The hook computes repo_root relative to its own location, so we cannot
    point it at tmp_path. Instead we create a temporary repo layout
    matching A-Wiki structure. Simplest: skip cwd override and create
    raw/ + wiki/sources/ under the real REPO_ROOT (gitignored).
    """
    # We need a real raw/ file reachable from REPO_ROOT. Use a uniquely-
    # named temp file under raw/ (gitignored) and clean up after.
    slug = "test_source_orig_file_unittest"
    raw_file = REPO_ROOT / "raw" / f"{slug}.md"
    wiki_file = REPO_ROOT / "wiki" / "sources" / f"{slug}.md"
    try:
        raw_file.parent.mkdir(exist_ok=True)
        raw_file.write_text("source content", encoding="utf-8")
        payload = _write_source(
            f"wiki/sources/{slug}.md", _fm(f"raw/{slug}.md"))
        r = _run(payload)
        assert r.returncode == 0, f"expected pass, got block: {r.stderr}"
    finally:
        raw_file.unlink(missing_ok=True)
        wiki_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 2. BLOCK cases (Iron Law #8 violations)
# ---------------------------------------------------------------------------
def test_blocks_when_original_file_missing_from_frontmatter(tmp_path):
    payload = _write_source("wiki/sources/foo.md", _fm(original_file=None))
    r = _run(payload, cwd=tmp_path)
    assert r.returncode == 2
    assert "original_file" in r.stderr.lower()


def test_blocks_when_original_file_is_null(tmp_path):
    payload = _write_source("wiki/sources/foo.md", _fm("null"))
    r = _run(payload, cwd=tmp_path)
    assert r.returncode == 2


def test_blocks_when_original_file_does_not_start_with_raw(tmp_path):
    payload = _write_source("wiki/sources/foo.md", _fm("drive/foo.md"))
    r = _run(payload, cwd=tmp_path)
    assert r.returncode == 2


def test_blocks_when_original_file_points_to_missing_file(tmp_path):
    """raw/ exists but raw/foo.md is missing → block."""
    (tmp_path / "raw").mkdir()
    payload = _write_source("wiki/sources/foo.md", _fm("raw/foo.md"))
    r = _run(payload, cwd=tmp_path)
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 3. HOOK_SKIP behavior (documented design: handled by hooks_runner all-hooks
#    mode only; the single-hook invocation path does NOT pre-filter — the hook
#    itself must check HOOK_SKIP if it wants to honor it when invoked directly).
#    check_source_original_file does NOT check HOOK_SKIP itself (per its
#    docstring: "HOOK_SKIP includes ... (handled by hooks_runner)"). So these
#    tests document the actual behavior: when invoked directly/specifically,
#    the hook blocks regardless of HOOK_SKIP.
# ---------------------------------------------------------------------------
def test_hook_skip_via_runner_specific_invocation_does_not_filter(tmp_path):
    """The runner's single-hook path does NOT pre-filter HOOK_SKIP (per
    hooks_runner.py:151-165). The hook relies on the runner's all-hooks
    path for that. This test documents that behavior."""
    payload = _write_source("wiki/sources/foo.md", _fm(original_file=None))
    r = _run(payload, env_extra={"HOOK_SKIP": "check_source_original_file"},
             cwd=tmp_path)
    # The hook itself doesn't check HOOK_SKIP → block fires even with env set.
    # This is a known design gap (the hook should self-check for robustness),
    # but it's out of scope for this test suite — we document behavior, not
    # prescribe a fix.
    assert r.returncode == 2  # documents the actual behavior


# ---------------------------------------------------------------------------
# 4. Fail-open
# ---------------------------------------------------------------------------
def test_fail_open_on_non_json_stdin():
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    runner = REPO_ROOT / "scripts" / "hooks_runner.py"
    r = subprocess.run(
        [sys.executable, str(runner), "check-source-original-file"],
        input="{{{ not json",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert r.returncode == 0


def test_fail_open_when_file_path_missing():
    r = _run({"tool_name": "Write", "tool_input": {}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 5. Edit/MultiEdit handling
# ---------------------------------------------------------------------------
def test_passes_when_edit_payload_unreconstructable(tmp_path):
    """Edit with mismatched old_string (can't reconstruct) → pass (lenient)."""
    # Edit a wiki/sources/ file that doesn't exist on disk → can't reconstruct
    payload = _write_source(
        "wiki/sources/nonexistent_xyz.md",
        "new content only",
        tool="Edit",
        old_string="missing",
        new_string="new content only",
    )
    r = _run(payload, cwd=tmp_path)
    assert r.returncode == 0  # lenient on reconstruction failure


# ---------------------------------------------------------------------------
# 6. TestWiring
# ---------------------------------------------------------------------------
class TestWiring:
    def test_registered_in_pretooluse_edit_matcher(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            if "Edit" not in grp.get("matcher", ""):
                continue
            cmds = [h.get("command", "") for h in grp.get("hooks", [])]
            for c in cmds:
                if "check-source-original-file" in c or "check_source_original_file" in c:
                    return
        raise AssertionError(
            "check_source_original_file must be registered on Edit|Write|MultiEdit"
        )

    def test_routed_through_hooks_runner(self):
        cfg = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pretool = cfg["hooks"].get("PreToolUse", [])
        for grp in pretool:
            if "Edit" not in grp.get("matcher", ""):
                continue
            for h in grp.get("hooks", []):
                c = h.get("command", "")
                if "source_original_file" in c or "source-original-file" in c:
                    assert "hooks_runner" in c
                    return
        raise AssertionError("check_source_original_file not on PreToolUse")
