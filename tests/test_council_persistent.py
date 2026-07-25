"""Tests for scripts/lib/council_persistent.py — blackboard-backed async council.

Iron Law #1: failing tests written FIRST.

council_persistent ทำให้ personas (code-reviewer/test-engineer/
security-auditor) ถกเถียงกันผ่าน blackboard อย่างถาวร — thread คงอยู่
ข้าม session, dashboard แสดงได้, resume ได้.

ปัจจุบัน council (multi-perspective review) เป็น ephemeral — ผลหายไป
หลัง session. Persistent version เขียนลง blackboard.jsonl.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import council_persistent as cp  # noqa: E402 -- module under test (created here)
import blackboard as bb  # noqa: E402 -- dependency


# ---------------------------------------------------------------------------
# 1. open_council — creates a blackboard thread with council type
# ---------------------------------------------------------------------------
def test_open_council_returns_thread_id(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="review PR #42 for security", participants=["code-reviewer", "security-auditor"])
    assert tid is not None
    msgs = bb.Blackboard(bb_path).read(thread_id=tid)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "proposal"  # council opener is a proposal
    assert "council" in msgs[0].get("tags", [])


def test_open_council_stores_participants(tmp_path):
    """Council opener must list who should respond."""
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["code-reviewer", "test-engineer", "security-auditor"])
    opener = bb.Blackboard(bb_path).read(thread_id=tid)[0]
    assert set(opener["participants"]) == {"code-reviewer", "test-engineer", "security-auditor"}


# ---------------------------------------------------------------------------
# 2. post_perspective — a persona adds its view to the thread
# ---------------------------------------------------------------------------
def test_post_perspective_adds_to_thread(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="review module X", participants=["code-reviewer", "security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="sql injection risk in query()", severity="critical")
    council.post_perspective(thread_id=tid, persona="code-reviewer",
                              finding="naming inconsistent", severity="minor")
    msgs = bb.Blackboard(bb_path).read(thread_id=tid)
    assert len(msgs) == 3  # opener + 2 perspectives
    # perspectives should be type=answer (replying to the proposal)
    perspectives = [m for m in msgs if m["type"] == "answer"]
    assert len(perspectives) == 2


def test_post_perspective_includes_severity(tmp_path):
    """Each perspective must carry severity (critical/important/minor)."""
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="critical bug", severity="critical")
    perspectives = [m for m in bb.Blackboard(bb_path).read(thread_id=tid) if m["type"] == "answer"]
    assert perspectives[0]["severity"] == "critical"


def test_post_perspective_rejects_invalid_severity(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["x"])
    with pytest.raises(ValueError):
        council.post_perspective(thread_id=tid, persona="x",
                                  finding="y", severity="garbage")


# ---------------------------------------------------------------------------
# 3. summarize — aggregate findings by severity
# ---------------------------------------------------------------------------
def test_summarize_counts_by_severity(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["a", "b", "c"])
    council.post_perspective(thread_id=tid, persona="a", finding="f1", severity="critical")
    council.post_perspective(thread_id=tid, persona="b", finding="f2", severity="important")
    council.post_perspective(thread_id=tid, persona="c", finding="f3", severity="minor")
    council.post_perspective(thread_id=tid, persona="a", finding="f4", severity="critical")
    summary = council.summarize(thread_id=tid)
    assert summary["critical"] == 2
    assert summary["important"] == 1
    assert summary["minor"] == 1
    assert summary["total_findings"] == 4


def test_summarize_empty_council(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["a"])
    summary = council.summarize(thread_id=tid)
    assert summary["critical"] == 0
    assert summary["total_findings"] == 0


# ---------------------------------------------------------------------------
# 4. has_critical — quick check for self-audit gate
# ---------------------------------------------------------------------------
def test_has_critical_true_when_critical_exists(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["a"])
    council.post_perspective(thread_id=tid, persona="a", finding="bad", severity="critical")
    assert council.has_critical(thread_id=tid) is True


def test_has_critical_false_when_only_minor(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["a"])
    council.post_perspective(thread_id=tid, persona="a", finding="ok", severity="minor")
    assert council.has_critical(thread_id=tid) is False


# ---------------------------------------------------------------------------
# 5. persistence — survives Council recreation (cross-session)
# ---------------------------------------------------------------------------
def test_council_survives_recreation(tmp_path):
    """Council thread persists across sessions via blackboard.jsonl."""
    bb_path = tmp_path / "bb.jsonl"
    council_a = cp.Council(bb_path)
    tid = council_a.open(topic="cross-session review", participants=["code-reviewer"])
    council_a.post_perspective(thread_id=tid, persona="code-reviewer",
                                finding="issue", severity="important")

    council_b = cp.Council(bb_path)  # new instance = new session
    summary = council_b.summarize(thread_id=tid)
    assert summary["total_findings"] == 1
    assert summary["important"] == 1
