"""Tests for scripts/hooks/auto_council_trigger.py — auto-open council on sensitive edit.

Iron Law #1: failing tests written FIRST.

auto_council_trigger คือ PostToolUse Edit|Write hook ที่:
  - ถ้าไฟล์ที่แก้ match sensitive pattern (auth/security/secret/password/
    token/api_key) + เป็น source code (.py/.js/.ts/.go/.rs/...)
  - → auto-open council thread (lazy — ไม่เรียก personas)
  - tag "needs-review" เพื่อให้ self_audit Stop hook เตือนถ้ายังไม่ review

Root cause ที่แก้: user ไม่ต้องจำ /A-Council — ระบบเปิดให้เองเมื่อเสี่ยง
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

import auto_council_trigger as act  # noqa: E402 -- module under test (created here)
import council_persistent as cp  # noqa: E402


# ---------------------------------------------------------------------------
# 1. is_sensitive_path — matches code files touching sensitive concerns
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path,expected", [
    # Sensitive: code + sensitive keyword
    ("scripts/auth/login.py", True),
    ("src/security/checker.js", True),
    ("lib/crypto/password.go", True),
    ("api/keys/handlers.ts", True),
    ("secrets/rotate.py", True),
    ("middleware/auth-token.py", True),
    ("src/utils/api_key.py", True),
    ("src/utils/apikey.py", True),  # alternate spelling
    # Not sensitive: doc/config files even with sensitive word
    ("docs/auth.md", False),                # markdown, not code
    ("wiki/security.md", False),            # wiki
    ("README.md", False),                    # plain doc
    ("auth.example", False),                # example, not code
    # Not sensitive: code without sensitive keyword
    ("scripts/utils/format.py", False),
    ("src/components/Button.tsx", False),
    ("lib/helpers/string.go", False),
    # Edge: secret in name but example file
    ("config/secrets.example.json", False),  # example → skip
])
def test_is_sensitive_path(path, expected):
    assert act.is_sensitive_path(path) is expected


# ---------------------------------------------------------------------------
# 2. should_trigger — combines path sensitivity + skip overrides
# ---------------------------------------------------------------------------
def test_should_trigger_true_for_sensitive_code_edit(tmp_path):
    """Editing auth/login.py should trigger."""
    hook_input = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/auth/login.py"},
    }
    assert act.should_trigger(hook_input) is True


def test_should_trigger_false_for_doc_edit(tmp_path):
    """Editing auth.md should NOT trigger (doc, not code)."""
    hook_input = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "docs/auth.md"},
    }
    assert act.should_trigger(hook_input) is False


def test_should_trigger_false_for_non_sensitive_code():
    """Editing format.py (no sensitive keyword) should NOT trigger."""
    hook_input = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/utils/format.py"},
    }
    assert act.should_trigger(hook_input) is False


def test_should_trigger_false_for_read_tool():
    """Read tool is not an edit — should not trigger."""
    hook_input = {
        "tool_name": "Read",
        "tool_input": {"file_path": "scripts/auth/login.py"},
    }
    assert act.should_trigger(hook_input) is False


# ---------------------------------------------------------------------------
# 3. open_lazy_council — creates a council thread with needs-review tag
# ---------------------------------------------------------------------------
def test_open_lazy_council_creates_thread(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    tid = act.open_lazy_council(
        bb_path=bb_path,
        file_path="scripts/auth/login.py",
        reason="sensitive file edit (auth/login)",
    )
    assert tid is not None
    # Verify thread exists + has needs-review tag + references the file
    council = cp.Council(bb_path)
    # Read raw to check tags
    import blackboard
    msgs = blackboard.Blackboard(bb_path).read(thread_id=tid)
    assert len(msgs) == 1
    opener = msgs[0]
    assert "needs-review" in opener.get("tags", [])
    assert "auto-council" in opener.get("tags", [])
    assert "auth/login.py" in opener["body"]


def test_open_lazy_council_dedupes_within_window(tmp_path):
    """Editing the same file twice in 60s should NOT create 2 councils.

    Prevents spam: agent iterates on auth.py 5 times → 1 council, not 5.
    """
    bb_path = tmp_path / "bb.jsonl"
    tid1 = act.open_lazy_council(bb_path=bb_path, file_path="scripts/auth/login.py", reason="edit 1")
    tid2 = act.open_lazy_council(bb_path=bb_path, file_path="scripts/auth/login.py", reason="edit 2")
    assert tid1 == tid2, "should dedupe — same file within window returns existing thread"


def test_open_lazy_council_different_files_create_separate_threads(tmp_path):
    """Editing auth/login.py and security/check.py → 2 separate councils."""
    bb_path = tmp_path / "bb.jsonl"
    tid1 = act.open_lazy_council(bb_path=bb_path, file_path="scripts/auth/login.py", reason="x")
    tid2 = act.open_lazy_council(bb_path=bb_path, file_path="scripts/security/check.py", reason="y")
    assert tid1 != tid2


# ---------------------------------------------------------------------------
# 4. main — hook entry, exits 0 always, opens council on sensitive edit
# ---------------------------------------------------------------------------
def test_main_exits_zero_on_sensitive_edit(monkeypatch, tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    monkeypatch.setattr(act, "DEFAULT_BB_PATH", bb_path)
    monkeypatch.setattr("sys.stdin", _Stdin(json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/auth/login.py"},
    })))
    assert act.main() == 0
    # Council should have been opened
    import blackboard
    msgs = blackboard.Blackboard(bb_path).read()
    assert len(msgs) >= 1
    assert any("needs-review" in m.get("tags", []) for m in msgs)


def test_main_no_op_on_non_sensitive_edit(monkeypatch, tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    monkeypatch.setattr(act, "DEFAULT_BB_PATH", bb_path)
    monkeypatch.setattr("sys.stdin", _Stdin(json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/utils/format.py"},
    })))
    assert act.main() == 0
    # No council should be opened
    assert not bb_path.is_file() or bb_path.read_text().strip() == ""


def test_main_respects_hook_skip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOOK_SKIP", "auto_council_trigger")
    monkeypatch.setattr(act, "DEFAULT_BB_PATH", tmp_path / "bb.jsonl")
    monkeypatch.setattr("sys.stdin", _Stdin(json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/auth/login.py"},
    })))
    assert act.main() == 0


class _Stdin:
    def __init__(self, payload):
        self._payload = payload
    def read(self):
        return self._payload
