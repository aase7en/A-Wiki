"""Tests for scripts/hooks/memory_capture.py — auto-capture events to ledger.

Iron Law #1: failing tests written FIRST.

memory_capture เป็น hook ที่เชื่อม Neural Spine เข้ากับระบบ hook จริง:
  - PostToolUse Bash(git commit) → ledger.append(type=decision, ...)
  - Stop                          → ledger.append(type=outcome, ...)
  - UserPromptSubmit /remember    → ledger.append(type per arg)

Hook รับ input JSON ผ่าน stdin (เหมือน hooks อื่น) และ never blocks (exit 0).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402
import memory_capture as mc  # noqa: E402 -- module under test (created by this chunk)


# ---------------------------------------------------------------------------
# 1. parse_commit_message — extracts subject from a git commit Bash result
# ---------------------------------------------------------------------------
def test_parse_commit_message_from_bash_output():
    """A successful 'git commit' Bash tool result contains the subject line."""
    bash_result = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'feat(x): add thing'"},
        "tool_response": {
            "output": "[main abc1234] feat(x): add thing\n 1 file changed, 5 insertions(+)",
        },
    }
    msg = mc.parse_commit_message(bash_result)
    assert msg is not None
    assert "feat(x)" in msg or "add thing" in msg


def test_parse_commit_message_returns_none_for_non_commit():
    """Don't capture when the command wasn't a git commit."""
    bash_result = {
        "tool_name": "Bash",
        "tool_input": {"command": "git status"},
        "tool_response": {"output": "nothing to commit"},
    }
    assert mc.parse_commit_message(bash_result) is None


def test_parse_commit_message_handles_inline_dash_m():
    """Commit messages via -m flag should be captured from the command itself."""
    bash_result = {
        "tool_name": "Bash",
        "tool_input": {"command": 'git commit -m "fix: critical bug in parser"'},
        "tool_response": {"output": ""},
    }
    msg = mc.parse_commit_message(bash_result)
    assert msg is not None
    assert "critical bug" in msg


# ---------------------------------------------------------------------------
# 2. capture_commit — writes decision entry to ledger
# ---------------------------------------------------------------------------
def test_capture_commit_writes_decision_to_ledger(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    mc.capture_commit(
        ledger_path=ledger_path,
        session_id="sess_test",
        commit_message="feat: neural spine init",
        changed_files=["scripts/lib/x.py"],
    )
    entries = ml.MemoryLedger(ledger_path).recent(limit=5)
    assert len(entries) == 1
    assert entries[0]["type"] == "decision"
    assert "neural spine" in entries[0]["summary"]
    assert entries[0]["files"] == ["scripts/lib/x.py"]


def test_capture_commit_redacts_secrets_in_message(tmp_path):
    """Iron Law #6: even commit messages get redacted."""
    ledger_path = tmp_path / "ledger.jsonl"
    mc.capture_commit(
        ledger_path=ledger_path,
        session_id="s",
        commit_message="fix: remove sk-1234567890secret from code",
    )
    entries = ml.MemoryLedger(ledger_path).recent(limit=1)
    assert "sk-1234567890secret" not in entries[0]["summary"]


