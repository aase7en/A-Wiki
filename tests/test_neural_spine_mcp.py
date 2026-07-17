"""Tests for scripts/lib/neural_spine_mcp.py — MCP tool wrappers for Neural Spine.

Iron Law #1: failing tests written FIRST.

Each MCP tool wraps a Neural Spine primitive (memory_ledger / blackboard /
task_board) so agents can call them via the awiki MCP server.

Tools exposed (8):
  memory_recall(query, limit)        → list[entry]
  memory_remember(type, summary, ...) → ts
  bb_post(frm, to, body, type, thread_id) → msg_id
  bb_read(since_ts, thread_id, to_filter, limit) → list[msg]
  bb_reply(thread_id, frm, body, type) → msg_id
  task_add(goal, files, parent_goal_id, lease_minutes) → task_id
  task_claim(task_id, claimant, lease_minutes) → bool
  task_release(task_id) → bool
  task_list(status) → list[task]
  task_update(task_id, status, note) → bool
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import neural_spine_mcp as nsmcp  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. TOOLS dict exposes all 10 Neural Spine tools with correct shape
# ---------------------------------------------------------------------------
def test_tools_dict_has_all_neural_spine_tools():
    """All 10 tools must be registered for agents to use."""
    expected = {
        "memory_recall", "memory_remember",
        "bb_post", "bb_read", "bb_reply",
        "task_add", "task_claim", "task_release", "task_list", "task_update",
    }
    actual = set(nsmcp.TOOLS.keys())
    missing = expected - actual
    assert not missing, f"missing MCP tools: {missing}"


def test_each_tool_has_fn_description_schema():
    """Each tool entry must have fn (callable), description, inputSchema."""
    for name, spec in nsmcp.TOOLS.items():
        assert "fn" in spec, f"{name} missing fn"
        assert callable(spec["fn"]), f"{name}.fn not callable"
        assert "description" in spec and isinstance(spec["description"], str), f"{name} missing description"
        assert "inputSchema" in spec, f"{name} missing inputSchema"
        assert spec["inputSchema"]["type"] == "object", f"{name} inputSchema must be object"


# ---------------------------------------------------------------------------
# 2. memory_recall — wraps ledger.search()
# ---------------------------------------------------------------------------
def test_memory_recall_returns_matching_entries(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    # Seed the ledger
    import memory_ledger
    memory_ledger.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="use postgres",
        tags=["architecture"],
    )
    nsmcp.set_paths(ledger=ledger_path, blackboard=tmp_path / "bb.jsonl",
                    task_board=tmp_path / "tasks.json")
    result = nsmcp.TOOLS["memory_recall"]["fn"]({"query": "postgres"})
    assert isinstance(result, list)
    assert len(result) == 1
    assert "postgres" in result[0]["summary"]


def test_memory_remember_writes_entry_and_returns_ts(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    nsmcp.set_paths(ledger=ledger_path, blackboard=tmp_path / "bb.jsonl",
                    task_board=tmp_path / "tasks.json")
    ts = nsmcp.TOOLS["memory_remember"]["fn"]({
        "type": "lesson", "summary": "always test concurrent access",
    })
    assert isinstance(ts, float) and ts > 0


# ---------------------------------------------------------------------------
# 3. bb_post / bb_read — wrap Blackboard
# ---------------------------------------------------------------------------
def test_bb_post_returns_msg_id_and_bb_read_finds_it(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    nsmcp.set_paths(ledger=tmp_path / "l.jsonl", blackboard=bb_path,
                    task_board=tmp_path / "t.json")
    msg_id = nsmcp.TOOLS["bb_post"]["fn"]({
        "frm": "claude", "to": "codex", "body": "hi codex",
    })
    assert isinstance(msg_id, str) and msg_id.startswith("m")
    msgs = nsmcp.TOOLS["bb_read"]["fn"]({"to_filter": "codex"})
    assert len(msgs) == 1
    assert msgs[0]["body"] == "hi codex"


def test_bb_reply_creates_answer_in_thread(tmp_path):
    bb_path = tmp_path / "bb.jsonl"
    nsmcp.set_paths(ledger=tmp_path / "l.jsonl", blackboard=bb_path,
                    task_board=tmp_path / "t.json")
    thread_id = nsmcp.TOOLS["bb_post"]["fn"]({
        "frm": "claude", "to": "*", "body": "question?", "type": "question",
    })
    reply_id = nsmcp.TOOLS["bb_reply"]["fn"]({
        "thread_id": thread_id, "frm": "codex", "body": "answer!",
    })
    assert isinstance(reply_id, str)
    thread = nsmcp.TOOLS["bb_read"]["fn"]({"thread_id": thread_id})
    assert len(thread) == 2
    assert thread[1]["type"] == "answer"


# ---------------------------------------------------------------------------
# 4. task_add / task_claim / task_release / task_list / task_update
# ---------------------------------------------------------------------------
def test_task_lifecycle_via_mcp_tools(tmp_path):
    """Full lifecycle: add → claim → update(doing) → update(done) → list."""
    tasks_path = tmp_path / "tasks.json"
    nsmcp.set_paths(ledger=tmp_path / "l.jsonl", blackboard=tmp_path / "bb.jsonl",
                    task_board=tasks_path)
    # add
    task_id = nsmcp.TOOLS["task_add"]["fn"]({"goal": "refactor x"})
    assert isinstance(task_id, str)
    # claim
    won = nsmcp.TOOLS["task_claim"]["fn"]({"task_id": task_id, "claimant": "claude"})
    assert won is True
    # second claim loses
    won2 = nsmcp.TOOLS["task_claim"]["fn"]({"task_id": task_id, "claimant": "codex"})
    assert won2 is False
    # update doing
    ok = nsmcp.TOOLS["task_update"]["fn"]({"task_id": task_id, "status": "doing"})
    assert ok is True
    # update done
    ok = nsmcp.TOOLS["task_update"]["fn"]({"task_id": task_id, "status": "done",
                                            "note": "shipped"})
    assert ok is True
    # list by status
    done = nsmcp.TOOLS["task_list"]["fn"]({"status": "done"})
    assert len(done) == 1
    assert done[0]["id"] == task_id


def test_task_release_returns_bool(tmp_path):
    nsmcp.set_paths(ledger=tmp_path / "l.jsonl", blackboard=tmp_path / "bb.jsonl",
                    task_board=tmp_path / "tasks.json")
    task_id = nsmcp.TOOLS["task_add"]["fn"]({"goal": "x"})
    nsmcp.TOOLS["task_claim"]["fn"]({"task_id": task_id, "claimant": "claude"})
    released = nsmcp.TOOLS["task_release"]["fn"]({"task_id": task_id})
    assert released is True
