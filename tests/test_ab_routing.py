"""Tests for scripts/eval/ab_routing.py — A/B model routing core (R4).

Iron Law #1: failing tests written FIRST. These pin the contract of the
pure routing functions before any implementation exists.

Architecture: time-sliced A/B (NOT per-call). A rotator flips the
subagent frontmatter model between champion (phase A) and challenger
(phase B) every `phase_size` invocations. The PostToolUse hook tags
each event with the current phase. This avoids racy per-call model
overrides (which the PreToolUse hook cannot do anyway — model comes
from frontmatter).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import ab_routing  # noqa: E402  -- module under test (created by R4)


# ---------------------------------------------------------------------------
# Sample experiment
# ---------------------------------------------------------------------------
EXP = {
    "subagent": "clinical-reasoner",
    "champion": "deepseek-v4-pro",
    "challenger": "glm-5.2",
    "active": True,
    "phase_size": 20,
    "total_phases": 4,
    "reason": "compare DeepSeek reasoning vs GLM on clinical tasks",
}


# ---------------------------------------------------------------------------
# 1. current_phase alternates every phase_size invocations
# ---------------------------------------------------------------------------
def test_current_phase_alternates_every_phase_size():
    """Phases alternate A, B, A, B as invocations cross phase_size boundaries."""
    ps = 20
    assert ab_routing.current_phase(0, ps) == "A"
    assert ab_routing.current_phase(19, ps) == "A"   # last of phase 0 (A)
    assert ab_routing.current_phase(20, ps) == "B"   # first of phase 1 (B)
    assert ab_routing.current_phase(39, ps) == "B"   # last of phase 1 (B)
    assert ab_routing.current_phase(40, ps) == "A"   # phase 2 (A)
    assert ab_routing.current_phase(60, ps) == "B"   # phase 3 (B)


# ---------------------------------------------------------------------------
# 2. model_for_phase returns the right model
# ---------------------------------------------------------------------------
def test_model_for_phase_returns_correct_model():
    exp = EXP
    assert ab_routing.model_for_phase(exp, "A") == "deepseek-v4-pro"
    assert ab_routing.model_for_phase(exp, "B") == "glm-5.2"


# ---------------------------------------------------------------------------
# 3. decide_phase — pure: count invocations, return phase + model
# ---------------------------------------------------------------------------
def test_decide_phase_returns_phase_and_model():
    """Given an experiment + state with invocation count, decide the phase."""
    state = {"clinical-reasoner": {"invocations": 5}}
    phase, model = ab_routing.decide_phase(EXP, state)
    assert phase == "A"
    assert model == "deepseek-v4-pro"

    state2 = {"clinical-reasoner": {"invocations": 25}}
    phase2, model2 = ab_routing.decide_phase(EXP, state2)
    assert phase2 == "B"
    assert model2 == "glm-5.2"


# ---------------------------------------------------------------------------
# 4. advance_experiment — keeps within phase (no flip yet)
# ---------------------------------------------------------------------------
def test_advance_keeps_within_phase():
    state = {"clinical-reasoner": {"invocations": 5, "current_phase": "A", "current_model": "deepseek-v4-pro"}}
    action, new_state = ab_routing.advance_experiment(EXP, state)
    assert action == "kept"
    assert new_state["clinical-reasoner"]["invocations"] == 6
    assert new_state["clinical-reasoner"]["current_phase"] == "A"


# ---------------------------------------------------------------------------
# 5. advance_experiment — flips at boundary
# ---------------------------------------------------------------------------
def test_advance_flips_at_boundary():
    """At invocation 19→20, phase should flip A→B."""
    state = {"clinical-reasoner": {"invocations": 19, "current_phase": "A", "current_model": "deepseek-v4-pro"}}
    action, new_state = ab_routing.advance_experiment(EXP, state)
    assert action == "flipped"
    assert new_state["clinical-reasoner"]["invocations"] == 20
    assert new_state["clinical-reasoner"]["current_phase"] == "B"
    assert new_state["clinical-reasoner"]["current_model"] == "glm-5.2"


# ---------------------------------------------------------------------------
# 6. advance_experiment — completes at total_phases
# ---------------------------------------------------------------------------
def test_advance_completes_at_total_phases():
    """When invocations reach phase_size * total_phases, the experiment completes."""
    # total_phases=4, phase_size=20 → completes at 80 invocations
    state = {"clinical-reasoner": {"invocations": 79, "current_phase": "B", "current_model": "glm-5.2"}}
    action, new_state = ab_routing.advance_experiment(EXP, state)
    assert action == "completed"
    assert new_state["clinical-reasoner"]["invocations"] == 80


# ---------------------------------------------------------------------------
# 7. flip_subagent_model — preserves frontmatter
# ---------------------------------------------------------------------------
def test_flip_subagent_model_preserves_frontmatter(tmp_path):
    """Editing the model field must preserve all other frontmatter + body."""
    sa_file = tmp_path / "test-agent.md"
    original = """---
