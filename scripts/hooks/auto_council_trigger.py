"""auto_council_trigger.py — PostToolUse hook: auto-open council on sensitive edit.

Tier 2 #7+#8 enhancement. Root cause (per /a-debug analysis 2026-07-25):
slash-command-driven council requires user to remember '/A-Council' →
human error → review skipped → bugs ship. This hook removes that step:
when an agent edits a sensitive code file, a council thread is auto-opened
(lazy — no personas invoked, just the thread + 'needs-review' tag).

Flow:
  PostToolUse Edit|Write on scripts/auth/login.py
    → is_sensitive_path() = True
    → open_lazy_council() — dedupes within 60s window per file
    → council thread on blackboard.jsonl with tags [council, auto-council,
      needs-review]
    → self_audit Stop hook later warns if 'needs-review' thread has no
      perspectives yet (still un-reviewed)

ALWAYS exits 0. Override: HOOK_SKIP=auto_council_trigger.

Why 'lazy' (no persona invocation in this hook):
  - Hook timeout is 5s; persona LLM calls take 10s+ → would time out
  - Personas stay explicit (user or A-Loop invokes them) — only the
    council *opening* is automated. This is the minimal auto-step that
    removes the 'forgot /A-Council' failure mode.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import atomic_json  # noqa: E402
import council_persistent  # noqa: E402

DEFAULT_BB_PATH = REPO_ROOT / ".tmp" / "blackboard.jsonl"
DEDUP_WINDOW_SECONDS = 60  # same file edited twice within 60s = 1 council

# Code file extensions (NOT docs/configs/examples)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt",
    ".rb", ".php", ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".swift",
    ".m", ".mm", ".scala", ".clj", ".ex", ".exs", ".erl", ".hs", ".lua",
    ".pl", ".pm", ".sh", ".bash", ".zsh", ".fish", ".ps1",
}

# Path patterns that mark sensitive concerns (regex, case-insensitive)
# Boundary: word boundary OR path separator OR dash (auth-token, auth_token, auth/token)
SENSITIVE_PATTERNS = [
    re.compile(r"(?:^|/|_|-)(auth|authentication|authorization)(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)security(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)secret(?:s|/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)password(?:s|/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)token(?:s|/|_|\.|-|$)", re.IGNORECASE),
    # api key — match "api_key", "api-key", "apikey", "api/keys"
    re.compile(r"api[_\-/]?key", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)credential(?:s|/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)crypto(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)cookie(?:s|/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)session(?:s|/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)jwt(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)oauth(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)login(?:/|_|\.|-|$)", re.IGNORECASE),
    re.compile(r"(?:^|/|_|-)logout(?:/|_|\.|-|$)", re.IGNORECASE),
]

# Files to skip even if they match sensitive (examples, templates, docs)
SKIP_PATTERNS = [
    re.compile(r"\.example$", re.IGNORECASE),
    re.compile(r"\.example\.[^.]+$", re.IGNORECASE),  # secrets.example.json
    re.compile(r"\.template$", re.IGNORECASE),
    re.compile(r"\.md$", re.IGNORECASE),
    re.compile(r"\.rst$", re.IGNORECASE),
    re.compile(r"\.txt$", re.IGNORECASE),
    re.compile(r"\.jsonc?$", re.IGNORECASE),
    re.compile(r"\.ya?ml$", re.IGNORECASE),
    re.compile(r"\.toml$", re.IGNORECASE),
    re.compile(r"/wiki/", re.IGNORECASE),
    re.compile(r"/docs?/", re.IGNORECASE),
]


def is_sensitive_path(file_path: str) -> bool:
    """True if file_path is a code file touching sensitive concerns.

    Rules:
      - Extension must be a code extension (.py/.js/.ts/...), NOT .md/.json/.example
      - Path must match a sensitive keyword (auth/security/secret/password/...)
      - Skip examples/templates/docs even if they match
    """
    if not file_path:
        return False
    # Skip overrides first (cheaper)
    for pat in SKIP_PATTERNS:
        if pat.search(file_path):
            return False
    # Must be a code extension
    ext = Path(file_path).suffix.lower()
    if ext not in CODE_EXTENSIONS:
        return False
    # Must match a sensitive keyword
    return any(pat.search(file_path) for pat in SENSITIVE_PATTERNS)


def should_trigger(hook_input: dict) -> bool:
    """Decide whether this PostToolUse event should auto-open a council.

    Returns True only if:
      - tool is Edit|Write|MultiEdit
      - file_path is sensitive code
    """
    if not isinstance(hook_input, dict):
        return False
    tool = hook_input.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        return False
    file_path = (hook_input.get("tool_input") or {}).get("file_path", "")
    return is_sensitive_path(file_path)


def _find_recent_council_for_file(
    bb_path: Path | str,
    file_path: str,
    window_seconds: int = DEDUP_WINDOW_SECONDS,
) -> str | None:
    """Find an auto-council thread opened for this file within the window.

    Returns thread_id if found (for dedup), else None.
    """
    bb = council_persistent.blackboard.Blackboard(bb_path)
    if not Path(bb_path).is_file():
        return None
    cutoff = time.time() - window_seconds
    msgs = bb.read(since_ts=cutoff, limit=200)
    for m in msgs:
        if m.get("type") != "proposal":
            continue
        tags = m.get("tags", [])
        if "auto-council" not in tags:
            continue
        # Check if this council references our file
        body = m.get("body", "")
        meta_file = m.get("trigger_file", "")
        if file_path in body or file_path == meta_file:
            return m.get("thread_id")
    return None


def open_lazy_council(
    *,
    bb_path: Path | str,
    file_path: str,
    reason: str,
) -> str:
    """Open (or reuse) a council thread for a sensitive file edit.

    Dedup: if a council for this file was opened within DEDUP_WINDOW_SECONDS,
    return its thread_id instead of creating a new one.
    """
    # Dedup check
    existing = _find_recent_council_for_file(bb_path, file_path)
    if existing:
        return existing

    council = council_persistent.Council(bb_path)
    topic = f"Auto-review: {file_path}"
    body = (
        f"AUTO-COUNCIL triggered by sensitive file edit.\n"
        f"File: {file_path}\n"
        f"Reason: {reason}\n"
        f"Status: needs-review — run personas (security-auditor, code-reviewer) "
        f"before shipping this change."
    )
    tid = council.open(topic=topic, participants=["security-auditor", "code-reviewer"])
    # Augment the opener with our extra tags + trigger_file metadata.
    # Read-modify-write the last line (the opener we just wrote).
    import json as _json
    if Path(bb_path).is_file():
        lines = Path(bb_path).read_text(encoding="utf-8").splitlines()
        if lines:
            try:
                last = _json.loads(lines[-1])
                if last.get("id") == tid:
                    last.setdefault("tags", []).extend(["auto-council", "needs-review"])
                    last["trigger_file"] = file_path
                    last["trigger_reason"] = reason
                    lines[-1] = _json.dumps(last, ensure_ascii=False)
                    Path(bb_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
            except (_json.JSONDecodeError, IndexError):
                pass
    return tid


def main() -> int:
    """PostToolUse hook entry. Exits 0 always."""
    if "auto_council_trigger" in os.environ.get("HOOK_SKIP", ""):
        return 0
    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if not should_trigger(hook_input):
        return 0

    file_path = (hook_input.get("tool_input") or {}).get("file_path", "")
    try:
        tid = open_lazy_council(
            bb_path=DEFAULT_BB_PATH,
            file_path=file_path,
            reason=f"sensitive file edit ({file_path})",
        )
        sys.stderr.write(
            f"🏛️ [auto-council] opened review thread {tid} for {file_path} "
            f"(tag: needs-review). Run personas before ship.\n"
        )
    except Exception as e:
        sys.stderr.write(f"[auto-council] error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
