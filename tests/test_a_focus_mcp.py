"""Tests for the MCP focus_* and skill_route tools (A-Suite C4).

These tools are the cross-agent parity substrate: a hook can only serve Claude
Code, but any MCP-aware agent (Codex, ZCode, Gemini, Claude) can call these.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import neural_spine_mcp as ns  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_focus(tmp_path, monkeypatch):
    """Point focus state at a temp dir so tests never touch the real .tmp/.

    ADR-0012 slice A4 added a path-traversal sandbox guard that rejects paths
    outside AWIKI_DATA_DIR (default ``.tmp/``). pytest's ``tmp_path`` lives
    under the OS temp dir, so broaden the sandbox to include it. Restore the
    default sandbox BEFORE resetting focus_dir, because set_paths() itself
    validates against AWIKI_DATA_DIR and monkeypatch hasn't undone the env
    change yet at teardown time.
    """
    monkeypatch.setenv("AWIKI_DATA_DIR", str(tmp_path))
    ns.set_paths(focus_dir=tmp_path)
    yield tmp_path
    # Undo the env broadening first so the repo-root .tmp is back in-sandbox.
    monkeypatch.delenv("AWIKI_DATA_DIR", raising=False)
    ns.set_paths(focus_dir=REPO_ROOT / ".tmp")


class TestFocusLifecycle:
    def test_get_returns_none_when_no_focus_is_set(self):
        assert ns.tool_focus_get({}) is None

    def test_set_starts_at_the_first_phase_by_default(self):
        st = ns.tool_focus_set({"skill": "a-plan", "goal": "design the dashboard"})
        assert st["skill"] == "a-plan"
        assert st["goal"] == "design the dashboard"
        assert st["phase"] == "ask"
        assert st["phases_done"] == []

    def test_set_accepts_an_explicit_starting_phase(self):
        st = ns.tool_focus_set({"skill": "a-debug", "goal": "500s", "phase": "debug"})
        assert st["phase"] == "debug"

    def test_set_rejects_an_unknown_phase(self):
        with pytest.raises(ValueError):
            ns.tool_focus_set({"skill": "a-plan", "goal": "x", "phase": "deploy"})

    def test_set_requires_a_skill(self):
        with pytest.raises((KeyError, ValueError)):
            ns.tool_focus_set({"goal": "x"})

    def test_get_reads_back_what_set_wrote(self):
        ns.tool_focus_set({"skill": "a-doc", "goal": "ประกาศ"})
        st = ns.tool_focus_get({})
        assert st["skill"] == "a-doc"
        assert st["goal"] == "ประกาศ"

    def test_advance_walks_the_chain_and_records_history(self):
        ns.tool_focus_set({"skill": "a-plan", "goal": "x"})
        st = ns.tool_focus_advance({})
        assert st["phase"] == "design"
        assert st["phases_done"] == ["ask"]
        st = ns.tool_focus_advance({})
        assert st["phase"] == "plan"
        assert st["phases_done"] == ["ask", "design"]

    def test_advance_at_the_end_of_the_chain_completes_the_focus(self):
        ns.tool_focus_set({"skill": "a-debug", "goal": "x", "phase": "test"})
        st = ns.tool_focus_advance({})
        assert st["phase"] is None or st.get("complete") is True
        assert "test" in st["phases_done"]

    def test_advance_without_a_focus_raises(self):
        with pytest.raises(ValueError):
            ns.tool_focus_advance({})

    def test_clear_removes_the_state(self):
        ns.tool_focus_set({"skill": "a-plan", "goal": "x"})
        ns.tool_focus_clear({})
        assert ns.tool_focus_get({}) is None

    def test_clear_is_idempotent(self):
        ns.tool_focus_clear({})
        ns.tool_focus_clear({})   # must not raise

    def test_state_survives_a_module_reload(self, isolated_focus):
        """Focus is on disk, not in memory — it must outlive the process."""
        ns.tool_focus_set({"skill": "a-plan", "goal": "persist me"})
        import importlib
        reloaded = importlib.reload(ns)
        reloaded.set_paths(focus_dir=isolated_focus)
        assert reloaded.tool_focus_get({})["goal"] == "persist me"


class TestSkillRoute:
    def test_routes_a_thai_prompt(self):
        hits = ns.tool_skill_route({"text": "ช่วยแก้บั๊ก dashboard หน่อย"})
        assert hits and hits[0]["skill"] == "a-debug"

    def test_routes_an_english_prompt(self):
        hits = ns.tool_skill_route({"text": "help me design the architecture"})
        assert hits and hits[0]["skill"] == "a-plan"

    def test_returns_empty_for_an_unrelated_prompt(self):
        assert ns.tool_skill_route({"text": "สวัสดีครับ"}) == []

    def test_result_carries_the_invocation_hint_so_a_caller_can_act(self):
        hits = ns.tool_skill_route({"text": "ช่วยแก้บั๊กหน่อย"})
        assert hits[0]["invocation_hint"]
        assert hits[0]["score"] > 0

    def test_respects_limit(self):
        hits = ns.tool_skill_route({"text": "error crash design architecture", "limit": 1})
        assert len(hits) <= 1

    def test_missing_text_returns_empty_rather_than_raising(self):
        assert ns.tool_skill_route({}) == []


class TestToolsRegistration:
    @pytest.mark.parametrize(
        "name",
        ["skill_route", "focus_set", "focus_get", "focus_advance", "focus_clear"],
    )
    def test_tool_is_registered_with_a_schema(self, name):
        assert name in ns.TOOLS, f"{name} missing from neural_spine_mcp.TOOLS"
        spec = ns.TOOLS[name]
        assert callable(spec["fn"])
        assert spec.get("description")
        assert spec.get("inputSchema", {}).get("type") == "object"

    def test_tools_actually_reach_the_awiki_mcp_server(self):
        """The server merges our TOOLS inside a bare try/except.

        scripts/mcp-wiki-server.py does:

            try:
                import neural_spine_mcp as _ns
                TOOLS.update(_ns.TOOLS)
            except Exception as _e:
                sys.stderr.write(...)

        so ANY error in this module — a syntax error, a bad import — silently
        drops every neural-spine tool from the server with no failure anywhere.
        This assertion is the only thing that catches that.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_awiki_mcp_server_under_test", REPO_ROOT / "scripts" / "mcp-wiki-server.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in ("skill_route", "focus_set", "focus_get", "wiki_search"):
            assert name in mod.TOOLS, (
                f"{name} did not reach the MCP server's TOOLS — the neural-spine "
                f"merge in mcp-wiki-server.py probably swallowed an exception"
            )
