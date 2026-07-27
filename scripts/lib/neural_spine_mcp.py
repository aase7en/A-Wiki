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
_FOCUS_DIR: Path = REPO_ROOT / ".tmp"


def set_paths(*, ledger: Path | str | None = None,
              blackboard: Path | str | None = None,
              task_board: Path | str | None = None,
              focus_dir: Path | str | None = None) -> None:
    """Override the file paths the tools read/write. Mainly for tests."""
    global _LEDGER_PATH, _BB_PATH, _TASKS_PATH, _FOCUS_DIR
    if ledger is not None:
        _LEDGER_PATH = Path(ledger)
    if blackboard is not None:
        _BB_PATH = Path(blackboard)
    if task_board is not None:
        _TASKS_PATH = Path(task_board)
    if focus_dir is not None:
        _FOCUS_DIR = Path(focus_dir)


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


def tool_memory_semantic_recall(args: dict) -> list[dict]:
    """Semantic search (BM25) over the Memory Ledger — better than substring.

    Use for multi-word queries or when you want ranked relevance.
    Falls back to substring if semantic_recall unavailable.
    """
    query = args.get("query", "")
    limit = int(args.get("limit", 10))
    try:
        import semantic_recall
        return semantic_recall.search(_LEDGER_PATH, query, limit=limit)
    except Exception:
        # Graceful fallback to substring search
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


# ── A-Suite: routing + focus ──────────────────────────────────────────────
#
# These two are the cross-agent parity substrate. A UserPromptSubmit hook can
# only ever serve Claude Code (Codex has no such event; Gemini has two events
# total; Cline/Windsurf/Cursor/Aider have no hooks at all), but every one of
# those harnesses can call an MCP tool. Same registry, same matcher, same
# answer — so routing does not diverge by agent.

