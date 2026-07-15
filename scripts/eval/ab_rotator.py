#!/usr/bin/env python3
"""
ab_rotator.py — CLI for advancing/flipping A/B experiment phases (R4).

The rotator is the "clock" of the time-sliced A/B system. It:
  1. Bumps the invocation count for an experiment.
  2. When the count crosses a phase boundary (every `phase_size` calls),
     flips the subagent frontmatter `model:` field to the new phase's model.
  3. Persists state to .tmp/ab-experiment-state.json.

Typically driven by:
  - Manual: `python scripts/eval/ab_rotator.py --advance <subagent>`
  - Cron/timer: `python scripts/eval/ab_rotator.py --advance-all` (every N min)

The PostToolUse hook (log_subagent_result.py) does NOT advance state itself
(keeps the hot path cheap); it only READS state to tag events. A separate
 lightweight process (this CLI, or a hook on session-end) advances counts.

Usage:
  python scripts/eval/ab_rotator.py --list
  python scripts/eval/ab_rotator.py --advance clinical-reasoner
  python scripts/eval/ab_rotator.py --advance-all          # advance all active
  python scripts/eval/ab_rotator.py --apply clinical-reasoner   # force-flip now
  python scripts/eval/ab_rotator.py --reset clinical-reasoner   # restart experiment
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

import ab_routing  # noqa: E402


def _subagent_path(subagent: str) -> Path | None:
    """Find the frontmatter .md file for a subagent name."""
    candidates = [
        REPO_ROOT / "agents" / "subagents" / f"{subagent}.md",
        REPO_ROOT / "agents" / f"{subagent}.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def cmd_list(experiments, state) -> int:
    if not experiments:
        print("No A/B experiments configured.")
        print(f"  Config: {ab_routing.DEFAULT_CONFIG}")
        return 0
    print(f"A/B Experiments ({len(experiments)}):")
    for exp in experiments:
        sa = exp["subagent"]
        sa_state = state.get(sa, {})
        inv = sa_state.get("invocations", 0)
        phase = sa_state.get("current_phase", "(none)")
        model = sa_state.get("current_model", "(none)")
        ps = exp.get("phase_size", 20)
        tp = exp.get("total_phases", 4)
        target = ps * tp
        active = "🟢" if exp.get("active") else "⚪"
        complete = "✅" if ab_routing.is_complete(exp, inv) else "⏳"
        print(f"  {active} {complete} {sa:<28} {exp['champion']}↔{exp['challenger']}")
        print(f"       invocations: {inv}/{target}  phase: {phase}  model: {model}")
    return 0


def cmd_advance(subagent: str, experiments, state, config_path) -> int:
    exp = next((e for e in experiments if e["subagent"] == subagent), None)
    if exp is None:
        print(f"❌ No experiment for '{subagent}'", file=sys.stderr)
        return 1
    if not exp.get("active", False):
        print(f"⚪ Experiment for '{subagent}' is inactive. Activate it in {config_path} first.")
        return 0

    action, new_state = ab_routing.advance_experiment(exp, state)
    ab_routing.save_state(new_state)

    sa_state = new_state[subagent]
    print(f"advanced '{subagent}': {action}")
    print(f"  invocations: {sa_state['invocations']}  phase: {sa_state['current_phase']}  model: {sa_state['current_model']}")

    if action == "flipped":
        sa_path = _subagent_path(subagent)
        if sa_path is None:
            print(f"  ⚠️  subagent .md not found for '{subagent}' — frontmatter not flipped.")
        else:
            changed = ab_routing.flip_subagent_model(sa_path, sa_state["current_model"])
            if changed:
                print(f"  ✓ flipped {sa_path.name} model → {sa_state['current_model']}")
            else:
                print(f"  ⚠️  could not flip {sa_path.name} (no model field in frontmatter?)")
    elif action == "completed":
        print(f"  ✅ experiment complete! Run: python scripts/eval/ab_report.py --subagent {subagent} --recommend")
    return 0


def cmd_advance_all(experiments, state, config_path) -> int:
    active = [e for e in experiments if e.get("active", False)]
    if not active:
        print("No active experiments.")
        return 0
    for exp in active:
        cmd_advance(exp["subagent"], experiments, state, config_path)
        # Re-read state after each advance (it was saved).
        state = ab_routing.load_state()
    return 0


def cmd_apply(subagent: str, experiments, state) -> int:
    """Force-flip to the current phase's model immediately (no invocation bump)."""
    exp = next((e for e in experiments if e["subagent"] == subagent), None)
    if exp is None:
        print(f"❌ No experiment for '{subagent}'", file=sys.stderr)
        return 1
    phase, model = ab_routing.decide_phase(exp, state)
    sa_path = _subagent_path(subagent)
    if sa_path is None:
        print(f"❌ subagent .md not found for '{subagent}'", file=sys.stderr)
        return 1
    changed = ab_routing.flip_subagent_model(sa_path, model)
    if changed:
        print(f"✓ applied {sa_path.name} model → {model} (phase {phase})")
    else:
        print(f"⚠️  could not flip {sa_path.name}")
    return 0


def cmd_reset(subagent: str, experiments, state) -> int:
    """Reset an experiment's state (restart from invocation 0, phase A)."""
    exp = next((e for e in experiments if e["subagent"] == subagent), None)
    if exp is None:
        print(f"❌ No experiment for '{subagent}'", file=sys.stderr)
        return 1
    new_state = dict(state)
    new_state[subagent] = {"invocations": 0, "current_phase": "A", "current_model": exp["champion"]}
    ab_routing.save_state(new_state)
    # Also flip frontmatter back to champion.
    sa_path = _subagent_path(subagent)
    if sa_path:
        ab_routing.flip_subagent_model(sa_path, exp["champion"])
    print(f"✓ reset '{subagent}' → invocations=0, phase=A, model={exp['champion']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list all experiments + status")
    g.add_argument("--advance", metavar="SUBAGENT", help="advance one experiment by 1 invocation")
    g.add_argument("--advance-all", action="store_true", help="advance all active experiments")
    g.add_argument("--apply", metavar="SUBAGENT", help="force-flip to current phase model now")
    g.add_argument("--reset", metavar="SUBAGENT", help="reset an experiment (restart)")
    p.add_argument("--config", default=str(ab_routing.DEFAULT_CONFIG))
    args = p.parse_args()

    experiments = ab_routing.load_experiments(args.config)
    state = ab_routing.load_state()

    if args.list:
        return cmd_list(experiments, state)
    if args.advance:
        return cmd_advance(args.advance, experiments, state, args.config)
    if args.advance_all:
        return cmd_advance_all(experiments, state, args.config)
    if args.apply:
        return cmd_apply(args.apply, experiments, state)
    if args.reset:
        return cmd_reset(args.reset, experiments, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
