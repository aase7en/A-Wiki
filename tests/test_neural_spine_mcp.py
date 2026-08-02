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
# A-Council 2026-08-02 critical fix #3 + sandbox integration.
# Every test in this module gets:
#   (a) AWIKI_DATA_DIR pointed at a per-test tmp sandbox, so set_paths()
#       accepts the tmp_path and the new path-traversal guard passes.
#   (b) agent_claims store redirected to tmp_path, so claim_acquire/list/
#       release never touch the real REPO_ROOT/.tmp/agent-claims.json
#       (previously a live Iron Law #11 leak — see test-engineer finding #1).
#   (c) neural_spine_mcp state restored to defaults after the test, so a
#       wired mock cannot leak into the next test (security-auditor finding
#       on _wire global mutation).
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AWIKI_DATA_DIR", str(tmp_path))
    import agent_claims
    agent_claims.set_store(tmp_path / "claims.json")
    # Snapshot nsmcp wiring so we can restore it even if the test wired a mock
    snap = (nsmcp._memory, nsmcp._taskboard,
            nsmcp._LEDGER_PATH, nsmcp._BB_PATH, nsmcp._TASKS_PATH,
            nsmcp._FOCUS_DIR,
            nsmcp._memory_explicitly_wired, nsmcp._taskboard_explicitly_wired)
    yield tmp_path
    # Restore: production defaults, clear explicit-wired flags
    (nsmcp._memory, nsmcp._taskboard,
     nsmcp._LEDGER_PATH, nsmcp._BB_PATH, nsmcp._TASKS_PATH,
     nsmcp._FOCUS_DIR,
     nsmcp._memory_explicitly_wired, nsmcp._taskboard_explicitly_wired) = snap
    try:
        agent_claims.set_store(None)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. TOOLS dict exposes all Neural Spine tools with correct shape
#    Char-test extension 2026-08-01 (ADR-0012 slice A4): covers the 9+ tools
#    that the original test omitted (semantic_recall, skill_route, focus_*,
#    claim_*). Total now 19 tools — was undercounted at 10.
# ---------------------------------------------------------------------------
def test_tools_dict_has_all_neural_spine_tools():
    """All 19 tools must be registered for agents to use.

    Char-test (ADR-0012 slice A4): the original 10-tool assertion silently
    passed while 9 real tools were untested. We now enumerate every tool
    actually present in the module so a regression (tool removal) fails loud.
    """
    expected = {
        # Memory (3)
        "memory_recall", "memory_semantic_recall", "memory_remember",
        # Blackboard (3)
        "bb_post", "bb_read", "bb_reply",
        # Task Board (5)
        "task_add", "task_claim", "task_release", "task_list", "task_update",
        # A-Suite: routing + focus (5)
        "skill_route", "focus_set", "focus_get", "focus_advance", "focus_clear",
        # Cross-agent claims (4)
        "claim_acquire", "claim_list", "claim_release", "claim_advance",
    }
    actual = set(nsmcp.TOOLS.keys())
    missing = expected - actual
    assert not missing, f"missing MCP tools: {missing}"
    extra = actual - expected
    # If a tool is added later, force this test to be updated — don't let
    # new tools ship untested (the very gap this char-test fixes).
    assert not extra, f"untracked tool — extend this assertion + add a test: {extra}"


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


# ---------------------------------------------------------------------------
# 5. memory_semantic_recall — char-test (ADR-0012 slice A4)
#    Behavioural contract: returns a list, degrades gracefully when the
#    optional semantic_recall module is absent (falls back to substring).
# ---------------------------------------------------------------------------
def test_memory_semantic_recall_returns_list_and_degrades(tmp_path):
    """Semantic recall must return a list even when the optional BM25 module
    is missing — it falls back to substring search. A bare except hides bugs,
    so we pin the contract: a list, possibly empty, never an exception."""
    ledger_path = tmp_path / "ledger.jsonl"
    import memory_ledger
    memory_ledger.MemoryLedger(ledger_path).append(
        session_id="s", type="lesson", summary="prefer ports over frameworks",
        tags=["architecture"],
    )
    nsmcp.set_paths(ledger=ledger_path, blackboard=tmp_path / "bb.jsonl",
                    task_board=tmp_path / "t.json")
    result = nsmcp.TOOLS["memory_semantic_recall"]["fn"]({"query": "ports"})
    assert isinstance(result, list)
    # Whether BM25 or substring path ran, the seeded entry must be findable
    # by a query that literally appears in its summary.
    assert any("ports" in e.get("summary", "") for e in result)


# ---------------------------------------------------------------------------
# 6. skill_route — char-test (ADR-0012 slice A4)
#    Behavioural contract: empty text → empty list (fall back to /A-Think);
#    non-empty text → ranked candidates with the documented shape. Read-only.
# ---------------------------------------------------------------------------
def test_skill_route_empty_text_returns_empty_list():
    """Empty / whitespace-only text must short-circuit to []. This is the
    documented contract in the tool description and is load-bearing for the
    UserPromptSubmit hook substrate."""
    assert nsmcp.TOOLS["skill_route"]["fn"]({"text": ""}) == []
    assert nsmcp.TOOLS["skill_route"]["fn"]({"text": "   "}) == []


