"""Tests for scripts/lib/memory_ledger.py — event-sourced cross-session memory.

Iron Law #1: failing tests written FIRST.

Memory Ledger คือความจำข้าม session ของสมอง A-Wiki. แตกต่างจาก
session-memory.md (manual) ตรงนี้:
  - append-only (ไม่ overwrite ของเดิม)
  - searchable (FTS5 บน summary + tags)
  - auto-captured โดย hooks (commit/Stop/block)
  - survives context compaction (อยู่บน disk ไม่ใช่ context window)

Schema per line:
  {"ts", "session_id", "type": "decision|lesson|failure|outcome|idea",
   "summary", "files": [], "tags": [], "parent_ts": null}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402 -- module under test (created by this chunk)


# ---------------------------------------------------------------------------
# 1. append — writes one valid JSON line per call
# ---------------------------------------------------------------------------
def test_append_creates_file_and_writes_entry(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(
        session_id="sess_a",
        type="decision",
        summary="chose Approach A",
        files=["scripts/x.py"],
        tags=["architecture"],
    )
    f = tmp_path / "ledger.jsonl"
    assert f.is_file()
    entries = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(entries) == 1
    e = entries[0]
    assert e["type"] == "decision"
    assert e["summary"] == "chose Approach A"
    assert e["files"] == ["scripts/x.py"]
    assert e["tags"] == ["architecture"]
    assert e["session_id"] == "sess_a"
    assert "ts" in e and isinstance(e["ts"], float)


def test_append_assigns_monotonic_timestamps(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ts1 = ledger.append(session_id="s", type="decision", summary="first")
    ts2 = ledger.append(session_id="s", type="decision", summary="second")
    assert ts2 >= ts1


def test_append_strips_secrets_from_summary(tmp_path):
    """Iron Law #6: ledger writer must not store raw secrets in summary.

    If a hook captures a commit/block with an API key in the message, the
    writer should redact obvious secret patterns before persisting.
    """
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(
        session_id="s",
        type="failure",
        summary="key sk-abc123secret456 leaked in command",
    )
    entries = ledger.recent(limit=1)
    assert "sk-abc123secret456" not in entries[0]["summary"], (
        "raw secret must not be persisted in ledger — Iron Law #6"
    )


# ---------------------------------------------------------------------------
# 1b. redaction — must cover ALL common cloud/SaaS secret formats
# ---------------------------------------------------------------------------
# Found via deep-debug 2026-07-22: _redact only covered sk-/AIza/Bearer.
# AWS keys (AKIA...), GitHub tokens (ghp_...), Slack (xoxb-), JWT all LEAKED.
# A commit message containing any of these would be persisted raw → Iron Law #6.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,secret", [
    ("AWS access key", "AKIAIOSFODNN7EXAMPLE"),
    ("GitHub PAT", "ghp_1234567890abcdefghijklmnop"),
    ("Slack bot token", "xoxb-1234567890-abcdef"),
    ("JWT", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signaturepart"),
    ("Anthropic key", "sk-ant-api03-1234567890abcdefghijklmnop"),
])
def test_redact_covers_cloud_saas_secrets(name, secret):
    """Each common secret format must be redacted, not just sk-/AIza."""
    redacted = ml._redact(f"leaked token: {secret} in log")
    assert secret not in redacted, (
        f"{name} pattern not redacted — {secret!r} leaked through _redact(). "
        f"Iron Law #6 violation."
    )


def test_redact_preserves_normal_text():
    """Redaction must not destroy normal commit messages (false positives)."""
    normal = "fix: handle ask- prefix in tokenizer (refs #123)"
    redacted = ml._redact(normal)
    assert redacted == normal, f"normal text wrongly redacted: {redacted!r}"


# ---------------------------------------------------------------------------
# 1c. summary size cap — prevent unbounded ledger entries (DoS / disk bomb)
# ---------------------------------------------------------------------------
def test_append_caps_oversized_summary(tmp_path):
    """A 1MB summary should be truncated, not stored raw.

    Found via deep-debug: no size cap means a malicious/large commit message
    or hook payload could bloat the ledger. Cap at a sane limit.
    """
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    huge = "x" * (500 * 1024)  # 500KB
    ledger.append(session_id="s", type="decision", summary=huge)
    entry = ledger.recent(limit=1)[0]
    assert len(entry["summary"]) < len(huge), (
        f"summary not capped: stored {len(entry['summary'])} chars "
        f"(should be < {len(huge)})"
    )


# ---------------------------------------------------------------------------
# 1d. ledger rotation — _load_all must not read unbounded history
# ---------------------------------------------------------------------------
def test_ledger_caps_loaded_entries(tmp_path):
    """Found via deep-debug: _load_all reads entire file. After 1 year of
    commits (~1825 entries, 247KB) it loads all into memory every call.
    A hard cap prevents memory growth + keeps recent() fast.
    """
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    for i in range(500):
        ledger.append(session_id="s", type="decision", summary=f"entry-{i}")
    # _load_all should respect a max-entries cap (e.g. 200)
    loaded = ledger._load_all()
    assert len(loaded) <= 300, (
        f"_load_all returned {len(loaded)} entries — no cap; unbounded memory growth"
    )


# ---------------------------------------------------------------------------
# 2. append — rejects invalid type
# ---------------------------------------------------------------------------
def test_append_rejects_invalid_type(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(ValueError):
        ledger.append(session_id="s", type="garbage", summary="x")


# ---------------------------------------------------------------------------
# 3. recent — returns last N entries, newest-first
# ---------------------------------------------------------------------------
def test_recent_returns_newest_first(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    for i in range(5):
        ledger.append(session_id="s", type="decision", summary=f"entry-{i}")
    recent = ledger.recent(limit=3)
    assert len(recent) == 3
    # newest first
    assert recent[0]["summary"] == "entry-4"
    assert recent[2]["summary"] == "entry-2"


def test_recent_limit_defaults_to_reasonable_number(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    for i in range(50):
        ledger.append(session_id="s", type="decision", summary=f"e{i}")
    # default limit should not return everything blindly
    recent = ledger.recent()
    assert len(recent) <= 50
    assert len(recent) > 0


# ---------------------------------------------------------------------------
# 4. search — FTS5 on summary + tags (case-insensitive substring)
# ---------------------------------------------------------------------------
def test_search_matches_summary_substring(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(session_id="s", type="decision", summary="refactor database layer")
    ledger.append(session_id="s", type="lesson", summary="learned about hooks")
    results = ledger.search("database")
    assert len(results) == 1
    assert "database" in results[0]["summary"]


def test_search_matches_tags(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(session_id="s", type="decision", summary="X", tags=["security", "auth"])
    ledger.append(session_id="s", type="decision", summary="Y", tags=["ui"])
    results = ledger.search("security")
    assert len(results) == 1
    assert results[0]["summary"] == "X"


def test_search_returns_empty_when_no_match(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(session_id="s", type="decision", summary="hello world")
    assert ledger.search("nonexistent") == []


# ---------------------------------------------------------------------------
# 5. replay_for_context — SessionStart injection (filtered by tags/files)
# ---------------------------------------------------------------------------
def test_replay_filters_by_tags(tmp_path):
    """SessionStart should replay only entries relevant to current work.

    If working on security, don't surface UI decisions.
    """
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    ledger.append(session_id="s1", type="decision", summary="use bcrypt", tags=["security"])
    ledger.append(session_id="s2", type="decision", summary="use tailwind", tags=["ui"])
    out = ledger.replay_for_context(interest_tags=["security"], limit=10)
    assert len(out) == 1
    assert out[0]["summary"] == "use bcrypt"


def test_replay_returns_empty_for_empty_ledger(tmp_path):
    ledger = ml.MemoryLedger(tmp_path / "ledger.jsonl")
    assert ledger.replay_for_context(interest_tags=["x"], limit=10) == []


# ---------------------------------------------------------------------------
# 6. persistence — survives ledger object recreation (new session)
# ---------------------------------------------------------------------------
def test_ledger_survives_recreation(tmp_path):
    """Simulate session boundary: write with one object, read with a NEW one.

    This is THE test that proves cross-session continuity: session A writes
    via MemoryLedger(f), session B reads via a fresh MemoryLedger(f).
    """
    f = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(f).append(
        session_id="sess_A", type="decision",
        summary="chose postgres over mysql",
        tags=["architecture"],
    )
    # session B: new process, new MemoryLedger instance, same file
    ledger_b = ml.MemoryLedger(f)
    recent = ledger_b.recent(limit=5)
    assert len(recent) == 1
    assert recent[0]["summary"] == "chose postgres over mysql"
    assert recent[0]["session_id"] == "sess_A"
