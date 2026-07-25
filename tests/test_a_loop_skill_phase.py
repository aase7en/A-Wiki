"""Tests for scripts/lib/a_loop_skill.py — Phase 4: propose skill from failure.

Iron Law #1: failing tests written FIRST.

a_loop_skill คือ half ที่สองของ A-Loop Phase 3→4 bridge:
  - propose_skill_for_pattern(tag, summary) → DRAFT skill proposal (dict)
  - ไม่ auto-register — ส่ง dict ให้ user/agent พิจารณา
  - เมื่อ user ยืนยัน → call new-skill.py --apply (subprocess)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import a_loop_skill as als  # noqa: E402 -- module under test (created here)


# ---------------------------------------------------------------------------
# 1. propose_skill_for_pattern — builds a skill proposal draft
# ---------------------------------------------------------------------------
def test_propose_returns_dict_with_required_fields():
    proposal = als.propose_skill_for_pattern(
        tag="permission-denied",
        failure_count=3,
        sample_summaries=["perm denied on /tmp", "perm denied writing config"],
    )
    assert isinstance(proposal, dict)
    assert "name" in proposal
    assert "description" in proposal
    assert "domain" in proposal
    assert "phase" in proposal
    assert "rationale" in proposal


def test_propose_name_is_kebab_case():
    """Skill name must be kebab-case (registry validates this)."""
    proposal = als.propose_skill_for_pattern(
        tag="Permission Denied", failure_count=3, sample_summaries=["x"])
    name = proposal["name"]
    assert name == name.lower(), f"name must be lowercase, got {name}"
    assert " " not in name, f"name must not contain spaces: {name}"
    assert name.replace("-", "").replace("_", "").isalnum(), (
        f"name must be alphanumeric+dash: {name}"
    )


def test_propose_includes_rationale_with_evidence():
    """The proposal must show WHY (evidence = failure count + samples)."""
    proposal = als.propose_skill_for_pattern(
        tag="timeout",
        failure_count=5,
        sample_summaries=["api timeout 1", "api timeout 2"],
    )
    rationale = proposal["rationale"]
    assert "5" in rationale, "rationale should mention failure count"
    assert "timeout" in rationale.lower()


# ---------------------------------------------------------------------------
# 2. propose_skill_for_pattern — name avoids collision with existing skills
# ---------------------------------------------------------------------------
def test_propose_name_does_not_collide_with_existing():
    """Proposed name should not duplicate an existing skill name."""
    proposal = als.propose_skill_for_pattern(
        tag="test-failure", failure_count=3, sample_summaries=["x"])
    # Read registry to check
    import json
    reg = json.loads(Path("skills-registry.json").read_text(encoding="utf-8"))
    existing_names = {s["name"] for s in reg.get("skills", [])}
    assert proposal["name"] not in existing_names, (
        f"proposed name {proposal['name']!r} collides with existing skill"
    )


# ---------------------------------------------------------------------------
# 3. apply_proposal — calls new-skill.py (mocked, not real)
# ---------------------------------------------------------------------------
def test_apply_proposal_invokes_new_skill_py(monkeypatch, tmp_path):
    """apply_proposal should shell out to new-skill.py --apply."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class FakeResult:
            returncode = 0
            stdout = "applied: registered"
            stderr = ""
        return FakeResult()

    monkeypatch.setattr(als.subprocess, "run", fake_run)
    proposal = {
        "name": "test-skill-proposal",
        "description": "test",
        "domain": "engineering",
        "phase": "build",
    }
    result = als.apply_proposal(proposal, repo_root=tmp_path)
    assert result is True
    assert len(calls) == 1
    cmd_str = " ".join(calls[0])
    assert "new-skill.py" in cmd_str
    assert "--apply" in cmd_str
    assert "test-skill-proposal" in cmd_str


def test_apply_proposal_returns_false_on_failure(monkeypatch, tmp_path):
    """If new-skill.py fails, apply_proposal returns False (no crash)."""
    def fake_run(cmd, **kwargs):
        class FakeResult:
            returncode = 1
            stdout = ""
            stderr = "validation error"
        return FakeResult()

    monkeypatch.setattr(als.subprocess, "run", fake_run)
    proposal = {"name": "bad", "description": "x", "domain": "engineering", "phase": "build"}
    result = als.apply_proposal(proposal, repo_root=tmp_path)
    assert result is False
