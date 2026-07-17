"""Tests for scripts/lib/blackboard.py — async messaging channel between agents.

Iron Law #1: failing tests written FIRST.

Blackboard คือช่องคุยระหว่าง agent ของสมอง A-Wiki. ทำให้ Claude Code,
Codex, Gemini CLI, Cline สามารถถาม/ตอบ/@mention กันได้แบบ async.

Schema (JSONL, 1 บรรทัดต่อ message):
  {ts, id, from, to, type, body, thread_id, replies: []}

type ∈ {msg, question, proposal, answer}
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import blackboard as bb  # noqa: E402 -- module under test (created by this chunk)


# ---------------------------------------------------------------------------
# 1. post — writes one message, returns its id
# ---------------------------------------------------------------------------
def test_post_creates_message_and_returns_id(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    msg_id = board.post(
        frm="claude", to="codex", body="can you check the auth module?",
        msg_type="question",
    )
    assert msg_id is not None and isinstance(msg_id, str)
    msgs = board.read()
    assert len(msgs) == 1
    assert msgs[0]["from"] == "claude"
    assert msgs[0]["to"] == "codex"
    assert msgs[0]["body"] == "can you check the auth module?"
    assert msgs[0]["type"] == "question"
    assert msgs[0]["id"] == msg_id


def test_post_assigns_unique_monotonic_ids(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    id1 = board.post(frm="a", to="*", body="m1")
    id2 = board.post(frm="b", to="*", body="m2")
    assert id1 != id2


def test_post_rejects_invalid_msg_type(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    with pytest.raises(ValueError):
        board.post(frm="a", to="b", body="x", msg_type="garbage")


# ---------------------------------------------------------------------------
# 2. read — filtering by recipient, thread, since_ts
# ---------------------------------------------------------------------------
def test_read_filters_by_recipient(tmp_path):
    """Agent should only see messages addressed to them (or to '*'/broadcast)."""
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    board.post(frm="claude", to="codex", body="private to codex")
    board.post(frm="claude", to="gemini", body="private to gemini")
    board.post(frm="claude", to="*", body="broadcast")
    codex_msgs = board.read(to_filter="codex")
    assert len(codex_msgs) == 2  # private + broadcast
    bodies = [m["body"] for m in codex_msgs]
    assert "private to codex" in bodies
    assert "broadcast" in bodies
    assert "private to gemini" not in bodies


def test_read_filters_by_thread(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    tid = board.post(frm="a", to="*", body="start thread")
    board.post(frm="b", to="*", body="unrelated")
    thread_msgs = board.read(thread_id=tid)
    assert len(thread_msgs) == 1
    assert thread_msgs[0]["body"] == "start thread"


def test_read_since_ts_filters_old_messages(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    board.post(frm="a", to="*", body="old")
    import time
    cutoff = time.time() + 0.001  # slightly in the future
    time.sleep(0.01)
    board.post(frm="b", to="*", body="new")
    new_msgs = board.read(since_ts=cutoff)
    assert len(new_msgs) == 1
    assert new_msgs[0]["body"] == "new"


# ---------------------------------------------------------------------------
# 3. reply — posts an answer into an existing thread
# ---------------------------------------------------------------------------
def test_reply_associates_with_thread(tmp_path):
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    thread_id = board.post(frm="claude", to="codex", body="what about X?", msg_type="question")
    reply_id = board.reply(thread_id=thread_id, frm="codex", body="X is at scripts/x.py", msg_type="answer")
    assert reply_id is not None
    thread_msgs = board.read(thread_id=thread_id)
    assert len(thread_msgs) == 2
    assert thread_msgs[0]["body"] == "what about X?"
    assert thread_msgs[1]["body"] == "X is at scripts/x.py"
    assert thread_msgs[1]["type"] == "answer"


def test_reply_to_unknown_thread_creates_orphan_answer(tmp_path):
    """Reply to non-existent thread: still write it, but it has no parent context.

    We choose robustness over strict validation — agents may reply after
    restarts where the original thread id was lost.
    """
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    reply_id = board.reply(thread_id="ghost-thread", frm="a", body="late reply")
    assert reply_id is not None
    msgs = board.read()
    assert len(msgs) == 1


# ---------------------------------------------------------------------------
# 4. concurrency — concurrent posts never lose messages
# ---------------------------------------------------------------------------
def test_concurrent_posts_never_lose_messages(tmp_path):
    """10 agents each post 5 messages concurrently → all 50 must persist."""
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    N_AGENTS = 10
    MSGS_PER_AGENT = 5
    barrier = threading.Barrier(N_AGENTS)

    def agent_worker(agent_id):
        barrier.wait()
        for i in range(MSGS_PER_AGENT):
            board.post(
                frm=f"agent-{agent_id}",
                to="*" if i == 0 else f"agent-{(agent_id+1) % N_AGENTS}",
                body=f"msg-{agent_id}-{i}",
            )

    threads = [threading.Thread(target=agent_worker, args=(i,)) for i in range(N_AGENTS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    msgs = board.read()
    assert len(msgs) == N_AGENTS * MSGS_PER_AGENT, (
        f"expected {N_AGENTS * MSGS_PER_AGENT} messages, got {len(msgs)} — "
        f"concurrent posts lost data"
    )
    # All must be valid JSON-parsed dicts (no corruption)
    for m in msgs:
        assert "body" in m and "from" in m


# ---------------------------------------------------------------------------
# 5. persistence — survives Blackboard instance recreation (cross-session)
# ---------------------------------------------------------------------------
def test_blackboard_survives_recreation(tmp_path):
    """agent A posts → agent B (new instance) reads it. Cross-session continuity."""
    f = tmp_path / "bb.jsonl"
    bb.Blackboard(f).post(frm="claude", to="codex", body="hello from yesterday")
    board_b = bb.Blackboard(f)
    msgs = board_b.read(to_filter="codex")
    assert len(msgs) == 1
    assert msgs[0]["body"] == "hello from yesterday"


# ---------------------------------------------------------------------------
# 6. @mention detection — helpers for the chat UI
# ---------------------------------------------------------------------------
def test_extract_mentions_finds_at_references(tmp_path):
    """Body containing '@codex' or '@claude' should be detected as a mention."""
    board = bb.Blackboard(tmp_path / "bb.jsonl")
    mentions = board.extract_mentions("hey @codex can you help @gemini with this?")
    assert "codex" in mentions
    assert "gemini" in mentions
    assert "claude" not in mentions
