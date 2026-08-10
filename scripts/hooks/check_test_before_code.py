"""check_test_before_code.py — PreToolUse hook enforcing Iron Law #1.

Iron Law #1: NO production code without a failing test first.

This hook turns the soft prompt-rule into a hard-enforce PreToolUse gate.
When an Edit/Write/MultiEdit adds a NEW public symbol (def/class/async def)
to a production python file (scripts/lib/*.py, scripts/hooks/*.py), the
hook checks that a tests/test_*.py file is also staged in the working tree.
If not → block (exit 2).

Blocks (exit 2) when:
  - tool is Edit/Write/MultiEdit
  - file_path matches scripts/lib/*.py or scripts/hooks/*.py
  - the new content defines a NEW public symbol (def/class/async def, NOT _private)
  - no tests/test_*.py file appears in the staged-files list

Passes through when:
  - HOOK_SKIP contains 'check_test_before_code' (substring, comma-separated)
  - tool is not Edit/Write/MultiEdit (Read/Bash/Glob/Grep/etc.)
  - file_path is whitelisted: __init__.py, conftest.py, setup.py, *.config.py
  - file_path is itself a tests/*.py file (tests are not subject to the gate)
  - file_path is outside scripts/lib/ and scripts/hooks/
  - the new content contains no new public symbol (refactor/docstring/config)
  - a tests/test_*.py file is in the staged list (test was written first)

Exit codes (per hooks_runner convention):
  0 = pass
  2 = BLOCK (Iron Law #1 violation)
  other = error (reported but not blocking)

Override: HOOK_SKIP=check_test_before_code (substring match)

Cross-agent caveat: this hook is wired in .claude/settings.json PreToolUse
and runs in Claude Code only (substrate Hook). Codex/ZCode/Gemini route
through substrate Tool (MCP) or Model-read — those agents must enforce
Iron Law #1 manually until a substrate-equivalent is built (Phase 2).

Rationale: Iron Law #1 was previously enforced only via prompt; agents
could add new functions to scripts/lib/*.py without a test and commit.
This hook closes that loophole. See:
  - AGENTS.md §Iron Laws (Law #1)
  - tests/test_check_test_before_code.py (TDD contract)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Windows console UTF-8 (Thai messages render correctly)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent

# ── Tools that are NEVER gated (navigation/read/state-mgmt) ──────────────────
EXEMPT_TOOLS = {
    "Bash", "Read", "Glob", "Grep", "TodoWrite", "WebFetch", "WebSearch",
    "Task", "Agent", "Edit",  # Edit/Write/MultiEdit handled below
} - {"Edit"}  # Edit IS gated

GATE_TOOLS = {"Edit", "Write", "MultiEdit"}

# ── Whitelist — filenames that are config/import/fixture, not production logic ──
WHITELIST_NAMES = {
    "__init__.py", "conftest.py", "setup.py", "setup.cfg",
}

WHITELIST_SUFFIXES = (".config.py", ".cfg.py", "_config.py")

# ── Patterns that match NEW public symbols ────────────────────────────────────
# A public symbol = def/class/async def at column 0 (not indented, not nested)
# and does NOT start with underscore (convention-private).
_NEW_PUBLIC_SYMBOL = re.compile(
    r"^(?:async\s+def|def|class)\s+([A-Za-z][A-Za-z0-9_]*)",
    re.MULTILINE,
)


def _emit(msg: str) -> None:
    sys.stderr.write(msg if msg.endswith("\n") else msg + "\n")


def _is_gated_path(file_path: str) -> bool:
    """True iff file_path is a production python file subject to Iron Law #1."""
    if not file_path:
        return False
    # Normalize backslashes + strip leading ./
    p = file_path.replace("\\", "/").lstrip("./")
    # Must end in .py
    if not p.endswith(".py"):
        return False
    # Test files are not gated (they ARE tests)
    if p.startswith("tests/") or "/tests/" in p:
        return False
    # Whitelisted names → config/import, not production logic
    name = p.rsplit("/", 1)[-1]
    if name in WHITELIST_NAMES:
        return False
    if name.endswith(WHITELIST_SUFFIXES):
        return False
    # Only gate scripts/lib/ and scripts/hooks/
    return p.startswith("scripts/lib/") or p.startswith("scripts/hooks/")


