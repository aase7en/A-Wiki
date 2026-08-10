"""Tests for .codex/hooks.json parity with .claude/settings.json.

P0-2: Codex was missing 8 fixable hooks + 3 platform-limited (UserPromptSubmit).
This test pins the parity contract: every Claude hook event that Codex
also supports must carry the same hook commands.

Platform limit (documented): Codex does not support UserPromptSubmit —
its substitutes are MCP tools (skill_route, memory_recall) per AGENTS.md
substrate table. Those are not in this config file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_CFG = REPO_ROOT / ".claude" / "settings.json"
CODEX_CFG = REPO_ROOT / ".codex" / "hooks.json"

# Codex platform limit (per AGENTS.md substrate table):
# "Codex 5 ไม่มี UserPromptSubmit" — these 3 hooks have MCP substitutes.
PLATFORM_LIMITED = {
    ("UserPromptSubmit", "check_a_route.py"),
    ("UserPromptSubmit", "check_compaction_suggest.py"),
    ("UserPromptSubmit", "recall_on_prompt.py"),
}


def _hooks_by_event(cfg_path: Path) -> dict[str, set[tuple[str, str]]]:
    """Return {event: set of (matcher, hook_name)} tuples from a config."""
    d = json.loads(cfg_path.read_text(encoding="utf-8"))
    out: dict[str, set[tuple[str, str]]] = {}
    for event, entries in d.get("hooks", {}).items():
        if not isinstance(entries, list):
            continue
        bucket: set[tuple[str, str]] = set()
        for grp in entries:
            matcher = grp.get("matcher", "")
            for h in grp.get("hooks", []):
                cmd = h.get("command", "")
                # Extract the hook identifier from a command string
                # Three forms:
                #   python3 scripts/hooks_runner.py check-foo-bar
                #   python3 scripts/hooks/foo.py
                #   bash .codex/hooks/foo.sh OR .claude/hooks/foo.sh
                m = re.search(r"hooks_runner\.py\s+([\w-]+)", cmd)
                if m:
                    name = m.group(1).replace("-", "_") + ".py"
                else:
                    m = re.search(r"(?:scripts/hooks/|\.claude/hooks/|\.codex/hooks/|scripts/)([^/\s]+\.sh|[^/\s]+\.py)", cmd)
                    name = m.group(1) if m else cmd
                bucket.add((matcher, name))
        out[event] = bucket
    return out


# ---------------------------------------------------------------------------
# 1. Parity test — every Codex-supported event mirrors Claude
# ---------------------------------------------------------------------------
def test_codex_pretooluse_edit_hooks_match_claude():
    """The Edit|Write|MultiEdit PreToolUse hooks must match Claude's set."""
    claude = _hooks_by_event(CLAUDE_CFG)
    codex = _hooks_by_event(CODEX_CFG)
    c = {n for m, n in claude.get("PreToolUse", set()) if m == "Edit|Write|MultiEdit"}
    x = {n for m, n in codex.get("PreToolUse", set()) if m == "Edit|Write|MultiEdit"}
    missing = c - x
    assert not missing, (
        f"Codex PreToolUse Edit|Write|MultiEdit missing vs Claude: {missing}"
    )


def test_codex_pretooluse_agent_hooks_match_claude():
    """Agent matcher PreToolUse hooks must match."""
    claude = _hooks_by_event(CLAUDE_CFG)
    codex = _hooks_by_event(CODEX_CFG)
    c = {n for m, n in claude.get("PreToolUse", set()) if m == "Agent"}
    x = {n for m, n in codex.get("PreToolUse", set()) if m == "Agent"}
    missing = c - x
    assert not missing, f"Codex PreToolUse Agent missing: {missing}"


def test_codex_posttooluse_agent_matcher_exists():
    """PostToolUse Agent matcher (log-subagent-result) must be present."""
    codex = _hooks_by_event(CODEX_CFG)
    agent_matchers = {(m, n) for m, n in codex.get("PostToolUse", set()) if m == "Agent"}
    assert agent_matchers, (
        "Codex PostToolUse Agent matcher missing — log-subagent-result should be there"
    )


def test_codex_sessionstart_parity():
    claude = _hooks_by_event(CLAUDE_CFG)
    codex = _hooks_by_event(CODEX_CFG)
    c = claude.get("SessionStart", set())
    x = codex.get("SessionStart", set())
    missing = c - x
    assert not missing, f"Codex SessionStart missing: {missing}"


