#!/usr/bin/env python3
"""
Hook: Compaction Suggest (#16) — strategic /compact nudge
----------------------------------------------------------
Wired on UserPromptSubmit DIRECTLY in .claude/settings.json (not via
hooks_runner, which captures child stdout — stdout here must reach the
model as injected context).

Reads the session transcript (JSONL), takes the newest assistant `usage`
entry, and estimates current context = input + cache_read + cache_creation
tokens. When usage crosses AWIKI_COMPACT_SUGGEST_PCT (default 75%) of
AWIKI_CONTEXT_WINDOW (default 200k), prints a /compact suggestion.

Claude Code's own auto-compact fires at ~95% — too late per
docs/protocols/context-compaction.md. This hook makes the "strategic"
trigger table in that protocol enforceable instead of prose-only.

State: .tmp/compact-suggest-<session_id>.txt keeps the last-warned pct so
each level warns once; re-warns every +AWIKI_COMPACT_SUGGEST_STEP pp
(default 10); a drop of more than one step (i.e. a compaction happened)
resets the ladder.

Fail-soft: every unexpected condition exits 0 silently — this hook must
never break or delay a prompt.

Opt-out: AWIKI_COMPACT_SUGGEST=0 or HOOK_SKIP=check_compaction_suggest.
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAIL_BYTES = 262_144  # only the newest entries matter; keeps the hook O(1)


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
        return value if value > 0 else default
    except ValueError:
        return default


def _skipped_by_hook_skip() -> bool:
    entries = os.environ.get("HOOK_SKIP", "").split(",")
    for entry in entries:
        normalized = entry.strip().replace("-", "_")
        if normalized.endswith(".py"):
            normalized = normalized[: -len(".py")]
        if normalized == "check_compaction_suggest":
            return True
    return False


def _latest_context_tokens(transcript: Path) -> int | None:
    """Newest assistant usage entry → total context tokens, else None."""
    try:
        size = transcript.stat().st_size
        with open(transcript, "rb") as f:
            f.seek(max(0, size - TAIL_BYTES))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None

    for line in reversed(tail.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict) or "input_tokens" not in usage:
            continue
        try:
            return (
                int(usage.get("input_tokens") or 0)
                + int(usage.get("cache_read_input_tokens") or 0)
                + int(usage.get("cache_creation_input_tokens") or 0)
            )
        except (TypeError, ValueError):
            continue
    return None


def _state_path(session_id: str) -> Path:
    tmp_dir = Path(os.environ.get("AWIKI_COMPACT_SUGGEST_TMP_DIR", str(REPO_ROOT / ".tmp")))
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id) or "default"
    return tmp_dir / f"compact-suggest-{safe_id}.txt"


def _read_last_warned(state_file: Path) -> int:
    try:
        return int(state_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def _write_last_warned(state_file: Path, pct: int) -> None:
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(str(pct), encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    # Windows consoles default to cp874/cp1252 — force UTF-8 for the Thai message
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if os.environ.get("AWIKI_COMPACT_SUGGEST", "1") == "0":
        return 0
    if _skipped_by_hook_skip():
        return 0

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0

    transcript_path = data.get("transcript_path")
    if not transcript_path:
        return 0
    transcript = Path(transcript_path)
    if not transcript.is_file():
        return 0

    tokens = _latest_context_tokens(transcript)
    if tokens is None:
        return 0

    window = _env_int("AWIKI_CONTEXT_WINDOW", 200_000)
    threshold = _env_int("AWIKI_COMPACT_SUGGEST_PCT", 75)
    step = _env_int("AWIKI_COMPACT_SUGGEST_STEP", 10)
    pct = round(tokens * 100 / window)

    state_file = _state_path(str(data.get("session_id") or "default"))
    last_warned = _read_last_warned(state_file)

    if last_warned and pct <= last_warned - step:
        # context shrank a whole step → a compaction/clear happened; reset ladder
        last_warned = 0
        _write_last_warned(state_file, 0)

    if pct >= threshold and (last_warned == 0 or pct >= last_warned + step):
        print(
            f"🗜️ Context ≈{pct}% ของ window ({tokens:,}/{window:,} tokens) — "
            f"เลยจุด strategic /compact ({threshold}%) แล้ว\n"
            f"   แนะนำ: `/compact focus on <งานปัจจุบัน>` — ตาราง trigger ใน docs/protocols/context-compaction.md\n"
            f"   ❌ อย่า compact กลาง verify/contradiction check หรือก่อน user input ที่ต้องอ้าง history เต็ม"
        )
        _write_last_warned(state_file, pct)

    return 0


if __name__ == "__main__":
    sys.exit(main())
