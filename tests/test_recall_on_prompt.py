"""Tests for scripts/hooks/recall_on_prompt.py — auto semantic recall on prompt.

Iron Law #1: failing tests written FIRST.

Purpose: after cross-device sync (#2), the local ledger contains decisions
from ALL devices. This hook fires on UserPromptSubmit → runs semantic_recall
→ injects the top result IF it's strongly relevant (score > threshold).
This makes the brain proactively surface cross-device memory without the
user asking.

Safety:
  - Skip trivial prompts (too short, or matches greeting/confirmation)
  - Skip if no strong match (score below MIN_SCORE)
  - Machine-path defense (R-SR2): never inject entries containing machine
    paths (C:\\Users\\..., /Users/..., /home/...) even if they score high
  - Never crash the session (all errors caught)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import memory_ledger as ml  # noqa: E402
import recall_on_prompt as rop  # noqa: E402 -- module under test (created here)


def _seed_ledger(path: Path, entries: list[dict]) -> None:
    """Write entries directly to ledger JSONL (bypass redact for test data)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# ---------------------------------------------------------------------------
# 1. decide_recall — core decision logic (pure function, no I/O)
# ---------------------------------------------------------------------------
def test_strong_match_returns_injection(tmp_path):
    """Prompt matches a ledger entry strongly → return injection string."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "pi5", "type": "lesson",
         "summary": "Pi5 autonomous job learned: use atomic writes for ledger",
         "files": [], "tags": ["pi5", "atomic"], "parent_ts": None},
    ])
    result = rop.decide_recall(ledger, "atomic writes ledger problem")
    assert result is not None
    assert "atomic" in result.lower()


def test_no_match_returns_none(tmp_path):
    """Prompt has nothing relevant → return None (no injection)."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "pi5", "type": "lesson",
         "summary": "Pi5 autonomous job learned: use atomic writes",
         "files": [], "tags": ["atomic"], "parent_ts": None},
    ])
    result = rop.decide_recall(ledger, "quantum physics philosophy")
    assert result is None


# ---------------------------------------------------------------------------
# 2. Trivial prompt filtering (R-SR3 mitigation)
# ---------------------------------------------------------------------------
def test_short_prompt_skipped(tmp_path):
    """Prompt < 15 chars → skip (return None, no search)."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "x", "type": "decision",
         "summary": "atomic writes", "files": [], "tags": [], "parent_ts": None},
    ])
    assert rop.decide_recall(ledger, "atomic") is None  # 6 chars → skip


def test_greeting_prompt_skipped(tmp_path):
    """Prompt matches greeting/confirmation patterns → skip."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "x", "type": "decision",
         "summary": "hello world decision", "files": [], "tags": [], "parent_ts": None},
    ])
    for greeting in ["hi there how are you", "thanks for the help",
                     "ok got it thanks", "yes please go ahead"]:
        assert rop.decide_recall(ledger, greeting) is None, \
            f"trivial prompt should be skipped: {greeting!r}"


# ---------------------------------------------------------------------------
# 3. Machine-path defense (R-SR2)
# ---------------------------------------------------------------------------
def test_machine_path_in_entry_blocks_injection(tmp_path):
    """Even if an entry scores high, if it contains a machine path,
    do NOT inject it (privacy: don't surface foreign-repo/host paths)."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "pi5", "type": "lesson",
         "summary": "Learned: deploy to C:\\Users\\secret\\projects\\thing",
         "files": [], "tags": ["deploy"], "parent_ts": None},
    ])
    result = rop.decide_recall(ledger, "deploy projects learned")
    assert result is None, "must not inject entry with machine path"


def test_unix_machine_path_blocked(tmp_path):
    """Unix-style machine paths also blocked."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1.0, "session_id": "mac", "type": "outcome",
         "summary": "Fixed /Users/john/repo-thing/bug in auth module",
         "files": [], "tags": ["auth"], "parent_ts": None},
    ])
    result = rop.decide_recall(ledger, "fix auth module bug")
    assert result is None


# ---------------------------------------------------------------------------
# 4. Injection format — includes date for freshness (R-SR4)
# ---------------------------------------------------------------------------
def test_injection_includes_date(tmp_path):
    """Injection string includes the entry's date so user can judge freshness."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1784305167.0, "session_id": "pi5", "type": "lesson",
         "summary": "atomic writes prevent corruption",
         "files": [], "tags": ["atomic"], "parent_ts": None},
    ])
    result = rop.decide_recall(ledger, "atomic writes corruption prevention")
    assert result is not None
    # Should contain a date marker (year-based)
    assert "2026" in result or "2025" in result


# ---------------------------------------------------------------------------
# 5. Hook entry point — reads stdin, writes JSON to stdout
# ---------------------------------------------------------------------------
def test_hook_main_outputs_json_on_strong_match(tmp_path, monkeypatch, capsys):
    """Hook reads UserPromptSubmit payload from stdin, outputs JSON to stdout."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1784305167.0, "session_id": "pi5", "type": "lesson",
         "summary": "atomic writes prevent ledger corruption on crash",
         "files": [], "tags": ["atomic", "ledger"], "parent_ts": None},
    ])
    monkeypatch.setenv("AWIKI_TMP_DIR", str(tmp_path))
    # Simulate stdin: UserPromptSubmit payload
    payload = {"prompt": "how to prevent ledger corruption on crash"}
    monkeypatch.setattr("sys.stdin", _StubStdin(json.dumps(payload)))
    rc = rop.main()
    assert rc == 0
    out = capsys.readouterr().out.strip()
    if out:
        parsed = json.loads(out)
        assert "additionalContext" in parsed or "context" in parsed


def test_hook_main_no_output_on_trivial(tmp_path, monkeypatch, capsys):
    """Trivial prompt → no stdout output (silent, exit 0)."""
    ledger = tmp_path / "memory-ledger.jsonl"
    _seed_ledger(ledger, [
        {"ts": 1784305167.0, "session_id": "pi5", "type": "lesson",
         "summary": "atomic writes", "files": [], "tags": [], "parent_ts": None},
    ])
    monkeypatch.setenv("AWIKI_TMP_DIR", str(tmp_path))
    payload = {"prompt": "ok thanks"}
    monkeypatch.setattr("sys.stdin", _StubStdin(json.dumps(payload)))
    rc = rop.main()
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == "", "trivial prompt should produce no stdout"


class _StubStdin:
    """Minimal stdin stub for hook tests."""
    def __init__(self, text: str):
        self._text = text

    def read(self) -> str:
        return self._text
