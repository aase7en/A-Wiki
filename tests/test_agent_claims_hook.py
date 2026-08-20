"""Tests for check_agent_claim.py — the mandatory cross-agent collision gate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_agent_claim.py"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
import agent_claims as ac  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    p = tmp_path / "agent-claims.json"
    ac.set_store(p)
    yield p
    ac.set_store(None)


def run(payload: dict, store_path: Path, agent: str, env_extra=None):
    env = dict(os.environ)
    for k in ("HOOK_SKIP", "AWIKI_CLAIM_GATE", "ZCODE_SESSION_ID",
              "CLAUDE_SESSION_ID", "CODEX_SESSION_ID", "GEMINI_SESSION_ID"):
        env.pop(k, None)
    env["AWIKI_AGENT"] = agent
    env["AWIKI_CLAIMS_STORE"] = str(store_path)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


EDIT = {"tool_name": "Edit", "tool_input": {"file_path": "skills/awiki/a-router/SKILL.md"}}


class TestCollisionBlocks:
    def test_blocks_when_another_agent_holds_the_scope(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="a-flow router")
        r = run(EDIT, store, agent="claude")
        assert r.returncode == 2, "collision must be a hard block"
        assert "zcode" in r.stderr and "a-flow router" in r.stderr

    def test_block_message_names_the_phase_and_the_way_to_coordinate(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="g", phase="implement")
        r = run(EDIT, store, agent="claude")
        assert "implement" in r.stderr
        assert "bb_post" in r.stderr and "claim_list" in r.stderr

    def test_my_own_claim_does_not_block_me(self, store):
        ac.acquire(agent="claude", scope=["skills/awiki/**"], goal="mine")
        assert run(EDIT, store, agent="claude").returncode == 0

    def test_unrelated_path_is_not_blocked(self, store):
        ac.acquire(agent="zcode", scope=["docs/**"], goal="docs work")
        assert run(EDIT, store, agent="claude").returncode == 0


class TestUnclaimedIsOnlyAWarning:
    def test_shared_surface_without_a_claim_warns_but_passes(self, store):
        r = run(EDIT, store, agent="claude")
        assert r.returncode == 0, "must not deadlock the tool needed to claim"
        assert "claim_acquire" in r.stderr

    def test_non_shared_surface_is_silent(self, store):
        r = run({"tool_name": "Write", "tool_input": {"file_path": "notes/scratch.txt"}},
                store, agent="claude")
        assert r.returncode == 0 and r.stderr.strip() == ""


class TestFailOpen:
    def test_non_write_tools_ignored(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="g")
        for tool in ("Read", "Grep", "Bash", "Glob"):
            assert run({"tool_name": tool, "tool_input": {}}, store, agent="claude").returncode == 0

    def test_gate_disabled_by_env(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="g")
        assert run(EDIT, store, agent="claude", env_extra={"AWIKI_CLAIM_GATE": "0"}).returncode == 0

    def test_hook_skip_bypasses(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="g")
        r = run(EDIT, store, agent="claude", env_extra={"HOOK_SKIP": "check_agent_claim"})
        assert r.returncode == 0

    def test_corrupt_store_fails_open(self, store):
        store.write_text("{broken", encoding="utf-8")
        assert run(EDIT, store, agent="claude").returncode == 0

    def test_malformed_stdin_exits_zero(self, store):
        env = dict(os.environ); env["AWIKI_CLAIMS_STORE"] = str(store)
        r = subprocess.run([sys.executable, str(HOOK)], input="not json",
                           capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30, env=env)
        assert r.returncode == 0

    def test_thai_block_message_survives_cp874(self, store):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="งานภาษาไทย")
        r = run(EDIT, store, agent="claude", env_extra={"PYTHONIOENCODING": "cp874"})
        assert r.returncode == 2
        assert "Traceback" not in r.stderr


class TestConsistency:
    def test_phases_match_the_a_suite_spine(self):
        """agent_claims duplicates the phase list as a literal for import cost —
        this is the drift guard that keeps the two in sync."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from skills_registry import routing
        assert ac.PHASES == routing.A_PHASE_CHAIN

    def test_wired_into_pretooluse_for_claude_and_codex(self):
        for cfg_path in (".claude/settings.json", ".codex/hooks.json"):
            cfg = json.loads((REPO_ROOT / cfg_path).read_text(encoding="utf-8"))
            blob = json.dumps(cfg)
            if "check-agent-claim" not in blob and "check_agent_claim" not in blob:
                # Phase 6 sweep form: registry-driven dispatch — the hook runs
                # if the config has a PreToolUse event sweep AND the registry
                # declares it for the Edit-family matcher.
                import sys as _sys
                _sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
                import registry as _reg
                entry = _reg.HOOK_REGISTRY.get("check_agent_claim")
                sweep = "--event PreToolUse" in blob
                assert sweep and entry and "Edit|Write|MultiEdit" in entry["matchers"], (
                    f"check_agent_claim neither named nor sweep-dispatched in {cfg_path}")
