"""caveman_session_start.py — SessionStart hook for caveman-default rule.

Iron Law #7b (AGENTS.md 2026-08-11): caveman-style replies are the
default. This hook:
  1. Ensures .tmp/caveman.flag exists with value 'on' (default since
     2026-08-11 — user complaint 'พูดมากไม่สรุป').
  2. Prints the caveman rules blob to stdout (injected as additionalContext
     by Claude Code's hook framework).

Opt-out: user types /verbose → another mechanism (or manual edit) writes
'tmp/caveman.flag' = 'off'. This hook HONORS existing state — never
overwrites 'off' with 'on'.

Wired DIRECT on SessionStart (not via hooks_runner — runner uses
capture_output=True and swallows exit-0 stdout, which is exactly what
we need to inject as context).

Override: HOOK_SKIP=caveman_session_start (substring match)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Windows console UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
FLAG_PATH = REPO_ROOT / ".tmp" / "caveman.flag"

# Caveman rules — injected once per session as context.
# Kept short on purpose (this IS the caveman skill).
_RULES = """\
🦴 CAVEMAN DEFAULT (AGENTS.md §7b, since 2026-08-11)

Replies are caveman-style by default. Rules:
  - ตัด preamble ("ผมจะ...", "ก่อนอื่น...", "let me...")
  - ตัด recap ของสิ่งที่เพิ่งทำ (user เห็น tool calls แล้ว)
  - Bullet ≤3 บรรทัดต่อ section
  - ตอบตรงคำถาม — ใช่/ไม่ → "ใช่ — <เหตุผล 1 บรรทัด>" จบ
  - Snippets ตรงประเด็น ไม่ wrap ด้วย explanation
  - ตาราง >5 แถว → emit JSON/CSV → render → คืน path + 1-3 บรรทัดสรุป
  - ประหยัด ~60-65% output tokens

Opt-out: user พิมพ์ /verbose → .tmp/caveman.flag = 'off'
"""


def ensure_flag(path: Path = FLAG_PATH) -> None:
    """Create .tmp/caveman.flag with 'on' if missing. Preserve existing state."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("on", encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[caveman_session_start] could not write flag: {e}\n")


def is_caveman_on(path: Path = FLAG_PATH) -> bool:
    """True iff caveman mode is active (default: True when flag missing)."""
    try:
        if not path.exists():
            return True  # default since 2026-08-11
        return path.read_text(encoding="utf-8").strip().lower() in ("on", "1", "true", "yes")
    except Exception:
        return True  # fail-safe: caveman ON


def rules_blob() -> str:
    """Return the caveman rules text. Returns empty string when OFF."""
    if not is_caveman_on():
        return ""
    return _RULES


def main() -> int:
    """Hook entry. Exits 0 always (advisory SessionStart).

    Passes FLAG_PATH explicitly to ensure_flag/rules_blob so monkeypatch
    on the module global takes effect (default args bind at def-time).
    """
    if "caveman_session_start" in os.environ.get("HOOK_SKIP", ""):
        return 0
    try:
        ensure_flag(FLAG_PATH)
        if is_caveman_on(FLAG_PATH):
            sys.stdout.write(_RULES)
    except Exception as e:
        sys.stderr.write(f"[caveman_session_start] error (fail-soft): {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
