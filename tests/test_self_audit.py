"""Tests for scripts/hooks/self_audit.py — Tier 2 #7 self-audit Stop hook.

Iron Law #1: failing tests written FIRST.

self_audit คือ Stop hook ที่:
  - ถ้ามี council thread open → ตรวจ has_critical
  - ถ้า critical → เขียน findings เป็น ledger type=failure + block ship
  - ถ้าไม่มี council open → no-op (pass)
  - ถ้า council ไม่มี critical → pass + summary note

Design: hook ไม่เรียก personas เอง (personas ควรถูกเรียกก่อน Stop).
hook แค่ตรวจ council state + enforce gate.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import council_persistent as cp  # noqa: E402
import memory_ledger as ml  # noqa: E402
import self_audit as sa  # noqa: E402 -- module under test (created here)


def _setup(tmp_path):
    """Create council + ledger with given state."""
    bb_path = tmp_path / "bb.jsonl"
    ledger_path = tmp_path / "ledger.jsonl"
    return cp.Council(bb_path), ml.MemoryLedger(ledger_path), bb_path, ledger_path


# ---------------------------------------------------------------------------
# 1. check_open_councils — finds active council threads
# ---------------------------------------------------------------------------
def test_check_open_councils_finds_threads_with_findings(tmp_path):
    council, ledger, bb_path, ledger_path = _setup(tmp_path)
    tid = council.open(topic="review X", participants=["code-reviewer"])
    council.post_perspective(thread_id=tid, persona="code-reviewer",
                              finding="bug", severity="important")
    councils = sa.check_open_councils(bb_path)
    assert len(councils) >= 1
    assert councils[0]["thread_id"] == tid


def test_check_open_councils_empty_when_no_councils(tmp_path):
    _, _, bb_path, _ = _setup(tmp_path)
    assert sa.check_open_councils(bb_path) == []


# ---------------------------------------------------------------------------
# 2. evaluate_ship_gate — returns {block: bool, critical_count, summary}
# ---------------------------------------------------------------------------
def test_evaluate_ship_gate_blocks_when_critical(tmp_path):
    council, _, bb_path, _ = _setup(tmp_path)
    tid = council.open(topic="X", participants=["security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="sql injection", severity="critical")
    gate = sa.evaluate_ship_gate(bb_path)
    assert gate["block"] is True
    assert gate["critical_count"] >= 1


def test_evaluate_ship_gate_passes_when_no_critical(tmp_path):
    council, _, bb_path, _ = _setup(tmp_path)
    tid = council.open(topic="X", participants=["code-reviewer"])
    council.post_perspective(thread_id=tid, persona="code-reviewer",
                              finding="naming", severity="minor")
    gate = sa.evaluate_ship_gate(bb_path)
    assert gate["block"] is False
    assert gate["critical_count"] == 0


def test_evaluate_ship_gate_passes_when_no_councils(tmp_path):
    _, _, bb_path, _ = _setup(tmp_path)
    gate = sa.evaluate_ship_gate(bb_path)
    assert gate["block"] is False


# ---------------------------------------------------------------------------
# 3. record_findings_to_ledger — writes findings as failure entries
# ---------------------------------------------------------------------------
def test_record_findings_writes_critical_to_ledger(tmp_path):
    council, ledger, bb_path, ledger_path = _setup(tmp_path)
    tid = council.open(topic="X", participants=["security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="critical bug X", severity="critical")
    gate = sa.evaluate_ship_gate(bb_path)
    n_written = sa.record_findings_to_ledger(ledger_path, bb_path, gate)
    assert n_written >= 1
    # Verify ledger has a failure entry
    entries = ledger.search("critical bug X")
    assert len(entries) >= 1
    assert entries[0]["type"] == "failure"


def test_record_findings_skips_when_no_critical(tmp_path):
    council, ledger, bb_path, ledger_path = _setup(tmp_path)
    tid = council.open(topic="X", participants=["a"])
    council.post_perspective(thread_id=tid, persona="a",
                              finding="minor", severity="minor")
    gate = sa.evaluate_ship_gate(bb_path)
    n = sa.record_findings_to_ledger(ledger_path, bb_path, gate)
    assert n == 0  # don't write minor findings as failures


# ---------------------------------------------------------------------------
# 4. main — hook entry, exit 0 (warns but never hard-blocks session)
# ---------------------------------------------------------------------------
def test_main_exits_zero(monkeypatch, tmp_path):
    """Hook must exit 0 — it WARNS about critical, doesn't kill session."""
    monkeypatch.setattr(sa, "DEFAULT_BB_PATH", tmp_path / "bb.jsonl")
    monkeypatch.setattr(sa, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    assert sa.main() == 0


def test_main_respects_hook_skip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOOK_SKIP", "self_audit")
    monkeypatch.setattr(sa, "DEFAULT_BB_PATH", tmp_path / "bb.jsonl")
    assert sa.main() == 0


# ---------------------------------------------------------------------------
# 5. main — emits warning to stderr when critical found
# ---------------------------------------------------------------------------
def test_main_warns_on_critical(monkeypatch, tmp_path, capsys):
    bb_path = tmp_path / "bb.jsonl"
    ledger_path = tmp_path / "ledger.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="X", participants=["security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="sql injection", severity="critical")
    monkeypatch.setattr(sa, "DEFAULT_BB_PATH", bb_path)
    monkeypatch.setattr(sa, "DEFAULT_LEDGER_PATH", ledger_path)
    sa.main()
    captured = capsys.readouterr()
    assert "critical" in captured.err.lower() or "block" in captured.err.lower(), (
        f"should warn about critical, got stderr: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# 6. check_unreviewed_councils — finds needs-review councils without perspectives
# ---------------------------------------------------------------------------
def test_check_unreviewed_finds_council_without_perspectives(tmp_path):
    """An auto-council opened but no personas posted → flagged unreviewed."""
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="auto-review auth.py", participants=["security-auditor"])
    # Augment opener with needs-review + auto-council tags (simulate trigger hook)
    import json
    lines = bb_path.read_text(encoding="utf-8").splitlines()
    last = json.loads(lines[-1])
    last.setdefault("tags", []).extend(["auto-council", "needs-review"])
    last["trigger_file"] = "scripts/auth/login.py"
    lines[-1] = json.dumps(last, ensure_ascii=False)
    bb_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # No perspectives posted → should be flagged
    unreviewed = sa.check_unreviewed_councils(bb_path)
    assert len(unreviewed) == 1
    assert unreviewed[0]["trigger_file"] == "scripts/auth/login.py"