def test_skill_route_returns_candidates_with_documented_shape():
    """Real registry, real query. Each candidate must carry the keys the
    tool description promises (skill, score, phase, invocation_hint,
    description). We don't assert on ranking order here — that's the
    routing module's own test suite — only on the wrapper's shape."""
    # Use a query that any reasonable skill registry will match something for.
    out = nsmcp.TOOLS["skill_route"]["fn"]({"text": "ออกแบบ database schema"})
    assert isinstance(out, list)
    if not out:  # registry may be empty in a fresh clone — skip shape check
        import warnings
        warnings.warn("skills-registry.json returned no matches; shape check skipped")
        return
    keys_expected = {"skill", "score", "phase", "invocation_hint", "description"}
    for cand in out:
        assert keys_expected <= set(cand.keys()), \
            f"skill_route candidate missing keys: {keys_expected - set(cand.keys())}"


# ---------------------------------------------------------------------------
# 7. focus lifecycle — char-test (ADR-0012 slice A4)
#    set → get → advance → clear. Pins the dual-key interop with a_flow_state
#    (phases_done ↔ completed_phases) without which the Stop hook nags.
# ---------------------------------------------------------------------------
def test_focus_lifecycle_set_get_advance_clear(tmp_path):
    nsmcp.set_paths(ledger=tmp_path / "l.jsonl", blackboard=tmp_path / "bb.jsonl",
                    task_board=tmp_path / "t.json", focus_dir=tmp_path)
    # set — starts at 'ask'
    state = nsmcp.TOOLS["focus_set"]["fn"]({
        "skill": "a-plan", "goal": "design db", "phase": "ask",
    })
    assert state["phase"] == "ask"
    assert state["skill"] == "a-plan"
    # get returns the same state
    got = nsmcp.TOOLS["focus_get"]["fn"]({})
    assert got is not None
    assert got["skill"] == "a-plan"
    # advance moves the phase and records completion
    advanced = nsmcp.TOOLS["focus_advance"]["fn"]({})
    assert "ask" in advanced.get("phases_done", [])
    assert advanced["phase"] != "ask"
    # clear is idempotent
    first_clear = nsmcp.TOOLS["focus_clear"]["fn"]({})
    assert first_clear["cleared"] is True
    second_clear = nsmcp.TOOLS["focus_clear"]["fn"]({})
    assert second_clear["cleared"] is False


def test_focus_set_rejects_unknown_phase(tmp_path):
    nsmcp.set_paths(focus_dir=tmp_path)
    import pytest as _pytest
    with _pytest.raises(ValueError):
        nsmcp.TOOLS["focus_set"]["fn"]({"skill": "x", "phase": "not-a-phase"})


def test_focus_advance_without_set_raises(tmp_path):
    nsmcp.set_paths(focus_dir=tmp_path)
    import pytest as _pytest
    with _pytest.raises(ValueError):
        nsmcp.TOOLS["focus_advance"]["fn"]({})


# ---------------------------------------------------------------------------
# 8. claim lifecycle — char-test (ADR-0012 slice A4)
#    acquire → list → advance → release. These are the Iron Law #11 gate
#    primitives, so their MCP surface must be a faithful pass-through.
#
#    A-Council 2026-08-02 critical #3 fix: the autouse _isolated_data_dir
#    fixture now redirects the claim store to tmp_path via
#    agent_claims.set_store(), so these tests no longer touch the real
#    REPO_ROOT/.tmp/agent-claims.json. The old isolated_session fixture
#    leaked (it only set ZCODE_SESSION_ID; the store stayed on the repo
#    default bound at import time).
# ---------------------------------------------------------------------------
def _unique_session(monkeypatch):
    """Unique session id per test so claim tests don't collide. Store
    isolation itself is handled by the autouse fixture."""
    import uuid
    sid = f"char-test-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("ZCODE_SESSION_ID", sid)
    return sid


def test_claim_acquire_returns_dict_with_id(monkeypatch):
    _unique_session(monkeypatch)
    result = nsmcp.TOOLS["claim_acquire"]["fn"]({
        "scope": ["scripts/foo/**"], "goal": "test goal",
    })
    assert isinstance(result, dict)
    assert "id" in result
    assert result["scope"] == ["scripts/foo/**"]


def test_claim_list_returns_claims_and_summary(monkeypatch):
    _unique_session(monkeypatch)
    nsmcp.TOOLS["claim_acquire"]["fn"]({
        "scope": ["scripts/bar/**"], "goal": "another",
    })
    out = nsmcp.TOOLS["claim_list"]["fn"]({})
    assert "claims" in out and "summary" in out
    assert isinstance(out["claims"], list)
    assert len(out["claims"]) >= 1


def test_claim_release_by_session_releases_all(monkeypatch):
    _unique_session(monkeypatch)
    nsmcp.TOOLS["claim_acquire"]["fn"]({
        "scope": ["scripts/baz/**"], "goal": "to release",
    })
    out = nsmcp.TOOLS["claim_release"]["fn"]({})  # no claim_id → by session
    # Finding: release_session returns the COUNT released (int, truthy).
    assert out["released"], f"expected truthy release count, got {out['released']!r}"
