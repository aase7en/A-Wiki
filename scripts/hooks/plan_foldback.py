#!/usr/bin/env python3
"""plan_foldback.py — Slice D2 Stop hook: fold today's decisions back
into the plans that own the touched files.

Community pattern ("kill stale specs"): at session end, recent ledger
decisions whose normalized changed-file evidence intersects a plan's exact
`scope:` are appended to "## Deviations (auto-folded)". Legacy/manual
entries without structural file evidence retain a bounded prose fallback.
Inserted Markdown is escaped and idempotent by a stable SHA-256 entry ID.

Stdin: Stop-hook payload (session_id used only for logging).
Exit 0 always (soft observe-only; registry classification: soft).
"""
from __future__ import annotations

import hashlib
import json
import math
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
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(e, dict) or e.get("type") != "decision":
            continue
        try:
            ts_value = float(e.get("ts", 0))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(ts_value):
            continue
        try:
            time.localtime(ts_value)
        except (OverflowError, OSError, ValueError):
            continue
        if ts_value >= cutoff:
            out.append(e)
    return out


def _normalize_repo_path(value: object) -> str | None:
    """Normalize one exact repo-relative path; reject escapes/absolutes."""
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


def _touches(entry: dict, scope: list[str]) -> bool:
    normalized_scope = {
        value for raw in scope
        if (value := _normalize_repo_path(raw)) is not None
    }
    if not normalized_scope:
        return False

    files = entry.get("files")
    if isinstance(files, list) and files:
        normalized_files = {
            value for raw in files
            if (value := _normalize_repo_path(raw)) is not None
        }
        # Structural evidence is authoritative. Invalid/non-matching evidence
        # must never fall back to a prose mention and create a false positive.
        return bool(normalized_scope & normalized_files)

    tags = [str(t) for t in entry.get("tags", [])]
    if "commit" in tags:
        # A captured commit with missing Git evidence must fail closed. Falling
        # back to its prose subject would recreate R-FR-004 false matches.
        return False

    # Backward compatibility for legacy/manual non-commit decisions.
    hay = " ".join([str(entry.get("summary", ""))]
                   + [str(t) for t in entry.get("tags", [])])
    return any(s in hay for s in normalized_scope)


def _markdown_inline(value: object) -> str:
    """Collapse untrusted ledger text to one escaped Markdown-safe line."""
    out = re.sub(r"\s+", " ", str(value) if value is not None else "").strip()
    out = out.replace("\\", "\\\\")
    for char in ("`", "*", "_", "[", "]", "(", ")", "<", ">", "#", "!", "|"):
        out = out.replace(char, "\\" + char)
    return out


def _entry_id(entry: dict) -> str:
    """Collision-resistant stable identity over the persisted ledger entry."""
    canonical = json.dumps(
        entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


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
    original_existing = text  # legacy ts markers only count before this run
    if MARKER not in existing:
        existing = existing.rstrip() + f"\n\n{MARKER}\n\n"
    added = 0
    for e in entries:
        raw_ts = e.get("ts", 0)
        legacy_stamp = f"ts={raw_ts}"
        legacy_marker = f"({legacy_stamp})"
        entry_id = _entry_id(e)
        id_marker = f"<!-- awiki-foldback:{entry_id} -->"
        if id_marker in existing:
            continue
        if legacy_marker in original_existing:
            # Preserve idempotency for lines produced by the pre-hash format.
            continue
        try:
            ts_value = float(raw_ts)
        except (TypeError, ValueError):
            ts_value = 0.0
        date = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts_value))
        session = _markdown_inline(e.get("session_id", "?")) or "?"
        summary = _markdown_inline(e.get("summary", ""))
        line = (f"- {date} [{session}] {summary} ({legacy_stamp}) "
                f"{id_marker}")
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
