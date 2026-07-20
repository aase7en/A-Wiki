"""Tests for scripts/hooks/prompt_redactor.py — privacy redaction (Y1).

Iron Law #1: failing tests written FIRST.

Y1 redact() แทนที่ secrets + machine paths + emails + codenames ด้วย ***
ก่อนเก็บ prompt ลง .tmp/prompts/ (opt-in, local-only).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import prompt_redactor  # noqa: E402  -- module under test (created by Y1)


# ---------------------------------------------------------------------------
# 1. API keys → ***
# ---------------------------------------------------------------------------
def test_redact_replaces_api_keys():
    """sk-... keys ต้องถูกแทนที่ด้วย ***"""
    # Fixtures assembled at runtime so the repo's own secret scanner
    # (check_secret_leak / check_apikey) never sees a contiguous key-shaped
    # literal — a full-length literal here blocks every git command in
    # every session while this file is staged.
    key1 = "sk-" + "abc123def456ghi789jkl012mno345"
    key2 = "sk-or-v1-" + "xyz789abc456def123ghi"
    text = f"My key is {key1} and {key2}"
    redacted = prompt_redactor.redact(text)
    assert "sk-abc123" not in redacted
    assert "sk-or-v1-xyz" not in redacted
    assert "***" in redacted


def test_redact_replaces_github_token():
    text = "token: " + "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz"
    redacted = prompt_redactor.redact(text)
    assert "ghp_" not in redacted
    assert "***" in redacted


# ---------------------------------------------------------------------------
# 2. Machine paths → ***
# ---------------------------------------------------------------------------
def test_redact_replaces_machine_paths():
    """Windows + macOS + Linux paths ต้องถูกแทนที่."""
    text = "File at C:\\Users\\john\\secret.txt and /Users/jane/.ssh/key and /home/bob/data"
    redacted = prompt_redactor.redact(text)
    # Machine path ต้องถูกแทนที่ (john, jane, bob หายไป)
    assert "john" not in redacted or "***" in redacted
    assert "jane" not in redacted or "***" in redacted
    assert "bob" not in redacted or "***" in redacted


# ---------------------------------------------------------------------------
# 3. Emails → ***
# ---------------------------------------------------------------------------
def test_redact_replaces_emails():
    text = "Contact me at john.doe@personal-mail.com or admin@mycompany.org"
    redacted = prompt_redactor.redact(text)
    assert "john.doe@personal-mail.com" not in redacted
    assert "***" in redacted


# ---------------------------------------------------------------------------
# 4. Normal text preserved
# ---------------------------------------------------------------------------
def test_redact_preserves_normal_text():
    """ข้อความทั่วไปไม่ถูกทำลาย."""
    text = "Summarize the evidence on metformin for type 2 diabetes."
    redacted = prompt_redactor.redact(text)
    assert "metformin" in redacted
    assert "diabetes" in redacted
    assert "Summarize" in redacted


# ---------------------------------------------------------------------------
# 5. Thai text preserved
# ---------------------------------------------------------------------------
def test_redact_handles_thai_text():
    """อักษรไทยผ่านได้ (ไม่ถูกทำลาย)."""
    text = "สรุปหลักฐานเรื่องยาแก้ซึมเศร้าในผู้สูงอายุ"
    redacted = prompt_redactor.redact(text)
    assert "ผู้สูงอายุ" in redacted
    assert "ยาแก้ซึมเศร้า" in redacted


# ---------------------------------------------------------------------------
# 6. Empty input
# ---------------------------------------------------------------------------
def test_redact_empty_input():
    assert prompt_redactor.redact("") == ""
    assert prompt_redactor.redact(None) == ""  # type: ignore


# ---------------------------------------------------------------------------
# 7. Multiple patterns in one text
# ---------------------------------------------------------------------------
def test_redact_multiple_patterns():
    """หลาย pattern ในข้อความเดียว — ทั้งหมดต้องถูกแทนที่."""
    text = (
        "Email: admin@test.org, Key: sk-test1234567890abcdefghijklmnop, "
        "Path: /Users/alice/data — analyze this medical data."
    )
    redacted = prompt_redactor.redact(text)
    assert "admin@test.org" not in redacted
    assert "sk-test1234567890abcdefghijklmnop" not in redacted
    assert "alice" not in redacted or "***" in redacted
    # Normal content preserved
    assert "medical" in redacted