def _extract_new_symbols(content: str) -> list[str]:
    """Return list of NEW public symbol names in the given content.

    Convention-private (_leading_underscore) symbols are excluded — Iron Law #1
    is about the public API surface; private helpers are exercised via the
    public API's tests.
    """
    if not content:
        return []
    symbols: list[str] = []
    for m in _NEW_PUBLIC_SYMBOL.finditer(content):
        name = m.group(1)
        if name.startswith("_"):
            continue
        symbols.append(name)
    return symbols


def _new_content_for(tool_name: str, tool_input: dict) -> str:
    """Extract the content that will be WRITTEN by this tool call.

    For Write → tool_input['content'].
    For Edit  → tool_input['new_string'] (the replacement).
    For MultiEdit → concatenation of all edits' new_string.
    Returns '' if nothing extractable (caller treats '' as no-new-symbol → pass).
    """
    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        return "\n".join(e.get("new_string", "") or "" for e in edits)
    return ""


def _staged_files() -> list[str]:
    """Return list of files in the working tree (staged + unstaged changes).

    Honors AWIKI_STAGED_FILES env override (newline-separated) for testing.
    Falls back to `git diff --name-only HEAD` (tracks both staged and unstaged).
    Fail-soft: returns [] on any error.
    """
    override = os.environ.get("AWIKI_STAGED_FILES")
    if override is not None:
        return [line.strip() for line in override.splitlines() if line.strip()]
    try:
        import subprocess
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(REPO_ROOT),
        )
        if r.returncode != 0:
            return []
        return [line.strip() for line in r.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def _has_test_in_staged(staged: list[str]) -> bool:
    """True iff any staged file looks like a pytest test module.

    Accepts tests/test_*.py and tests/**/test_*.py (any depth).
    """
    for f in staged:
        p = f.replace("\\", "/").lstrip("./")
        if "/test_" in p or p.startswith("tests/test_") or p.startswith("test_"):
            if p.endswith(".py"):
                return True
    return False


def evaluate(tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """Return (allowed: bool, reason: str).

    allowed=True → pass (exit 0).
    allowed=False → BLOCK (exit 2), reason is the user-facing message.
    """
    # 1. HOOK_SKIP override (substring, comma-separated)
    if "check_test_before_code" in os.environ.get("HOOK_SKIP", ""):
        return True, ""

    # 2. Only gate Edit/Write/MultiEdit
    if tool_name not in GATE_TOOLS:
        return True, ""

    # 3. Extract file_path (try multiple field names — tools vary)
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )

    # 4. Only gate production paths
    if not _is_gated_path(file_path):
        return True, ""

    # 5. Extract the content that will be written
    new_content = _new_content_for(tool_name, tool_input)
    if not new_content:
        return True, ""  # nothing being written → can't have new symbols

    # 6. Look for new public symbols
    symbols = _extract_new_symbols(new_content)
    if not symbols:
        return True, ""  # refactor/docstring/config — no new public API

    # 7. Has a test been staged alongside?
    staged = _staged_files()
    if _has_test_in_staged(staged):
        return True, ""  # test was written first → Iron Law #1 satisfied

    # 8. BLOCK — new public symbol with no test
    pretty_path = file_path.replace("\\", "/")
    sym_list = ", ".join(symbols[:3])
    if len(symbols) > 3:
        sym_list += f" (+{len(symbols) - 3} more)"
    reason = (
        f"🚫 [check_test_before_code] Blocked Edit: Iron Law #1 violation\n"
        f"   file: {pretty_path}\n"
        f"   new public symbol(s): {sym_list}\n"
        f"   problem: no tests/test_*.py file found in the working tree for this change\n"
        f"   fix: write the failing test FIRST, then re-attempt this edit:\n"
        f"     1. Create tests/test_<module>.py with a test that exercises the new symbol\n"
        f"     2. Confirm it fails (red)\n"
        f"     3. Then re-attempt this edit (gate will pass — test is now staged)\n"
        f"   override (emergency): HOOK_SKIP=check_test_before_code\n"
        f"   see: AGENTS.md §Iron Laws (Law #1)"
    )
    return False, reason


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        # Fail-open: never block on a parse error
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {}) or {}

    try:
        allowed, reason = evaluate(tool_name, tool_input)
    except Exception as e:
        # Fail-open: any internal error → pass (don't block work on a bug)
        sys.stderr.write(f"[check_test_before_code] internal error (fail-open): {e}\n")
        return 0

    if not allowed:
        _emit(reason)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
