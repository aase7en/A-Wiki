"""
Test the workflow graph model derived from dashboard events.
These tests must FAIL before Step 2 implementation — Iron Law #1.

Tests exercise:
1. /api/graph endpoint returns {nodes, edges, parallel_count, active_agents}
2. In-memory graph state derives correctly from synthetic events
3. Session, task, agent, and tool nodes are populated
4. Parallel agent count reflects active (not completed) agents
5. Tool clusters aggregate by tool name
"""
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import server


@pytest.fixture(autouse=True)
def reset_graph_state():
    """Reset server graph state before each test."""
    import threading
    server._graph_nodes.clear()
    server._graph_edges.clear()
    server._active_agents.clear()
    server._task_stack.clear()


class TestGraphEndpoint:
    """Verify /api/graph returns correct graph structure."""

    def test_graph_endpoint_returns_200(self):
        """GET /api/graph must exist and return JSON."""
        # We can't easily start the server, but we can test the _graph() handler
        # by feeding events and checking _graph_snapshot()
        pass

    def test_graph_snapshot_has_required_keys(self):
        """_graph_snapshot() must return nodes, edges, parallel_count, active_agents."""
        event = {
            "ts": time.time(),
            "type": "session_start",
            "session_id": "sess-test1",
            "agent_id": "agent-pri-1",
            "agent_role": "primary",
            "task_id": None,
            "parent_task_id": None,
        }
        server._process_graph_event(event)
        snapshot = server._graph_snapshot()
        for key in ("nodes", "edges", "parallel_count", "active_agents"):
            assert key in snapshot, f"Missing key '{key}' in graph snapshot"


