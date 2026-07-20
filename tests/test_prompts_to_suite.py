"""Tests for scripts/eval/prompts_to_suite.py — prod-log eval suite generator (Y2).

Iron Law #1: failing tests written FIRST.

Y2 อ่าน .tmp/prompts/<subagent>-*.jsonl → dedupe + filter → generate eval suite JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import prompts_to_suite  # noqa: E402  -- module under test (created by Y2)


def _write_prompts(dir_path: Path, subagent: str, prompts: list[str]) -> None:
    """Write fake prompt log JSONL for testing."""
    import time
    log_file = dir_path / f"{subagent}-20260101.jsonl"
    lines = []
    for p in prompts:
        lines.append(json.dumps({"ts": time.time(), "subagent": subagent, "prompt": p}))
    log_file.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Dedupe
# ---------------------------------------------------------------------------
def test_collect_prompts_dedupes(tmp_path):
    """Same prompt 3 times → counted once with count=3."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    _write_prompts(prompts_dir, "agent-x", [
        "Summarize metformin evidence",
        "Summarize metformin evidence",
        "Summarize metformin evidence",
        "Different prompt about diabetes",
    ])
    collected = prompts_to_suite.collect_prompts("agent-x", prompts_dir=prompts_dir)
    assert len(collected) == 2  # deduped
    # The repeated one should have count=3
    by_prompt = {c["prompt"]: c["count"] for c in collected}
    assert by_prompt["Summarize metformin evidence"] == 3
    assert by_prompt["Different prompt about diabetes"] == 1


# ---------------------------------------------------------------------------
# 2. min-count filter
# ---------------------------------------------------------------------------
def test_min_count_filter(tmp_path):
    """min_count=3 → เก็บเฉพาะ prompts ที่พบ >= 3 ครั้ง."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    _write_prompts(prompts_dir, "agent-x", [
        "frequent prompt", "frequent prompt", "frequent prompt",
        "rare prompt",
    ])
    collected = prompts_to_suite.collect_prompts("agent-x", prompts_dir=prompts_dir, min_count=3)
    assert len(collected) == 1
    assert collected[0]["prompt"] == "frequent prompt"


# ---------------------------------------------------------------------------
# 3. Auto-generate required keywords from frequency
# ---------------------------------------------------------------------------
def test_auto_required_keywords():
    """build_suite สร้าง required จากคำที่พบบ่อยใน prompt."""
    collected = [
        {"prompt": "Summarize metformin evidence for diabetes", "count": 5},
        {"prompt": "Analyze metformin side effects", "count": 3},
    ]
    suite = prompts_to_suite.build_suite("agent-x", collected)
    assert suite["suite"] == "prod-agent-x"
    assert len(suite["cases"]) == 2
    # Each case should have non-empty required (auto-generated)
    for case in suite["cases"]:
        assert len(case["required"]) > 0
        assert "subagent" in case
        assert "prompt" in case


# ---------------------------------------------------------------------------
# 4. Dry-run doesn't write files
# ---------------------------------------------------------------------------
def test_dry_run_no_write(tmp_path, monkeypatch):
    """collect + build_suite ไม่เขียนไฟล์ใดๆ."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    _write_prompts(prompts_dir, "agent-x", ["test prompt"] * 5)
    suite = prompts_to_suite.build_suite_from_logs(
        "agent-x", prompts_dir=prompts_dir, min_count=3)
    assert suite is not None
    # No files written to evals/
    evals_dir = tmp_path / "evals"
    assert not evals_dir.exists() or not any(evals_dir.iterdir())


# ---------------------------------------------------------------------------
# 5. No prompts → None
# ---------------------------------------------------------------------------
def test_no_prompts_returns_none(tmp_path):
    """No prompt logs → None (nothing to build)."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    result = prompts_to_suite.build_suite_from_logs(
        "nonexistent-agent", prompts_dir=prompts_dir)
    assert result is None
