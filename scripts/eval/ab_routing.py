#!/usr/bin/env python3
"""
ab_routing.py — A/B model routing core for live subagent comparison (R4).

ARCHITECTURE: time-sliced A/B (NOT per-call).

A PreToolUse hook CANNOT override the Agent tool's model mid-flight — the
model comes from the subagent's frontmatter file. So instead of a racy
per-call 80/20 split, we use TIME-SLICED phases:

  1. ab_rotator.py (CLI or cron) flips the subagent frontmatter `model:`
     field between champion (phase A) and challenger (phase B) every
     `phase_size` invocations.
  2. log_subagent_result.py (PostToolUse hook) tags each `subagent_invoke`
     event with `ab_phase` + `ab_model` (additive, zero-overhead when no
     experiment is active).
  3. subagent_stats.py aggregates pass_rate by ab_phase.
  4. ab_report.py compares the phases and recommends a winner.

This module is the PURE CORE — no I/O except flip_subagent_model (which
writes one frontmatter file) and load_experiments (which reads one JSON).
All routing decisions are pure functions of (experiment, state), making
them trivially testable.

Config: agents/ab-experiments.json (opt-in, active:false default).
State: .tmp/ab-experiment-state.json (gitignored, per-machine).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG = REPO_ROOT / "agents" / "ab-experiments.json"
DEFAULT_STATE = REPO_ROOT / ".tmp" / "ab-experiment-state.json"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
def load_experiments(config_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load the A/B experiment config. Returns [] if missing/invalid.

    Each experiment has:
      subagent, champion, challenger, active (bool),
      phase_size (int), total_phases (int), reason (str)

    Note: config_path defaults to the module-level DEFAULT_CONFIG resolved at
    CALL TIME (not definition time), so monkeypatching DEFAULT_CONFIG in tests
    takes effect.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG
    p = Path(config_path)
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    exps = data.get("experiments", [])
    if not isinstance(exps, list):
        return []
    # Normalize active to bool (lenient parse).
    out = []
    for e in exps:
        if not isinstance(e, dict):
            continue
        e = dict(e)
        e["active"] = bool(e.get("active", False))
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# Phase logic (pure)
# ---------------------------------------------------------------------------
def current_phase(invocations: int, phase_size: int) -> str:
    """Determine the current phase ('A' or 'B') from the invocation count.

    Phase index = invocations // phase_size.
    Even phase index → 'A' (champion); odd → 'B' (challenger).

    Args:
      invocations: total invocations of this subagent since experiment start.
      phase_size: invocations per phase.

    Returns 'A' or 'B'.
    """
    if phase_size <= 0:
        return "A"
    phase_index = invocations // phase_size
    return "A" if phase_index % 2 == 0 else "B"


def model_for_phase(exp: dict[str, Any], phase: str) -> str:
    """Return the model for a given phase ('A'→champion, 'B'→challenger)."""
    return exp["champion"] if phase == "A" else exp["challenger"]


def decide_phase(exp: dict[str, Any], state: dict[str, Any]) -> tuple[str, str]:
    """Pure: given an experiment + state, return (phase, model).

    Reads the invocation count from state[exp.subagent][invocations].
    Falls back to 0 if the subagent has no state yet.
    """
    sa_state = state.get(exp["subagent"], {})
    invocations = sa_state.get("invocations", 0)
    phase = current_phase(invocations, exp.get("phase_size", 20))
    model = model_for_phase(exp, phase)
    return phase, model


def is_complete(exp: dict[str, Any], invocations: int) -> bool:
    """True when invocations have reached phase_size * total_phases."""
    ps = exp.get("phase_size", 20)
    tp = exp.get("total_phases", 4)
    return invocations >= ps * tp


# ---------------------------------------------------------------------------
# State advancement (pure: returns new state, does not write)
# ---------------------------------------------------------------------------
def advance_experiment(
    exp: dict[str, Any],
    state: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Advance one invocation. Returns (action, new_state).

    Actions:
      'kept'      — incremented invocations, stayed in same phase.
      'flipped'   — crossed a phase boundary, phase/model changed.
      'completed' — reached total_phases; experiment done (no more flips).

    The caller (ab_rotator.py) is responsible for writing the frontmatter
    file when action == 'flipped', and persisting new_state to disk.
    """
    sa = exp["subagent"]
    sa_state = dict(state.get(sa, {}))
    invocations = sa_state.get("invocations", 0)
    ps = exp.get("phase_size", 20)
    tp = exp.get("total_phases", 4)

    old_phase = sa_state.get("current_phase")
    old_model = sa_state.get("current_model")

    new_invocations = invocations + 1
    new_phase = current_phase(new_invocations, ps)
    new_model = model_for_phase(exp, new_phase)

    sa_state["invocations"] = new_invocations
    sa_state["current_phase"] = new_phase
    sa_state["current_model"] = new_model

    # Build the new state (shallow copy to avoid mutating input).
    new_state = dict(state)
    new_state[sa] = sa_state

    if is_complete(exp, new_invocations):
        return "completed", new_state
    if new_phase != old_phase or new_model != old_model:
        return "flipped", new_state
    return "kept", new_state