def test_check_unreviewed_excludes_councils_with_perspectives(tmp_path):
    """Auto-council that DID get a perspective → not flagged."""
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="reviewed", participants=["security-auditor"])
    council.post_perspective(thread_id=tid, persona="security-auditor",
                              finding="ok", severity="minor")
    # Mark as needs-review (simulating trigger hook)
    import json
    lines = bb_path.read_text(encoding="utf-8").splitlines()
    opener = json.loads(lines[0])
    opener.setdefault("tags", []).extend(["auto-council", "needs-review"])
    lines[0] = json.dumps(opener, ensure_ascii=False)
    bb_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    unreviewed = sa.check_unreviewed_councils(bb_path)
    assert unreviewed == [], "reviewed council should not be flagged"


def test_main_warns_on_unreviewed(monkeypatch, tmp_path, capsys):
    """Stop hook should warn if there are un-reviewed auto-councils."""
    bb_path = tmp_path / "bb.jsonl"
    council = cp.Council(bb_path)
    tid = council.open(topic="needs review", participants=["x"])
    import json
    lines = bb_path.read_text(encoding="utf-8").splitlines()
    opener = json.loads(lines[0])
    opener.setdefault("tags", []).extend(["auto-council", "needs-review"])
    opener["trigger_file"] = "scripts/auth/x.py"
    lines[0] = json.dumps(opener, ensure_ascii=False)
    bb_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(sa, "DEFAULT_BB_PATH", bb_path)
    monkeypatch.setattr(sa, "DEFAULT_LEDGER_PATH", tmp_path / "ledger.jsonl")
    sa.main()
    captured = capsys.readouterr()
    assert "need review" in captured.err.lower() or "needs-review" in captured.err.lower(), (
        f"should warn about un-reviewed, got stderr: {captured.err!r}"
    )