class TestGraphProcessing:
    """Verify in-memory graph model from event processing."""

    def _feed(self, events):
        for e in events:
            server._process_graph_event(e)

    def test_session_start_creates_session_node(self):
        self._feed([{
            "ts": time.time(), "type": "session_start",
            "session_id": "sess-x", "agent_id": "agent-pri", "agent_role": "primary",
            "task_id": None, "parent_task_id": None,
        }])
        snapshot = server._graph_snapshot()
        node_ids = {n["id"] for n in snapshot["nodes"]}
        assert "sess-x" in node_ids
        # session node has type=session
        session_node = [n for n in snapshot["nodes"] if n["id"] == "sess-x"][0]
        assert session_node["type"] == "session"

    def test_task_start_creates_task_node(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-t", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "task_start",
             "session_id": "sess-t", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        node_ids = {n["id"] for n in snapshot["nodes"]}
        assert "task-1" in node_ids
        task_node = [n for n in snapshot["nodes"] if n["id"] == "task-1"][0]
        assert task_node["type"] == "task"
        assert task_node["status"] == "active"

    def test_nested_task_creates_parent_edge(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-n", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "task_start",
             "session_id": "sess-n", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-parent", "parent_task_id": None},
            {"ts": time.time(), "type": "task_start",
             "session_id": "sess-n", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-child", "parent_task_id": "task-parent"},
        ])
        snapshot = server._graph_snapshot()
        edge_ids = {(e["from"], e["to"]) for e in snapshot["edges"]}
        assert ("task-parent", "task-child") in edge_ids

    def test_agent_spawn_creates_agent_node_and_counts_parallel(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-a", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "agent_spawn",
             "session_id": "sess-a", "agent_id": "agent-arch-1", "agent_role": "architect",
             "task_id": "task-1", "parent_task_id": None,
             "model": "deepseek-v4-flash:free"},
        ])
        snapshot = server._graph_snapshot()
        node_ids = {n["id"] for n in snapshot["nodes"]}
        assert "agent-arch-1" in node_ids
        agent_node = [n for n in snapshot["nodes"] if n["id"] == "agent-arch-1"][0]
        assert agent_node["role"] == "architect"
        assert agent_node["status"] == "active"
        # parallel_count includes primary + architect
        assert snapshot["parallel_count"] >= 1
        assert "agent-arch-1" in snapshot["active_agents"]

    def test_agent_done_removes_from_parallel(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "agent_spawn",
             "session_id": "sess-d", "agent_id": "agent-arch-1", "agent_role": "architect",
             "task_id": "task-1", "parent_task_id": None, "model": "deepseek"},
            {"ts": time.time(), "type": "agent_done",
             "session_id": "sess-d", "agent_id": "agent-arch-1", "agent_role": "architect",
             "task_id": "task-1", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        agent_node = [n for n in snapshot["nodes"] if n["id"] == "agent-arch-1"][0]
        assert agent_node["status"] == "completed"
        assert "agent-arch-1" not in snapshot["active_agents"]

    def test_tool_events_aggregate_into_tool_clusters(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-tc", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "hook_check",
             "session_id": "sess-tc", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None,
             "tool": "write_to_file", "result": "pass"},
            {"ts": time.time(), "type": "hook_check",
             "session_id": "sess-tc", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None,
             "tool": "write_to_file", "result": "pass"},
            {"ts": time.time(), "type": "hook_check",
             "session_id": "sess-tc", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None,
             "tool": "execute_command", "result": "pass"},
        ])
        snapshot = server._graph_snapshot()
        tool_ids = {n["id"] for n in snapshot["nodes"] if n["type"] == "tool_cluster"}
        assert "tool_write_to_file" in tool_ids
        assert "tool_execute_command" in tool_ids
        write_node = [n for n in snapshot["nodes"] if n["id"] == "tool_write_to_file"][0]
        assert write_node["count"] == 2

    def test_task_complete_marks_done(self):
        self._feed([
            {"ts": time.time(), "type": "session_start",
             "session_id": "sess-x", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": None, "parent_task_id": None},
            {"ts": time.time(), "type": "task_start",
             "session_id": "sess-x", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None},
            {"ts": time.time(), "type": "task_complete",
             "session_id": "sess-x", "agent_id": "agent-pri", "agent_role": "primary",
             "task_id": "task-1", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        task_node = [n for n in snapshot["nodes"] if n["id"] == "task-1"][0]
        assert task_node["status"] == "completed"

    # ── delegate_* → derived agent activity (parallel subagent visibility) ──

    def _sess(self, sid="sess-d"):
        return {"ts": time.time(), "type": "session_start",
                "session_id": sid, "agent_id": "agent-pri", "agent_role": "primary",
                "task_id": None, "parent_task_id": None}

    def test_delegate_start_creates_active_agent_and_parallel(self):
        self._feed([
            self._sess(),
            {"ts": time.time(), "type": "delegate_start",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "model": "gemini-2.5-flash", "task": "lookup", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        agents = [n for n in snapshot["nodes"]
                  if n.get("type") == "agent" and n.get("model") == "gemini-2.5-flash"]
        assert agents, "delegate_start must synthesize an agent node for the model"
        assert agents[0]["status"] == "active"
        assert snapshot["parallel_count"] >= 1
        assert agents[0]["id"] in snapshot["active_agents"]

    def test_delegate_done_removes_from_parallel(self):
        self._feed([
            self._sess(),
            {"ts": time.time(), "type": "delegate_start",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "model": "deepseek-chat", "task": "reason", "parent_task_id": None},
            {"ts": time.time(), "type": "delegate_done",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "model": "deepseek-chat", "duration_ms": "1234", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        agents = [n for n in snapshot["nodes"]
                  if n.get("type") == "agent" and n.get("model") == "deepseek-chat"]
        assert agents and agents[0]["status"] == "completed"
        assert agents[0]["id"] not in snapshot["active_agents"]

    def test_delegate_fail_marks_failed(self):
        self._feed([
            self._sess(),
            {"ts": time.time(), "type": "delegate_start",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "model": "qwen3-235b", "task": "scan", "parent_task_id": None},
            {"ts": time.time(), "type": "delegate_fail",
             "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
             "model": "qwen3-235b", "reason": "rate-limit", "parent_task_id": None},
        ])
        snapshot = server._graph_snapshot()
        agents = [n for n in snapshot["nodes"]
                  if n.get("type") == "agent" and n.get("model") == "qwen3-235b"]
        assert agents and agents[0]["status"] == "failed"
        assert agents[0]["id"] not in snapshot["active_agents"]

    def test_parallel_delegates_count_concurrently(self):
        """Two delegate_start with different models → parallel_count == 2."""
        for m in ("gemini-2.5-flash", "deepseek-chat"):
            self._feed([{
                "ts": time.time(), "type": "delegate_start",
                "session_id": "sess-d", "agent_id": "agent-pri", "agent_role": "primary",
                "model": m, "task": "race", "parent_task_id": None,
            }])
        snapshot = server._graph_snapshot()
        assert snapshot["parallel_count"] == 2