# ---------------------------------------------------------------------------
# Event tagging (used by the PostToolUse hook)
# ---------------------------------------------------------------------------
def tag_for_event(
    subagent: str,
    experiments: list[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, str] | None:
    """Determine the ab_phase + ab_model tag for a subagent_invoke event.

    Returns None if:
      - no active experiment targets this subagent, OR
      - the experiment is inactive, OR
      - state has no current_phase for this subagent.

    This is called by log_subagent_result.py on EVERY subagent_invoke event,
    so it must be cheap and never raise.
    """
    for exp in experiments:
        if exp.get("subagent") != subagent:
            continue
        if not exp.get("active", False):
            return None
        sa_state = state.get(subagent, {})
        phase = sa_state.get("current_phase")
        model = sa_state.get("current_model")
        if phase is None:
            # No state yet — use decide_phase to compute from invocations.
            phase, model = decide_phase(exp, state)
        if phase is None:
            return None
        return {"ab_phase": phase, "ab_model": model or ""}
    return None


# ---------------------------------------------------------------------------
# Frontmatter editing (the ONE I/O function — writes a single .md file)
# ---------------------------------------------------------------------------
# Match `model: <value>` within the YAML frontmatter block (between --- fences).
_FM_MODEL_RE = re.compile(
    r"^(---\s*\n.*?^model:\s*)([^\n]*?)(\s*$.*)",
    re.MULTILINE | re.DOTALL,
)


def flip_subagent_model(subagent_path: Path | str, new_model: str) -> bool:
    """Edit the `model:` field in a subagent's frontmatter. Preserves everything else.

    Returns True if the file was changed, False if no frontmatter/model field found.

    Safe: reads the whole file, replaces only the model value within the
    first --- block, writes atomically. If the file has no frontmatter or no
    model field, it is left untouched.
    """
    p = Path(subagent_path)
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8", errors="replace")

    # Find the frontmatter block (between first pair of --- lines).
    if not text.startswith("---"):
        return False  # no frontmatter — don't touch
    # Locate the closing --- of the frontmatter.
    lines = text.split("\n")
    if len(lines) < 2 or lines[0].strip() != "---":
        return False
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        return False  # unclosed frontmatter — don't touch

    # Find the model: line within the frontmatter.
    model_line_idx = None
    for i in range(1, close_idx):
        if lines[i].startswith("model:"):
            model_line_idx = i
            break
    if model_line_idx is None:
        return False  # no model field — don't touch

    # Preserve indentation + trailing comment if any. Replace just the value.
    old_line = lines[model_line_idx]
    # Format: "model: <value>" possibly with trailing comment after #
    # Split on first '#' to preserve comments.
    if "#" in old_line:
        value_part, _, comment = old_line.partition("#")
        lines[model_line_idx] = f"model: {new_model} #{comment}"
    else:
        lines[model_line_idx] = f"model: {new_model}"

    p.write_text("\n".join(lines), encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# State file I/O (used by ab_rotator.py)
# ---------------------------------------------------------------------------
def load_state(state_path: Path | str | None = None) -> dict[str, Any]:
    """Load the A/B experiment state file. Returns {} if missing/invalid.

    Note: state_path defaults to module-level DEFAULT_STATE resolved at CALL
    TIME, so monkeypatching takes effect (same pattern as load_experiments).
    """
    if state_path is None:
        state_path = DEFAULT_STATE
    p = Path(state_path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_state(state: dict[str, Any], state_path: Path | str = DEFAULT_STATE) -> None:
    """Persist the A/B experiment state file."""
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


__all__ = [
    "load_experiments",
    "current_phase",
    "model_for_phase",
    "decide_phase",
    "is_complete",
    "advance_experiment",
    "tag_for_event",
    "flip_subagent_model",
    "load_state",
    "save_state",
    "DEFAULT_CONFIG",
    "DEFAULT_STATE",
]
