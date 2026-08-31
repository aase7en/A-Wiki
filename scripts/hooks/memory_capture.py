"""memory_capture.py — Neural Spine hook: auto-capture events to Memory Ledger.

Wires the brain's auto-memory on three triggers:
  PostToolUse Bash(git commit) → type=decision (commit subject + changed files)
  Stop                         → type=outcome  (session summary)
  UserPromptSubmit /remember   → type per arg  (manual add via slash command)

ALWAYS exits 0. Observes only — never blocks. Override: HOOK_SKIP=memory_capture.

Iron Law #6: commit messages pass through memory_ledger._redact() so a stray
API key in a commit message cannot leak into the persisted ledger.

Iron Law #5 note: this is a hook, NOT a protected config file. Safe to edit.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Path setup so this hook can be invoked from any cwd (Claude Code runs hooks
# with cwd = repo root, but tests invoke it from elsewhere).
HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import memory_ledger  # noqa: E402 -- chunk 2
LEDGER_PATH = Path(os.environ.get(
    "AWIKI_MEMORY_LEDGER_PATH", str(REPO_ROOT / ".tmp" / "memory-ledger.jsonl")
))


# Patterns that identify a Bash command as a real git commit (not just a
# commit-hash lookup, log, etc.).
_COMMIT_CMD_RE = re.compile(r"\bgit\s+commit\b")
# Extract subject from `git commit -m "subject"` form (inline).
_INLINE_MSG_RE = re.compile(r'-m\s+"([^"]+)"|-m\s+\'([^\']+)\'|-m\s+([^\s]+)')
# Extract subject from `git commit` *output*: line starts with `[<branch> <hash>]`.
_OUTPUT_SUBJECT_RE = re.compile(r"^\[[^\]]+\]\s*(.+)$", re.MULTILINE)


def parse_commit_message(hook_input: dict) -> str | None:
    """Return the commit subject if this event is a successful git commit, else None.

    Tries the tool output first (most accurate — git prints `[branch hash] subject`),
    falls back to parsing -m flag from the command.
    """
    if not isinstance(hook_input, dict):
        return None
    tool_input = hook_input.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not _COMMIT_CMD_RE.search(command):
        return None
    # Skip commit-tree, commit-graph (git subcommands that contain "commit" but
    # aren't the commit-creation command).
    if re.search(r"\bgit\s+commit-(tree|graph|fixup)\b", command):
        return None

    tool_response = hook_input.get("tool_response") or {}
    output = tool_response.get("output", "") if isinstance(tool_response, dict) else ""

    # Prefer the actual subject from git's output.
    if isinstance(output, str):
        m = _OUTPUT_SUBJECT_RE.search(output)
        if m:
            return m.group(1).strip()

    # Fallback: parse -m flag from the command line.
    m = _INLINE_MSG_RE.search(command)
    if m:
        # Three groups for "..." / '...' / unquoted
        return (m.group(1) or m.group(2) or m.group(3) or "").strip()

    return None


def _session_id_from_env() -> str:
    """Best-effort session identifier from env. Falls back to 'unknown'."""
    # ZCode / Claude Code export different env vars; pick whichever exists.
    for key in ("ZCODE_SESSION_ID", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID",
                "HERMES_SESSION_ID", "SESSION_ID"):
        v = os.environ.get(key)
        if v:
            return v
    return "unknown"


def capture_commit(
    *,
    ledger_path: Path,
    session_id: str,
    commit_message: str,
    changed_files: list[str] | None = None,
) -> None:
    """Write one decision entry for a commit. Best-effort: never raises."""
    try:
        memory_ledger.MemoryLedger(ledger_path).append(
            session_id=session_id,
            type="decision",
            summary=commit_message or "(empty commit message)",
            files=changed_files or [],
            tags=["commit"],
        )
    except Exception as e:
        sys.stderr.write(f"[memory_capture] commit capture failed: {e}\n")


def capture_stop(
    *,
    ledger_path: Path,
    session_id: str,
    session_summary: str,
) -> None:
    """Write one outcome entry at session end. Best-effort: never raises."""
    try:
        memory_ledger.MemoryLedger(ledger_path).append(
            session_id=session_id,
            type="outcome",
            summary=session_summary or "(session ended)",
            tags=["stop"],
        )
    except Exception as e:
        sys.stderr.write(f"[memory_capture] stop capture failed: {e}\n")


def replay_for_session_start(
    ledger_path: Path,
    *,
    limit: int = 5,
    interest_tags: list[str] | None = None,
) -> str:
    """Format recent ledger entries for SessionStart context injection.

    Returns a human-readable string with the most recent decisions, lessons,
    and outcomes. Returns "" if the ledger is empty or missing. Never raises.

    Used by scripts/hooks/session_start.py to surface muscle-memory from
    prior sessions at the top of every new session — solves the
    cross-session continuity gap.
    """
    try:
        ledger = memory_ledger.MemoryLedger(ledger_path)
        entries = ledger.replay_for_context(
            interest_tags=interest_tags,
            limit=limit,
        )
    except Exception:
        return ""
    if not entries:
        return ""
    lines = ["🧠 Memory Ledger (recent decisions/lessons/outcomes from prior sessions):"]
    for e in entries:
        ts_str = ""
        try:
            import time as _t
            ts_str = _t.strftime("%Y-%m-%d %H:%M", _t.localtime(e.get("ts", 0)))
        except Exception:
            ts_str = ""
        etype = e.get("type", "?")
        summary = e.get("summary", "")
        tags = ", ".join(e.get("tags", [])) or "-"
        lines.append(f"  [{ts_str}] {etype}: {summary}  (tags: {tags})")
    return "\n".join(lines)


def _commit_oid_from_output(hook_input: dict) -> str | None:
    """Extract the commit OID printed by a successful ``git commit``.

    Git can decorate root commits inside the bracket (``(root-commit)``), so
    take the final hex token before ``]`` instead of assuming a fixed layout.
    No printed OID means no structural evidence: callers must not guess HEAD.
    """
    if not isinstance(hook_input, dict):
        return None
    response = hook_input.get("tool_response") or {}
    output = response.get("output", "") if isinstance(response, dict) else ""
    if not isinstance(output, str):
        return None
    for line in output.splitlines():
        m = re.match(r"^\[([^\]]+)\]\s+.+$", line)
        if not m:
            continue
        tokens = m.group(1).split()
        if tokens and re.fullmatch(r"[0-9a-fA-F]{4,64}", tokens[-1]):
            return tokens[-1]
    return None


def _normalize_repo_path(value: object) -> str | None:
    """Return a canonical repo-relative POSIX path, or None if unsafe."""
    if not isinstance(value, str):
        return None
    raw = value.strip().replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    if (not raw or raw.startswith("/") or raw.startswith("//")
            or re.match(r"^[A-Za-z]:", raw)):
        return None
    parts = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == ".." or any(ord(ch) < 32 for ch in part):
            return None
        parts.append(part)
    return "/".join(parts) or None


def _changed_files_for_commit(
    hook_input: dict,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Read changed paths from the exact commit proven by hook output.

    ``--no-renames`` keeps both old and new paths for renames, ``--root``
    covers first commits, ``-m`` covers merge-parent diffs, and ``-z`` makes
    raw Git path records unambiguous before repo-path safety normalization.
    Control-character/escaping paths are rejected. This hook is soft: unavailable
    Git evidence degrades to [] rather than blocking the session.
    """
    oid = _commit_oid_from_output(hook_input)
    if not oid:
        return []
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    try:
        proc = subprocess.run(
            ["git", "diff-tree", "--root", "-m", "--no-renames",
             "--no-commit-id", "--name-only", "-r", "-z", oid],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    normalized = {
        path for raw in proc.stdout.split("\0")
        if raw and (path := _normalize_repo_path(raw)) is not None
    }
    return sorted(normalized)


def main() -> int:
    """Hook entry point. Reads JSON from stdin, writes to ledger, exits 0."""
    if "memory_capture" in os.environ.get("HOOK_SKIP", ""):
        return 0

    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # never block on malformed input

    if not isinstance(hook_input, dict):
        return 0

    session_id = _session_id_from_env()

    # Trigger 1: successful git commit → decision
    try:
        msg = parse_commit_message(hook_input)
    except Exception:
        msg = None
    if msg:
        files = _changed_files_for_commit(hook_input)
        capture_commit(
            ledger_path=LEDGER_PATH,
            session_id=session_id,
            commit_message=msg,
            changed_files=files,
        )

    return 0  # ALWAYS


if __name__ == "__main__":
    sys.exit(main())
