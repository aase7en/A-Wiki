"""neural_spine_mcp.py — MCP tool wrappers for Neural Spine primitives.

Exposes a TOOLS dict that the awiki MCP server merges into its own TOOLS
registry. Each tool wraps a primitive (memory_ledger / blackboard /
task_board) so any MCP-aware agent can call them.

Path configuration:
  set_paths(ledger=..., blackboard=..., task_board=...)
  Defaults point to REPO_ROOT/.tmp/{memory-ledger.jsonl,blackboard.jsonl,
  task-board.json}.

The wrappers are intentionally thin — they validate args minimally and
delegate to the underlying primitives, which already have their own
concurrency-safety via atomic_json (chunk 1).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import memory_ledger  # noqa: E402 -- chunk 2
import blackboard     # noqa: E402 -- chunk 4
import task_board     # noqa: E402 -- chunk 5

REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LEDGER = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
_DEFAULT_BB = REPO_ROOT / ".tmp" / "blackboard.jsonl"
_DEFAULT_TASKS = REPO_ROOT / ".tmp" / "task-board.json"

# Configurable paths (so tests can isolate). Use module-level state.
_LEDGER_PATH: Path = _DEFAULT_LEDGER
_BB_PATH: Path = _DEFAULT_BB
_TASKS_PATH: Path = _DEFAULT_TASKS


def set_paths(*, ledger: Path | str | None = None,
              blackboard: Path | str | None = None,
              task_board: Path | str | None = None) -> None:
    """Override the file paths the tools read/write. Mainly for tests."""
    global _LEDGER_PATH, _BB_PATH, _TASKS_PATH
    if ledger is not None:
        _LEDGER_PATH = Path(ledger)
    if blackboard is not None:
        _BB_PATH = Path(blackboard)
    if task_board is not None:
        _TASKS_PATH = Path(task_board)


def _session_id() -> str:
    return os.environ.get("ZCODE_SESSION_ID") or \
           os.environ.get("CLAUDE_SESSION_ID") or \
           os.environ.get("CODEX_SESSION_ID") or "mcp"


# ── Memory tools ──────────────────────────────────────────────────────────
def tool_memory_recall(args: dict) -> list[dict]:
    """Search the Memory Ledger."""
    query = args.get("query", "")
    limit = int(args.get("limit", 10))
    return memory_ledger.MemoryLedger(_LEDGER_PATH).search(query, limit=limit)


def tool_memory_remember(args: dict) -> float:
    """Append a manual entry to the Memory Ledger. Returns its ts."""
    return memory_ledger.MemoryLedger(_LEDGER_PATH).append(
        session_id=_session_id(),
        type=args["type"],
        summary=args["summary"],
        files=args.get("files", []),
        tags=args.get("tags", []),
    )


# ── Blackboard tools ──────────────────────────────────────────────────────
def tool_bb_post(args: dict) -> str:
    board = blackboard.Blackboard(_BB_PATH)
    return board.post(
        frm=args["frm"],
        to=args["to"],
        body=args["body"],
        msg_type=args.get("type", "msg"),
        thread_id=args.get("thread_id"),
    )


def tool_bb_read(args: dict) -> list[dict]:
    board = blackboard.Blackboard(_BB_PATH)
    return board.read(
        since_ts=float(args.get("since_ts", 0.0)),
        thread_id=args.get("thread_id"),
        to_filter=args.get("to_filter"),
        limit=int(args.get("limit", 200)),
    )


def tool_bb_reply(args: dict) -> str:
    board = blackboard.Blackboard(_BB_PATH)
    return board.reply(
        thread_id=args["thread_id"],
        frm=args["frm"],
        body=args["body"],
        msg_type=args.get("type", "answer"),
    )


# ── Task Board tools ──────────────────────────────────────────────────────
def tool_task_add(args: dict) -> str:
    board = task_board.TaskBoard(_TASKS_PATH)
    return board.add(
        goal=args["goal"],
        files=args.get("files", []),
        parent_goal_id=args.get("parent_goal_id"),
        lease_minutes=int(args.get("lease_minutes", 30)),
    )


def tool_task_claim(args: dict) -> bool:
    board = task_board.TaskBoard(_TASKS_PATH)
    return board.claim(
        args["task_id"],
        claimant=args["claimant"],
        lease_minutes=int(args.get("lease_minutes", 30)),
    )


def tool_task_release(args: dict) -> bool:
    return task_board.TaskBoard(_TASKS_PATH).release(args["task_id"])


def tool_task_update(args: dict) -> bool:
    return task_board.TaskBoard(_TASKS_PATH).update(
        args["task_id"],
        status=args["status"],
        note=args.get("note"),
    )


def tool_task_list(args: dict) -> list[dict]:
    return task_board.TaskBoard(_TASKS_PATH).list(status=args.get("status"))


# ── TOOLS registry (merged into awiki MCP server TOOLS) ───────────────────
TOOLS: dict[str, dict[str, Any]] = {
    "memory_recall": {
        "fn": tool_memory_recall,
        "description": "Search the cross-session Memory Ledger (decisions, lessons, failures, outcomes, ideas). Use to recall prior context across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Substring query (matched against summary + tags)"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    "memory_remember": {
        "fn": tool_memory_remember,
        "description": "Persist a manual entry to the Memory Ledger. Use when learning a lesson, recording a decision, or noting an outcome.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["decision", "lesson", "failure", "outcome", "idea"]},
                "summary": {"type": "string", "description": "1-line human-readable summary"},
                "files": {"type": "array", "items": {"type": "string"}, "default": []},
                "tags": {"type": "array", "items": {"type": "string"}, "default": []},
            },
            "required": ["type", "summary"],
        },
    },
    "bb_post": {
        "fn": tool_bb_post,
        "description": "Post a message to the Blackboard (async channel between agents). Use to ask/answer/@mention another agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "frm": {"type": "string", "description": "sender agent name (claude|codex|gemini|cline|user|...)"},
                "to": {"type": "string", "description": "recipient agent name or '*' for broadcast"},
                "body": {"type": "string"},
                "type": {"type": "string", "enum": ["msg", "question", "proposal", "answer"], "default": "msg"},
                "thread_id": {"type": "string", "description": "existing thread id to reply in (omit to start new)"},
            },
            "required": ["frm", "to", "body"],
        },
    },
    "bb_read": {
        "fn": tool_bb_read,
        "description": "Read Blackboard messages. Filter by recipient (to_filter), thread, or timestamp.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since_ts": {"type": "number", "default": 0, "description": "only messages after this timestamp"},
                "thread_id": {"type": "string"},
                "to_filter": {"type": "string", "description": "only messages addressed to this agent (or broadcast '*')"},
                "limit": {"type": "integer", "default": 200},
            },
        },
    },
    "bb_reply": {
        "fn": tool_bb_reply,
        "description": "Reply to a Blackboard thread. msg_type defaults to 'answer'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread_id": {"type": "string"},
                "frm": {"type": "string"},
                "body": {"type": "string"},
                "type": {"type": "string", "enum": ["msg", "question", "proposal", "answer"], "default": "answer"},
            },
            "required": ["thread_id", "frm", "body"],
        },
    },
    "task_add": {
        "fn": tool_task_add,
        "description": "Add a task to the Task Board. Other agents can claim it. Use to decompose a goal into resumable chunks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "one concrete result"},
                "files": {"type": "array", "items": {"type": "string"}, "default": []},
                "parent_goal_id": {"type": "string"},
                "lease_minutes": {"type": "integer", "default": 30},
            },
            "required": ["goal"],
        },
    },
    "task_claim": {
        "fn": tool_task_claim,
        "description": "Atomically claim a task. Returns true if this caller won, false if already claimed. Crash-safe via TTL lease.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "claimant": {"type": "string", "description": "your agent name"},
                "lease_minutes": {"type": "integer", "default": 30},
            },
            "required": ["task_id", "claimant"],
        },
    },
    "task_release": {
        "fn": tool_task_release,
        "description": "Release a claimed task back to 'todo' so another agent can pick it up.",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    "task_list": {
        "fn": tool_task_list,
        "description": "List tasks, optionally filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "claimed", "doing", "done", "blocked"]},
            },
        },
    },
    "task_update": {
        "fn": tool_task_update,
        "description": "Update a task's status, optionally appending a note.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "claimed", "doing", "done", "blocked"]},
                "note": {"type": "string"},
            },
            "required": ["task_id", "status"],
        },
    },
}
