"""
Test that dashboard events contain required IDs for the workflow graph feature.
These tests must FAIL before Step 1 implementation — Iron Law #1.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Force the event logger to write to a temp file
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import event_logger


class TestEventSchema:
    """Verify every logged event has session_id + agent metadata."""

    @pytest.fixture(autouse=True)
    def temp_log(self, monkeypatch, tmp_path):
        """Redirect event_logger to a temp file."""
        log_file = tmp_path / "test-events.jsonl"
        # Override the module-level constants
        monkeypatch.setattr(event_logger, "LOG_FILE", log_file)
        monkeypatch.setattr(event_logger, "MAX_LINES", 500)
        # Ensure session id is fresh per test
        monkeypatch.setattr(event_logger, "_session_id_cache", None)
        return log_file

    def read_events(self, log_file):
        return [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]

    # ── session_id tests ──────────────────────────────────────────

    def test_session_start_has_session_id(self, temp_log):
        """session_start events must include session_id."""
        event_logger.log("session_start")
        events = self.read_events(temp_log)
        assert len(events) == 1
        e = events[0]
        assert "session_id" in e, f"Missing session_id in: {e}"
        assert isinstance(e["session_id"], str)
        assert len(e["session_id"]) > 0

    def test_all_events_share_same_session_id(self, temp_log):
        """Every event within a process shares the same session_id."""
        event_logger.log("session_start")
        event_logger.log("hook_check", hook="check_cost_tier", tool="Edit", result="pass")
        event_logger.log("hook_check", hook="check_raw_immutable", tool="Write", result="pass")
        events = self.read_events(temp_log)
        assert len(events) == 3
        session_ids = {e["session_id"] for e in events}
        assert len(session_ids) == 1, f"Expected 1 session_id, got {len(session_ids)}"

    # ── agent_id / agent_role tests ──────────────────────────────

    def test_event_includes_agent_role(self, temp_log):
        """Every event must carry agent_role."""
        event_logger.log("hook_check", hook="check_cost_tier", tool="Edit", result="pass")
        events = self.read_events(temp_log)
        e = events[0]
        assert "agent_role" in e, f"Missing agent_role in: {e}"
        assert e["agent_role"] in ("primary", "architect", "executioner", "subagent", "unknown")

    def test_event_includes_agent_id(self, temp_log):
        """Every event must carry agent_id."""
        event_logger.log("hook_check", hook="check_cost_tier", tool="Edit", result="pass")
        events = self.read_events(temp_log)
        e = events[0]
        assert "agent_id" in e, f"Missing agent_id in: {e}"
        assert isinstance(e["agent_id"], str)
        assert len(e["agent_id"]) > 0

    def test_primary_agent_role_default(self, temp_log):
        """Without explicit agent_role, default to 'primary'."""
        event_logger.log("hook_check", hook="check_cost_tier", tool="Edit", result="pass")
        events = self.read_events(temp_log)
        assert events[0]["agent_role"] == "primary"

    # ── task_id tests ─────────────────────────────────────────────

    def test_event_includes_task_id(self, temp_log):
        """Every event must carry a task_id (can be null for session-level)."""
        event_logger.log("session_start")
        events = self.read_events(temp_log)
        e = events[0]
        assert "task_id" in e, f"Missing task_id in: {e}"
        # session_start may have null task_id
        assert e["task_id"] is None or isinstance(e["task_id"], str)

    def test_parent_task_id_field_exists(self, temp_log):
        """Every event must carry parent_task_id field (can be null)."""
        event_logger.log("hook_check", hook="check_cost_tier", tool="Edit", result="pass")
        events = self.read_events(temp_log)
        e = events[0]
        assert "parent_task_id" in e, f"Missing parent_task_id in: {e}"
        assert e["parent_task_id"] is None or isinstance(e["parent_task_id"], str)

    # ── backward compatibility ────────────────────────────────────

    def test_existing_fields_preserved(self, temp_log):
        """ts, type, and arbitrary kwargs still work."""
        event_logger.log("delegate_start", model="gemini-2.5-flash", task="lookup")
        events = self.read_events(temp_log)
        e = events[0]
        assert e["type"] == "delegate_start"
        assert "ts" in e
        assert e["model"] == "gemini-2.5-flash"
        assert e["task"] == "lookup"
        # New fields also present
        assert "session_id" in e
        assert "agent_id" in e
        assert "agent_role" in e

    # ── agent_spawn event type ────────────────────────────────────

    def test_agent_spawn_event(self, temp_log):
        """agent_spawn must carry agent_role for the spawned agent."""
        event_logger.log("agent_spawn", agent_role="architect", model="deepseek-v4-flash:free")
        events = self.read_events(temp_log)
        e = events[0]
        assert e["type"] == "agent_spawn"
        assert e["agent_role"] == "architect"
        assert e["model"] == "deepseek-v4-flash:free"