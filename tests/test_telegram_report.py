"""Tests for scripts/hermes/telegram_report.py — full-report chunking (R-P1-002).

Iron Law #1: failing tests written FIRST.

The P1.5 inline sender truncated every report after 4,000 characters
(`min(len(text), limit)`). These tests pin the corrected contract:

  - the ENTIRE report is represented exactly once, in order
  - multiple messages are produced for long reports
  - every message (header + body + suffix) fits Telegram's 4,096 limit
  - no silent truncation at any size
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

import telegram_report as tr  # noqa: E402 -- module under test


def _reconstruct(messages: list[str], header: str = "") -> str:
    """Strip framing (header prefix + part suffix) and rejoin the payload."""
    out = []
    for m in messages:
        if header:
            assert m.startswith(header + "\n\n"), f"missing header: {m[:40]!r}"
            m = m[len(header) + 2 :]
        m = re.sub(r"\n\n\(\d+/\d+\)$", "", m)
        out.append(m)
    return "".join(out)


def test_long_report_all_content_once_in_order():
    text = "".join(f"line-{i:05d} {'x' * 40}\n" for i in range(200))
    assert len(text) > 8000, "synthetic report must exceed two chunks"
    msgs = tr.chunk_report(text)
    assert len(msgs) >= 3, "expected multiple messages"
    assert _reconstruct(msgs) == text


def test_each_message_within_telegram_limit_no_truncation():
    text = "y" * 20000
    msgs = tr.chunk_report(text)
    assert all(len(m) <= 4096 for m in msgs), "every message must fit Telegram's limit"
    assert _reconstruct(msgs) == text, "no character may be dropped"


def test_header_appears_on_every_message():
    text = "z" * 9000
    msgs = tr.chunk_report(text, header="☁️ Report")
    assert len(msgs) >= 2
    assert all(m.startswith("☁️ Report\n\n") for m in msgs)
    assert _reconstruct(msgs, header="☁️ Report") == text


def test_short_report_single_message_no_suffix():
    assert tr.chunk_report("short report") == ["short report"]


def test_empty_report_yields_single_empty_message():
    assert tr.chunk_report("") == [""]


def test_default_chunk_keeps_messages_under_limit_with_framing():
    text = "w" * 15000
    msgs = tr.chunk_report(text, header="H" * 60)
    assert all(len(m) <= 4096 for m in msgs)
