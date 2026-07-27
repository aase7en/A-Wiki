"""Tests for scripts/lib/agent_claims.py — mandatory cross-agent work claims.

Why this exists: on 2026-07-27 two agents (Claude and ZCode) independently built
the same intent-router and the same phase state machine, in the same repo, on the
same branch, during the same hours. Neither noticed until both had landed on main.

A-Wiki already had every primitive needed to prevent that — a TaskBoard with TTL
leases, a Blackboard with @mentions, a shared .tmp/. What it lacked was a GATE:
nothing forced an agent to declare what it was about to build. These tests pin
down the gate.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import agent_claims as ac  # noqa: E402


@pytest.fixture(autouse=True)
def isolated(tmp_path):
    ac.set_store(tmp_path / "agent-claims.json")
    yield
    ac.set_store(None)


class TestAcquire:
    def test_acquire_returns_a_claim_with_an_id(self):
        c = ac.acquire(agent="claude", scope=["skills/awiki/**"], goal="build a-router")
        assert c["id"] and c["agent"] == "claude" and c["phase"] == "ask"

    def test_acquire_records_scope_and_goal(self):
        c = ac.acquire(agent="zcode", scope=["scripts/lib/**"], goal="a-flow state")
        assert c["scope"] == ["scripts/lib/**"] and c["goal"] == "a-flow state"

    def test_acquire_sets_a_lease_in_the_future(self):
        c = ac.acquire(agent="claude", scope=["a/**"], goal="g")
        assert c["lease_until"] > time.time()

    def test_acquire_requires_agent_scope_and_goal(self):
        for kwargs in ({"agent": "", "scope": ["a"], "goal": "g"},
                       {"agent": "a", "scope": [], "goal": "g"},
                       {"agent": "a", "scope": ["a"], "goal": ""}):
            with pytest.raises(ValueError):
                ac.acquire(**kwargs)

    def test_two_agents_can_hold_non_overlapping_claims(self):
        ac.acquire(agent="claude", scope=["skills/**"], goal="A")
        ac.acquire(agent="zcode", scope=["docs/**"], goal="B")
        assert len(ac.live()) == 2


class TestCollision:
    def test_detects_another_agents_claim_on_the_same_path(self):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="a-flow")
        hit = ac.collision("skills/awiki/a-router/SKILL.md", agent="claude")
        assert hit and hit["agent"] == "zcode" and hit["goal"] == "a-flow"

    def test_my_own_claim_is_never_a_collision(self):
        ac.acquire(agent="claude", scope=["skills/awiki/**"], goal="mine")
        assert ac.collision("skills/awiki/x/SKILL.md", agent="claude") is None

    def test_unrelated_path_is_not_a_collision(self):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="a-flow")
        assert ac.collision("docs/readme.md", agent="claude") is None

    def test_exact_file_scope_matches(self):
        ac.acquire(agent="zcode", scope=["skills-registry.json"], goal="registry")
        assert ac.collision("skills-registry.json", agent="claude")

    def test_windows_backslash_paths_are_normalised(self):
        """Hooks receive Windows paths; a claim must still match."""
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="a-flow")
        assert ac.collision(r"skills\awiki\a-router\SKILL.md", agent="claude")

    def test_absolute_paths_inside_the_repo_are_matched(self):
        ac.acquire(agent="zcode", scope=["skills/awiki/**"], goal="a-flow")
        abs_path = str(REPO_ROOT / "skills" / "awiki" / "a-router" / "SKILL.md")
        assert ac.collision(abs_path, agent="claude")

    def test_expired_claims_do_not_collide(self):
        c = ac.acquire(agent="zcode", scope=["skills/**"], goal="stale")
        ac._force_lease(c["id"], time.time() - 1)
        assert ac.collision("skills/x.md", agent="claude") is None


class TestLifecycle:
    def test_release_removes_the_claim(self):
        c = ac.acquire(agent="claude", scope=["a/**"], goal="g")
        assert ac.release(c["id"]) is True
        assert ac.live() == []

    def test_release_is_idempotent(self):
        assert ac.release("nope") is False

    def test_advance_updates_the_phase(self):
        c = ac.acquire(agent="claude", scope=["a/**"], goal="g")
        got = ac.advance(c["id"], "implement")
        assert got["phase"] == "implement"

    def test_advance_rejects_an_unknown_phase(self):
        c = ac.acquire(agent="claude", scope=["a/**"], goal="g")
        with pytest.raises(ValueError):
            ac.advance(c["id"], "deploy")

    def test_heartbeat_extends_the_lease(self):
        c = ac.acquire(agent="claude", scope=["a/**"], goal="g")
        ac._force_lease(c["id"], time.time() + 5)
        before = ac.get(c["id"])["lease_until"]
        after = ac.heartbeat(c["id"])["lease_until"]
        assert after > before

    def test_live_excludes_expired_and_reaps_them(self):
        c = ac.acquire(agent="zcode", scope=["a/**"], goal="stale")
        ac._force_lease(c["id"], time.time() - 1)
        assert ac.live() == []
        assert ac.get(c["id"]) is None, "expired claim should be reaped from the store"

    def test_release_all_for_a_session_clears_only_that_session(self):
        c1 = ac.acquire(agent="claude", scope=["a/**"], goal="g", session_id="s1")
        ac.acquire(agent="zcode", scope=["b/**"], goal="h", session_id="s2")
        n = ac.release_session("s1")
        assert n == 1
        ids = {x["id"] for x in ac.live()}
        assert c1["id"] not in ids and len(ids) == 1


class TestDurability:
    def test_state_survives_a_reload(self, tmp_path):
        ac.acquire(agent="claude", scope=["a/**"], goal="persist")
        import importlib
        re_ac = importlib.reload(ac)
        re_ac.set_store(tmp_path / "agent-claims.json")
        assert len(re_ac.live()) == 1

    def test_corrupt_store_fails_open_rather_than_wedging_the_repo(self, tmp_path):
        (tmp_path / "agent-claims.json").write_text("{not json", encoding="utf-8")
        assert ac.live() == []
        assert ac.collision("any/path.py", agent="claude") is None

    def test_writes_are_atomic(self, tmp_path):
        """Adopted from ZCode's a_flow_state.py — temp file + os.replace.

        A half-written claim store would be indistinguishable from 'no claims',
        which silently disables the gate for everyone.
        """
        import inspect
        src = inspect.getsource(ac._write)
        assert "os.replace" in src or "Path.replace" in src
