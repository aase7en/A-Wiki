"""Tests for the Subagent Fan-out Diversity Guard (check_subagent_fanout.py).

SO6 adds a language-aware recommendation: when a prompt contains substantial
Thai text, the hook advises using the GLM bucket (strong on Thai) instead of
the default bucket. These tests cover the pure helpers (language detection,
model resolution, provider bucketing) — no hook process spawned.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import check_subagent_fanout as fanout  # noqa: E402


# ---------------------------------------------------------------------------
# Provider bucket resolution
# ---------------------------------------------------------------------------

def test_provider_for_model_gemini():
    assert fanout.provider_for_model("gemini-3.5-flash") == "gemini-free"


def test_provider_for_model_deepseek():
    assert fanout.provider_for_model("deepseek-v4-flash") == "deepseek"


def test_provider_for_model_glm():
    assert fanout.provider_for_model("glm-5.2") == "glm"


def test_provider_for_model_custom_ref():
    """custom:<provider-id>:<model> should resolve via the model tail."""
    assert fanout.provider_for_model(
        "custom:5056d2a7-73ab-4d53-9266-9e4845946d32:deepseek-v4-flash"
    ) == "deepseek"


def test_provider_for_model_unknown():
    assert fanout.provider_for_model("totally-unknown-model") == "unknown"
    assert fanout.provider_for_model("") == "unknown"


# ---------------------------------------------------------------------------
# SO6 — Thai language detection (drives bucket recommendation)
# ---------------------------------------------------------------------------

def test_thai_ratio_empty():
    assert fanout.thai_ratio("") == 0.0


def test_thai_ratio_pure_english():
    assert fanout.thai_ratio("Find all files matching the query") == 0.0


def test_thai_ratio_pure_thai():
    # All Thai chars → ratio close to 1.0 (Thai chars dominate).
    r = fanout.thai_ratio("สรุปข้อมูลทางการแพทย์เกี่ยวกับยา")
    assert r > 0.5, f"pure Thai should have high ratio, got {r}"


def test_thai_ratio_mixed():
    """Mixed Thai/English prompt: ratio should be between 0 and 1."""
    r = fanout.thai_ratio("วิเคราะห์ AAPL stock analysis หน่อย")
    assert 0.0 < r < 1.0


def test_is_thai_heavy_threshold():
    """A prompt with >30% Thai chars crosses the 'Thai-heavy' threshold."""
    # ~50% Thai chars.
    assert fanout.is_thai_heavy("วิเคราะห์การลงทุนในหุ้น AAPL อย่างละเอียด") is True
    # <5% Thai.
    assert fanout.is_thai_heavy("Review the PR, just one คำไทย in it") is False


def test_recommended_bucket_for_thai_prompt():
    """A Thai-heavy prompt should recommend the GLM bucket (strong on Thai)."""
    bucket = fanout.recommended_bucket_for_prompt("สรุป evidence ทางการแพทย์เกี่ยวกับยา metformin")
    assert bucket == "glm", f"Thai-heavy prompt should prefer glm bucket, got {bucket}"


def test_recommended_bucket_for_english_prompt():
    """An English prompt should not force the GLM bucket (returns '')."""
    bucket = fanout.recommended_bucket_for_prompt("Analyze the stock price of AAPL")
    assert bucket == "", "English prompt should have no forced bucket recommendation"