# ---------------------------------------------------------------------------
# 3. capture_stop — writes outcome entry summarizing session
# ---------------------------------------------------------------------------
def test_capture_stop_writes_outcome_to_ledger(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    mc.capture_stop(
        ledger_path=ledger_path,
        session_id="sess_test",
        session_summary="Completed Phase 1 chunk 3, all tests green",
    )
    entries = ml.MemoryLedger(ledger_path).recent(limit=1)
    assert entries[0]["type"] == "outcome"
    assert "Phase 1 chunk 3" in entries[0]["summary"]


# ---------------------------------------------------------------------------
# 4. hook main — never blocks (exit 0)
# ---------------------------------------------------------------------------
def test_hook_main_exits_zero_on_commit_event(monkeypatch, tmp_path, capsys):
    """Hook MUST always exit 0 — it observes, never blocks."""
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(mc, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(mc, "REPO_ROOT", tmp_path)
    input_json = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'test: hook captures'"},
        "tool_response": {"output": "[main abc] test: hook captures"},
    }
    monkeypatch.setattr("sys.stdin", _StdinStub(json.dumps(input_json)))
    exit_code = mc.main()
    assert exit_code == 0, "memory_capture must never block"


def test_hook_main_no_crash_on_unrelated_event(monkeypatch, tmp_path):
    """Hook should silently no-op for events it doesn't care about."""
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(mc, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(mc, "REPO_ROOT", tmp_path)
    input_json = {
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_response": {"output": "file contents"},
    }
    monkeypatch.setattr("sys.stdin", _StdinStub(json.dumps(input_json)))
    assert mc.main() == 0
    # ledger should be empty — nothing captured
    assert not ledger_path.is_file() or ledger_path.read_text().strip() == ""


# ---------------------------------------------------------------------------
# 5. HOOK_SKIP override
# ---------------------------------------------------------------------------
def test_hook_respects_hook_skip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOOK_SKIP", "memory_capture")
    monkeypatch.setattr(mc, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(mc, "REPO_ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", _StdinStub(json.dumps({"tool_name": "Bash"})))
    assert mc.main() == 0
    # ledger should not be written when skipped
    assert not (tmp_path / "ledger.jsonl").is_file()


class _StdinStub:
    """Minimal stdin stub that returns a fixed payload on read()."""
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload


# ---------------------------------------------------------------------------
# 6. SessionStart replay — formats recent entries for context injection
# ---------------------------------------------------------------------------
def test_format_for_session_start_returns_string(tmp_path):
    """replay_for_session_start must return a human-readable string (or empty)."""
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="prev", type="decision",
        summary="chose postgres", tags=["architecture"],
    )
    out = mc.replay_for_session_start(ledger_path, limit=5)
    assert isinstance(out, str)
    assert "postgres" in out


def test_format_for_session_start_empty_ledger(tmp_path):
    out = mc.replay_for_session_start(tmp_path / "missing.jsonl", limit=5)
    assert out == ""


def test_format_for_session_start_includes_recent_decisions(tmp_path):
    """SessionStart should surface decisions + lessons + outcomes prominently."""
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(session_id="s", type="decision", summary="D1")
    ml.MemoryLedger(ledger_path).append(session_id="s", type="failure", summary="F1")
    ml.MemoryLedger(ledger_path).append(session_id="s", type="outcome", summary="O1")
    out = mc.replay_for_session_start(ledger_path, limit=10)
    # All three types should appear in the replay (they're all worth surfacing)
    assert "D1" in out
    assert "O1" in out

# ---------------------------------------------------------------------------
# 7. R-FR-004 — commit file evidence must be structural, not prose-derived
# ---------------------------------------------------------------------------
def _git(tmp_path: Path) -> Path:
    repo = tmp_path / "git-repo"
    repo.mkdir()
    def run(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True,
                              capture_output=True, text=True, encoding="utf-8")
    run("init", "-q")
    run("config", "user.email", "test.invalid")
    run("config", "user.name", "test")
    return repo


def _commit_event(repo: Path, message: str) -> dict:
    short = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, check=True,
        capture_output=True, text=True, encoding="utf-8").stdout.strip()
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=repo, check=True,
        capture_output=True, text=True, encoding="utf-8").stdout.strip() or "HEAD"
    return {
        "tool_name": "Bash",
        "tool_input": {"command": f"git commit -m '{message}'"},
        "tool_response": {"output": f"[{branch} {short}] {message}\n 1 file changed"},
    }


def test_changed_files_from_real_root_commit(tmp_path):
    repo = _git(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("a=1\n", encoding="utf-8")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "root"], cwd=repo, check=True)
    files = mc._changed_files_for_commit(_commit_event(repo, "root"), repo_root=repo)
    assert files == ["README.md", "src/a.py"]


def test_changed_files_preserve_old_and_new_paths_for_rename_and_delete(tmp_path):
    repo = _git(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "old.py").write_text("x=1\n", encoding="utf-8")
    (repo / "src" / "gone.py").write_text("gone\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    subprocess.run(["git", "mv", "src/old.py", "src/new.py"], cwd=repo, check=True)
    (repo / "src" / "gone.py").unlink()
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "move"], cwd=repo, check=True)
    files = mc._changed_files_for_commit(_commit_event(repo, "move"), repo_root=repo)
    assert {"src/old.py", "src/new.py", "src/gone.py"} <= set(files)


def test_changed_files_do_not_guess_head_without_commit_oid(tmp_path):
    repo = _git(tmp_path)
    (repo / "a.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'maybe failed'"},
        "tool_response": {"output": "nothing to commit, working tree clean"},
    }
    assert mc._changed_files_for_commit(event, repo_root=repo) == []


def test_hook_main_persists_real_commit_files(monkeypatch, tmp_path):
    repo = _git(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("x=1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "capture"], cwd=repo, check=True)
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(mc, "LEDGER_PATH", ledger_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr("sys.stdin", _StdinStub(json.dumps(_commit_event(repo, "capture"))))
    assert mc.main() == 0
    entry = ml.MemoryLedger(ledger_path).recent(limit=1)[0]
    assert entry["files"] == ["src/app.py"]


def test_changed_files_path_normalizer_rejects_control_characters():
    assert mc._normalize_repo_path("src/line\nbreak.py") is None
    assert mc._normalize_repo_path("src/tab\tbreak.py") is None
