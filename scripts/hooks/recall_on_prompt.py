#!/usr/bin/env python3
"""recall_on_prompt.py — UserPromptSubmit hook for auto semantic recall.

After cross-device sync (#2), the local .tmp/memory-ledger.jsonl contains
decisions/lessons/outcomes from ALL devices (Win/Mac/Pi5). This hook fires
on UserPromptSubmit → runs semantic_recall (FTS5 BM25) → injects the top
result IF it's strongly relevant. This makes the brain proactively surface
cross-device memory without the user asking.

Safety mitigations (from A-Think pre-mortem):
  - R-SR1 (false-positive): MIN_SCORE threshold (5.0) — only inject strong matches
  - R-SR2 (privacy): machine-path defense — NEVER inject entries containing
    C:\\Users\\..., /Users/..., /home/... (would surface foreign-repo/host paths
    in chat). This was the lesson from A-Council 2026-08-03.
  - R-SR3 (perf): skip trivial prompts (< 15 chars, greetings/confirmations)
  - R-SR4 (staleness): injection includes the entry's date for freshness judgment
  - Never crash: all errors caught, hook always exits 0

Output:
  - On strong match: JSON {"additionalContext": "[memory YYYY-MM-DD] ..."} to stdout
  - On no match / trivial: empty stdout, exit 0
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resolve repo root from hook location
REPO_ROOT = Path(__file__).resolve().parents[2]
_LIB_DIR = REPO_ROOT / "scripts" / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

# --- Config ---
MIN_PROMPT_LEN = 15
MIN_SCORE = 5.0  # BM25 score threshold for "strong match" (empirically tuned)
MAX_SUMMARY_INJECT = 200  # truncate entry summary in injection

_TRIVIAL_RE = re.compile(
    r"^\s*(hi|hello|hey|ok|okay|thanks|thank you|ty|yes|no|yep|nope|done|got it|"
    r"sure|cool|nice|great|awesome|bye|good)\s*[!.?]*\s*$",
    re.IGNORECASE,
)

# R-SR2: machine path patterns (Windows + Unix + Drive)
_MACHINE_PATH_RE = re.compile(
    r"C:\\Users\\[A-Za-z0-9._-]+|"      # Windows user home
    r"/Users/[A-Za-z0-9._-]+/|"          # macOS user home
    r"/home/[A-Za-z0-9._-]+/|"           # Linux user home
    r"\\\\[A-Za-z0-9._-]+\\",            # UNC paths
    re.IGNORECASE,
)


def _is_trivial(prompt: str) -> bool:
    """Check if prompt is too short or matches greeting/confirmation."""
    if len(prompt.strip()) < MIN_PROMPT_LEN:
        return True
    return bool(_TRIVIAL_RE.match(prompt.strip()))


def _contains_machine_path(text: str) -> bool:
    """R-SR2: detect machine-specific paths that would leak privacy."""
    return bool(_MACHINE_PATH_RE.search(text))


def _format_date(ts: float) -> str:
    """Format entry timestamp as YYYY-MM-DD for freshness display."""
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError, OverflowError):
        return "unknown-date"


def _format_injection(entry: dict) -> str:
    """Format a ledger entry as a context-injection string."""
    date_str = _format_date(entry.get("ts", 0))
    etype = entry.get("type", "memory")
    summary = (entry.get("summary", "") or "")[:MAX_SUMMARY_INJECT]
    tags = ", ".join(entry.get("tags", []) or [])
    tag_part = f" [{tags}]" if tags else ""
    return f"[memory {date_str}] ({etype}){tag_part} {summary}"


def _term_overlap_score(prompt: str, summary: str, tags: str) -> float:
    """Fallback scorer for small corpora where BM25 idf degenerates to 0.

    Returns the count of prompt tokens found in summary+tags (case-insensitive).
    At least 2 overlapping tokens = reasonable relevance.
    """
    prompt_tokens = set(_normalize(prompt).split())
    text = _normalize(f"{summary} {tags}")
    text_tokens = set(text.split())
    overlap = prompt_tokens & text_tokens
    return float(len(overlap))


def _normalize(text: str) -> str:
    """Lowercase + strip non-alphanumeric for term matching."""
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower()).strip()


def decide_recall(
    ledger_path: Path | str,
    prompt: str,
) -> str | None:
    """Pure function: given a prompt, return injection string or None.

    This is the testable core — no I/O side effects beyond reading the ledger.
    Returns:
      - injection string (with date) if strong, path-safe match found
      - None if trivial prompt, no match, weak match, or machine-path detected

    Scoring strategy:
      - On large corpora: FTS5 BM25 (score > MIN_SCORE = 5.0 = strong)
      - On small corpora (< 10 entries): BM25 idf degenerates to ~0, so we
        fall back to term-overlap (≥ 2 prompt tokens in summary+tags = match)
    """
    if _is_trivial(prompt):
        return None

    try:
        import semantic_recall as sr
        import memory_ledger as ml
    except ImportError:
        return None

    # Detect corpus size to pick scoring strategy
    try:
        ledger = ml.MemoryLedger(ledger_path)
        entries = ledger._load_all()
    except Exception:
        return None
    if not entries:
        return None

    use_fallback = len(entries) < 10

    top = None
    if not use_fallback:
        try:
            results = sr.search(ledger_path, prompt, limit=1)
        except Exception:
            results = []
        if results and results[0].get("score", 0) >= MIN_SCORE:
            top = results[0]

    if top is None:
        # Fallback: term-overlap scoring on raw entries
        best_score = 0.0
        best_entry = None
        for e in entries:
            summary = e.get("summary", "") or ""
            tags = " ".join(e.get("tags", []) or [])
            score = _term_overlap_score(prompt, summary, tags)
            if score > best_score:
                best_score = score
                best_entry = e
        if best_entry and best_score >= 2.0:
            top = best_entry

    if not top:
        return None

    # R-SR2: machine-path defense
    summary = top.get("summary", "") or ""
    files_text = " ".join(str(f) for f in top.get("files", []))
    if _contains_machine_path(summary) or _contains_machine_path(files_text):
        return None

    return _format_injection(top)


def main() -> int:
    """Hook entry point. Reads UserPromptSubmit JSON from stdin."""
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    # UserPromptSubmit payload: {"prompt": "...", ...}
    prompt = payload.get("prompt") or payload.get("message") or ""

    if not prompt or _is_trivial(prompt):
        return 0  # silent exit, no output

    # Resolve ledger path
    tmp_dir = Path(os.environ.get("AWIKI_TMP_DIR", REPO_ROOT / ".tmp"))
    ledger_path = tmp_dir / "memory-ledger.jsonl"
    if not ledger_path.is_file():
        return 0  # no ledger → nothing to recall

    injection = decide_recall(ledger_path, prompt)
    if injection:
        # Output JSON with additionalContext (ZCode/Claude hook convention)
        output = json.dumps({"additionalContext": injection})
        sys.stdout.write(output)
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    sys.exit(main())
