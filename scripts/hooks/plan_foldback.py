#!/usr/bin/env python3
"""plan_foldback.py — Slice D2 Stop hook: fold today's decisions back
into the plans that own the touched files.

Community pattern ("kill stale specs"): at session end, ledger decisions
whose summary/tags reference a path inside a plan's `scope:` are
appended to that plan's "## Deviations (auto-folded)" section — so the
plan file, not the chat log, stays the SSoT. Idempotent per entry ts.

Stdin: Stop-hook payload (session_id used only for logging).
Exit 0 always (soft observe-only; registry classification: soft).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_GLOBS = ("docs/plans/*.md", "decisions/*.md")
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
MARKER = "## Deviations (auto-folded)"


def _scope_of(text: str) -> list[str]:
    m = FM_RE.match(text)
    if not m:
        return []
    scope: list[str] = []
    in_scope = False
    for line in m.group(1).splitlines():
        if re.match(r"^scope:\s*$", line):
            in_scope = True; continue
        if in_scope:
            mm = re.match(r"^\s+-\s*(\S+)\s*$", line)
            if mm:
                scope.append(mm.group(1)); continue
            if line and not line.startswith((" ", "\t", "-")):
                in_scope = False
    return scope


def _today_entries(ledger: Path) -> list[dict]:
    if not ledger.is_file():
        return []
    out = []
    cutoff = time.time() - 24 * 3600
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "decision" and float(e.get("ts", 0)) >= cutoff:
            out.append(e)
    return out


def _touches(entry: dict, scope: list[str]) -> bool:
    hay = " ".join([entry.get("summary", "")]
                   + [str(t) for t in entry.get("tags", [])])
    return any(s and s in hay for s in scope)


def foldback(plan: Path, ledger: Path) -> int:
    """Append today's in-scope decisions to the plan; returns count added."""
    text = plan.read_text(encoding="utf-8")
    scope = _scope_of(text)
    if not scope:
        return 0
    entries = [e for e in _today_entries(Path(ledger))
               if _touches(e, scope)]
    if not entries:
        return 0

    existing = text
    if MARKER not in existing:
        existing = existing.rstrip() + f"\n\n{MARKER}\n\n"
    added = 0
    for e in entries:
        stamp = f"ts={e.get('ts')}"
        if stamp in existing:  # idempotent per entry
            continue
        date = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.get("ts", 0)))
        line = (f"- {date} [{e.get('session_id', '?')}] "
                f"{e.get('summary', '').strip()} ({stamp})")
        existing = existing.rstrip() + "\n" + line
        added += 1
    if added:
        plan.write_text(existing.rstrip() + "\n", encoding="utf-8")
    return added


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        data = {}
    ledger = Path(os.environ.get(
        "AWIKI_MEMORY_LEDGER_PATH",
        str(REPO_ROOT / ".tmp" / "memory-ledger.jsonl")))
    total = 0
    for pattern in SPEC_GLOBS:
        for plan in REPO_ROOT.glob(pattern):
            if plan.is_file():
                total += foldback(plan, ledger)
    if total:
        print(f"📋 fold-back: {total} decision(s) folded into their plans "
              f"(Deviations sections updated)")
    return 0


if __name__ == "__main__":
    import os  # noqa: E402 — used in main
    sys.exit(main())