name: test-agent
description: A test agent
tools: Read, Write
model: deepseek-v4-flash
color: blue
custom_field: value
---

# Test Agent Body

This is the agent body. It should be preserved.
"""
    sa_file.write_text(original, encoding="utf-8")
    ab_routing.flip_subagent_model(sa_file, "glm-5.2")
    result = sa_file.read_text(encoding="utf-8")
    # Model changed
    assert "model: glm-5.2" in result
    assert "model: deepseek-v4-flash" not in result
    # Other frontmatter preserved
    assert "name: test-agent" in result
    assert "description: A test agent" in result
    assert "tools: Read, Write" in result
    assert "color: blue" in result
    assert "custom_field: value" in result
    # Body preserved
    assert "# Test Agent Body" in result
    assert "This is the agent body." in result


# ---------------------------------------------------------------------------
# 8. flip_subagent_model — no frontmatter → no-op (safe)
# ---------------------------------------------------------------------------
def test_flip_subagent_model_no_frontmatter_is_safe(tmp_path):
    """A file without frontmatter should not be corrupted."""
    sa_file = tmp_path / "no-fm.md"
    sa_file.write_text("Just a body, no frontmatter here.", encoding="utf-8")
    # Should not raise; may no-op.
    ab_routing.flip_subagent_model(sa_file, "glm-5.2")
    result = sa_file.read_text(encoding="utf-8")
    assert "Just a body" in result


# ---------------------------------------------------------------------------
# 9. load_experiments — reads config
# ---------------------------------------------------------------------------
def test_load_experiments_reads_config(tmp_path):
    config = {"experiments": [EXP, {**EXP, "subagent": "other-agent", "active": False}]}
    cfg_path = tmp_path / "ab-experiments.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    exps = ab_routing.load_experiments(cfg_path)
    assert len(exps) == 2
    assert exps[0]["subagent"] == "clinical-reasoner"
    assert exps[0]["active"] is True
    assert exps[1]["active"] is False


# ---------------------------------------------------------------------------
# 10. load_experiments — missing file → empty list (no crash)
# ---------------------------------------------------------------------------
def test_load_experiments_missing_file_returns_empty(tmp_path):
    exps = ab_routing.load_experiments(tmp_path / "nope.json")
    assert exps == []


# ---------------------------------------------------------------------------
# 11. tag_for_event — determines ab_phase tag for a subagent_invoke event
# ---------------------------------------------------------------------------
def test_tag_for_event_returns_phase_when_active():
    """Given state + subagent, return the ab_phase tag (or None if no experiment)."""
    state = {"clinical-reasoner": {"current_phase": "B", "current_model": "glm-5.2"}}
    experiments = [EXP]
    tag = ab_routing.tag_for_event("clinical-reasoner", experiments, state)
    assert tag == {"ab_phase": "B", "ab_model": "glm-5.2"}


def test_tag_for_event_returns_none_when_no_experiment():
    """A subagent with no active experiment → None (zero overhead)."""
    state = {}
    experiments = [EXP]  # only clinical-reasoner
    tag = ab_routing.tag_for_event("some-other-agent", experiments, state)
    assert tag is None


def test_tag_for_event_returns_none_for_inactive_experiment():
    """An inactive experiment → None (no tagging)."""
    exp = {**EXP, "active": False}
    state = {"clinical-reasoner": {"current_phase": "A"}}
    tag = ab_routing.tag_for_event("clinical-reasoner", [exp], state)
    assert tag is None
