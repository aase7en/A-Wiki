"""
complexity_classifier.py — Decide if a batch of ingest requests is trivial
enough to send to Tier 0 (free models).

Heuristic only — fast, no LLM call. Errs on the side of NOT-trivial so we
don't waste free-tier rate limits on hard work that will fail quality_gate.

Inputs that flag as trivial:
  - small raw file (≤ trivial_max_input_chars from config)
  - all-ASCII or mostly-ASCII content (Thai-heavy → needs DeepSeek/Haiku)
  - single file (we don't batch trivial work)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from adapters import IngestRequest  # noqa: E402
from config import get_default, load_conf  # noqa: E402

THAI_RANGE = range(0x0E00, 0x0E80)


def _thai_ratio(text: str, sample_size: int = 4000) -> float:
    if not text:
        return 0.0
    sample = text[:sample_size]
    thai = sum(1 for ch in sample if ord(ch) in THAI_RANGE)
    return thai / max(1, len(sample))


def is_trivial(requests: list[IngestRequest], conf=None) -> tuple[bool, str]:
    """Return (is_trivial, reason).

    Reason is logged so the user can see *why* the router picked Tier 0
    (or didn't) — important for debugging surprise costs.
    """
    if not requests:
        return False, "empty backlog"
    if len(requests) > 1:
        return False, f"multiple files ({len(requests)}) — keep batch on Tier 1+"
    if conf is None:
        conf = load_conf()
    max_chars = int(get_default(conf, "trivial_max_input_chars") or 4000)

    req = requests[0]
    raw_path = REPO_ROOT / req.raw_path
    try:
        size = raw_path.stat().st_size
    except OSError:
        return False, f"raw path unreadable: {req.raw_path}"
    if size > max_chars:
        return False, f"raw size {size} > trivial_max_input_chars ({max_chars})"

    try:
        text = raw_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return False, f"raw read error: {e}"

    if _thai_ratio(text) > 0.05:
        return False, "Thai-heavy content — needs Tier 1+ for quality"

    return True, f"single small ASCII source ({size} bytes)"