def _registry():
    """Load the skills registry. Imported lazily: most MCP calls never need it."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from skills_registry import Registry
    return Registry.load(REPO_ROOT / "skills-registry.json")


def _routing():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from skills_registry import routing
    return routing


def _focus_path() -> Path:
    """Per-session state file. Session id is sanitised — it reaches a filename."""
    import re
    sid = re.sub(r"[^A-Za-z0-9_-]", "_", _session_id())
    return _FOCUS_DIR / f"a-focus-{sid}.json"


def tool_skill_route(args: dict) -> list[dict]:
    """Rank A-Suite skills against a free-text request."""
    text = args.get("text") or args.get("prompt") or ""
    if not text.strip():
        return []
    routing = _routing()
    reg = _registry()
    limit = int(args.get("limit", routing.DEFAULT_LIMIT))
    out: list[dict] = []
    for name, score in routing.route(reg, text, limit=limit):
        skill = reg.get(name) or {}
        out.append({
            "skill": name,
            "score": score,
            "phase": skill.get("a_phase"),
            "invocation_hint": skill.get("invocation_hint") or f"/{name}",
            "description": skill.get("th_description") or skill.get("description", ""),
        })
    return out


def _read_focus() -> dict | None:
    """Read focus state, tolerating scripts/lib/a_flow_state.py's key names.

    Two writers share .tmp/a-focus-<session>.json: these MCP tools and
    a_flow_state.py (the A-Flow stage gate), which deliberately adopted this
    path for interop but uses different keys for the same concepts:

        a_flow_state        here
        ------------        ----
        completed_phases    phases_done
        started_ts          started_at
        active: false       complete: true

    Without normalisation, a flow started by one side and advanced by the other
    grows duplicate keys, and this side's Stop hook nags about a run the other
    side already finished. Normalising on read costs nothing and makes the file
    safe no matter which system wrote it.
    """
    import json
    p = _focus_path()
    if not p.exists():
        return None
    try:
        state = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # A corrupt focus file must not wedge the session — treat as no focus.
        return None
    if not isinstance(state, dict):
        return None
    if "phases_done" not in state and "completed_phases" in state:
        state["phases_done"] = list(state.get("completed_phases") or [])
    if "started_at" not in state and "started_ts" in state:
        state["started_at"] = state.get("started_ts")
    if "complete" not in state and state.get("active") is False:
        state["complete"] = True
    return state


def _write_focus(state: dict) -> dict:
    """Write focus state in BOTH key spellings so a_flow_state.py can read it."""
    import json
    p = _focus_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = time.time()
    # Mirror onto a_flow_state.py's schema — same file, two readers.
    done = list(state.get("phases_done") or [])
    state["completed_phases"] = done
    state.setdefault("started_ts", int(state.get("started_at") or time.time()))
    state["active"] = not state.get("complete", False) and state.get("phase") is not None
    state.setdefault("allowed_files", [])
    state.setdefault("notes", [])
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def tool_focus_set(args: dict) -> dict:
    """Declare what is being worked on and which phase it is in."""
    routing = _routing()
    skill = (args.get("skill") or "").strip()
    if not skill:
        raise ValueError("focus_set requires 'skill'")
    phase = args.get("phase") or routing.A_PHASE_CHAIN[0]
    if phase not in routing.A_PHASE_CHAIN:
        raise ValueError(
            f"unknown phase {phase!r}; valid: {', '.join(routing.A_PHASE_CHAIN)}"
        )
    return _write_focus({
        "skill": skill,
        "goal": args.get("goal", ""),
        "phase": phase,
        "phases_done": [],
        "session_id": _session_id(),
        "started_at": time.time(),
    })


def tool_focus_get(args: dict) -> dict | None:
    """Current focus, or None. Cheap — callers may poll it."""
    return _read_focus()


def tool_focus_advance(args: dict) -> dict:
    """Move to the next phase, recording the one just finished."""
    routing = _routing()
    state = _read_focus()
    if not state:
        raise ValueError("no active focus — call focus_set first")
    current = state.get("phase")
    if current:
        done = state.setdefault("phases_done", [])
        if current not in done:
            done.append(current)
    nxt = routing.next_phase(current) if current in routing.A_PHASE_CHAIN else None
    state["phase"] = nxt
    state["complete"] = nxt is None
    return _write_focus(state)


def tool_focus_clear(args: dict) -> dict:
    """End the focus session. Idempotent."""
    p = _focus_path()
    existed = p.exists()
    if existed:
        try:
            p.unlink()
        except OSError:
            pass
    return {"cleared": existed}


# ── Cross-agent work claims ───────────────────────────────────────────────
# The coordination layer. Exposed over MCP so ZCode, Codex, Gemini and Claude
# all use the SAME store — a Claude-only hook could never have prevented the
# 2026-07-27 duplicate-router incident, because the other agent was ZCode.

def _claims():
    import agent_claims
    return agent_claims


def _agent_name(args: dict) -> str:
    explicit = (args.get("agent") or "").strip()
    if explicit:
        return explicit
    for env, name in (("ZCODE_SESSION_ID", "zcode"), ("CLAUDE_SESSION_ID", "claude"),
                      ("CODEX_SESSION_ID", "codex"), ("GEMINI_SESSION_ID", "gemini")):
        if os.environ.get(env):
            return name
    return os.environ.get("AWIKI_AGENT", "unknown")


def tool_claim_acquire(args: dict) -> dict:
    ac = _claims()
    return ac.acquire(
        agent=_agent_name(args),
        scope=args.get("scope") or [],
        goal=args.get("goal", ""),
        phase=args.get("phase", "ask"),
        session_id=_session_id(),
    )


def tool_claim_list(args: dict) -> dict:
    ac = _claims()
    claims = ac.live()
    return {"claims": claims, "summary": ac.describe(claims)}


def tool_claim_release(args: dict) -> dict:
    ac = _claims()
    cid = args.get("claim_id")
    if cid:
        return {"released": ac.release(cid)}
    return {"released": ac.release_session(_session_id())}


def tool_claim_advance(args: dict) -> dict:
    return _claims().advance(args["claim_id"], args["phase"])


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
    "memory_semantic_recall": {
        "fn": tool_memory_semantic_recall,
        "description": "Semantic search (BM25 ranked) over the Memory Ledger. Better than memory_recall for multi-word queries or when you want ranked relevance. Falls back to substring if unavailable.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language query (multi-word OK, ranked by relevance)"},
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
    # ── A-Suite (C4) ──────────────────────────────────────────────────────
    "skill_route": {
        "fn": tool_skill_route,
        "description": (
            "Pick the right A-Wiki skill for a request. Matches the text against the "
            "machine-readable `triggers` in skills-registry.json (Thai substring + "
            "ASCII prefix-boundary) and returns ranked candidates with their "
            "invocation hint. Empty list means nothing matched — fall back to "
            "/A-Think rather than guessing. Read-only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "the user's request, verbatim"},
                "limit": {"type": "integer", "default": 3},
            },
            "required": ["text"],
        },
    },
    "focus_set": {
        "fn": tool_focus_set,
        "description": (
            "Declare the skill, goal and phase being worked on, so the session stops "
            "drifting between phases. Phases: ask → design → plan → implement → "
            "review → debug → test. Call at the start of any non-trivial task."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "e.g. a-plan, a-debug"},
                "goal": {"type": "string", "description": "one line: what done looks like"},
                "phase": {
                    "type": "string",
                    "enum": ["ask", "design", "plan", "implement", "review", "debug", "test"],
                    "description": "starting phase (default: ask)",
                },
            },
            "required": ["skill"],
        },
    },
    "focus_get": {
        "fn": tool_focus_get,
        "description": "Current focus (skill, goal, phase, phases completed), or null. Read-only.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "focus_advance": {
        "fn": tool_focus_advance,
        "description": (
            "Finish the current phase and move to the next one in the chain. "
            "Returns phase=null and complete=true at the end of the chain."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    "focus_clear": {
        "fn": tool_focus_clear,
        "description": "End the focus session and delete its state. Idempotent.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # ── Cross-agent coordination (MANDATORY before shared-surface work) ──
    "claim_acquire": {
        "fn": tool_claim_acquire,
        "description": (
            "REQUIRED before editing shared surfaces (skills/, scripts/, commands/, "
            "skills-registry.json, AGENTS.md). Registers what you are about to build "
            "so other agents (ZCode, Codex, Gemini, Claude) can see it and not "
            "duplicate it. A PreToolUse hook BLOCKS edits that land inside another "
            "agent's live claim. Claims carry a TTL lease and self-reap."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {"type": "array", "items": {"type": "string"},
                          "description": "glob(s) you will touch, e.g. [\"skills/awiki/**\"]"},
                "goal": {"type": "string", "description": "one line: what done looks like"},
                "phase": {"type": "string",
                          "enum": ["ask", "design", "plan", "implement", "review", "debug", "test"]},
                "agent": {"type": "string", "description": "override detected identity"},
            },
            "required": ["scope", "goal"],
        },
    },
    "claim_list": {
        "fn": tool_claim_list,
        "description": (
            "Who else is working right now, on what, in which phase. Call this BEFORE "
            "starting anything non-trivial — it is the cheapest way to avoid building "
            "something another agent already has in flight. Read-only."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    "claim_release": {
        "fn": tool_claim_release,
        "description": "Release a claim by id, or all claims held by this session if omitted.",
        "inputSchema": {"type": "object", "properties": {"claim_id": {"type": "string"}}},
    },
    "claim_advance": {
        "fn": tool_claim_advance,
        "description": "Move a claim to a new phase and renew its lease.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "phase": {"type": "string",
                          "enum": ["ask", "design", "plan", "implement", "review", "debug", "test"]},
            },
            "required": ["claim_id", "phase"],
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