def test_codex_stop_parity():
    """Stop event must mirror Claude (self_audit, a_loop_distill,
    check_verify_before_done, release_agent_claims, a_focus_stop)."""
    claude = _hooks_by_event(CLAUDE_CFG)
    codex = _hooks_by_event(CODEX_CFG)
    c = claude.get("Stop", set())
    x = codex.get("Stop", set())
    missing = c - x
    assert not missing, f"Codex Stop missing: {missing}"


# ---------------------------------------------------------------------------
# 2. Critical individual hooks present in Codex
# ---------------------------------------------------------------------------
def test_codex_has_check_test_before_code():
    """Iron Law #1 hard-enforce must be wired in Codex too."""
    codex = _hooks_by_event(CODEX_CFG)
    names = {n for m, n in codex.get("PreToolUse", set())}
    assert "check_test_before_code.py" in names, (
        "Codex missing check_test_before_code — Iron Law #1 not enforced in Codex!"
    )


def test_codex_has_a_loop_distill_on_stop():
    """a-loop Phase 3 distill must run on Stop in Codex too."""
    codex = _hooks_by_event(CODEX_CFG)
    names = {n for m, n in codex.get("Stop", set())}
    assert "a_loop_distill.py" in names, "Codex Stop missing a_loop_distill"


def test_codex_has_check_verify_before_done_on_stop():
    codex = _hooks_by_event(CODEX_CFG)
    names = {n for m, n in codex.get("Stop", set())}
    assert "check_verify_before_done.py" in names


def test_codex_has_check_a_flow_discipline():
    codex = _hooks_by_event(CODEX_CFG)
    names = {n for m, n in codex.get("PreToolUse", set())}
    assert "check_a_flow_discipline.py" in names


# ---------------------------------------------------------------------------
# 3. Platform limit documentation (Codex has no UserPromptSubmit)
# ---------------------------------------------------------------------------
def test_codex_userpromptsubmit_absence_is_documented_platform_limit():
    """Codex does NOT support UserPromptSubmit event — its substitutes are
    MCP tools (skill_route, memory_recall) per AGENTS.md substrate table.

    This test documents the platform limit. If Codex ever adds
    UserPromptSubmit support, this test should be updated to require parity.
    """
    codex = _hooks_by_event(CODEX_CFG)
    assert "UserPromptSubmit" not in codex, (
        "Codex now supports UserPromptSubmit! Update this test + add the 3 "
        "missing hooks (check_a_route, check_compaction_suggest, recall_on_prompt) "
        "to achieve full parity."
    )


# ---------------------------------------------------------------------------
# 4. JSON validity sanity check
# ---------------------------------------------------------------------------
def test_codex_hooks_json_is_valid_json():
    d = json.loads(CODEX_CFG.read_text(encoding="utf-8"))
    assert "hooks" in d
    assert isinstance(d["hooks"], dict)


def test_codex_hook_commands_resolve_to_real_files():
    """Every hook command must reference a file that exists in the repo."""
    d = json.loads(CODEX_CFG.read_text(encoding="utf-8"))
    for event, entries in d.get("hooks", {}).items():
        if not isinstance(entries, list):
            continue
        for grp in entries:
            for h in grp.get("hooks", []):
                cmd = h.get("command", "")
                # Extract path from command — only check python/bash file refs
                m = re.search(
                    r"((?:scripts|\.codex|\.claude)/[^\s]+\.(?:py|sh))",
                    cmd,
                )
                if not m:
                    continue
                p = m.group(1).replace("\\", "/")
                # Codex uses .codex/hooks/<x>.sh as symlinks to .claude/hooks/
                # so check existence of either
                if p.startswith(".codex/hooks/") and not (REPO_ROOT / p).exists():
                    # Fall back to .claude/hooks/<same-name>
                    cl = ".claude/hooks/" + p.split("/")[-1]
                    assert (REPO_ROOT / cl).exists(), (
                        f"[{event}] {p} missing AND no .claude fallback at {cl}"
                    )
                else:
                    assert (REPO_ROOT / p).exists(), (
                        f"[{event}] hook command references missing file: {p}"
                    )
