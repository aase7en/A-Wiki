#!/usr/bin/env python3
"""registry.py — THE hook registration/classification authority (Phase 6).

One explicit registry for every executable hook the canonical lifecycle
runner (scripts/hooks_runner.py) may dispatch. Filename layout is a
compatibility hint, NEVER a security authority: a script that is not
registered here cannot be executed through the runner, and an intended
hard gate can never silently become soft because this module fails to
load — the runner fails CLOSED when the registry is unavailable/invalid.

Schema per entry (name → policy):
    events               lifecycle event(s) the hook is registered for
    classification       "hard" (enforcement; fail-closed) | "soft" (observe)
    order                deterministic execution priority (unique int)
    timeout_s            per-hook timeout override (None → runner default)
    allow_context_stdout may emit contextual stdout to the provider

Classifications are EVIDENCE-BASED from each hook's own contract:
  - hard  = every hook with an enforcement exit(2) path
  - soft  = hooks self-documented as warn/observe-only
    (check_subagent_fanout: "WARN-ONLY ... Never blocks";
     check_git_rebase_safety: "never block — warn + backup only";
     memory_capture: "ALWAYS" exit 0; Stop advisors per AGENTS.md)

CLI:  python scripts/hooks/registry.py --check   (CI: exit 1 on any error)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# Lifecycle events that ACTUALLY exist in provider wiring today.
# (.claude/settings.json + scripts/setup-codex-config.py HOOKS_CONFIG.)
# PreCompact is not wired anywhere — it must not appear here.
KNOWN_EVENTS = (
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "PostCompact",
)

CLASSIFICATIONS = ("hard", "soft")


class RegistryError(Exception):
    """Registry invalid/unavailable — callers must fail CLOSED."""


def _e(events, classification, order, *, timeout_s=None, context=False):
    return {"events": list(events), "classification": classification,
            "order": order, "timeout_s": timeout_s,
            "allow_context_stdout": context}


# ── THE authority ────────────────────────────────────────────────────────
# Preserve hook IDs in an ordered pre-lookup sequence so duplicate stable IDs
# remain observable to validation instead of being silently collapsed by dict.
HOOK_SPECS: tuple[tuple[str, dict], ...] = (
    # SessionStart — passive environment/link health (soft, warn-only)
    ("check_drive_link", _e(["SessionStart"], "soft", 5)),

    # UserPromptSubmit (Claude-only event; Codex cannot support it —
    # truthful provider limitation, see scripts/hooks/providers.py)
    ("check_compaction_suggest", _e(["UserPromptSubmit"], "soft", 10, context=True)),
    ("check_a_route",            _e(["UserPromptSubmit"], "soft", 20, context=True)),
    ("recall_on_prompt",         _e(["UserPromptSubmit"], "soft", 30, context=True)),

    # PreToolUse — Edit|Write|MultiEdit enforcement (hard)
    ("check_agent_claim",           _e(["PreToolUse"], "hard", 110)),
    ("check_claudemd_lock",         _e(["PreToolUse"], "hard", 120)),
    ("check_raw_immutable",         _e(["PreToolUse"], "hard", 130)),
    ("check_source_original_file",  _e(["PreToolUse"], "hard", 140)),
    ("check_external_editor_drift", _e(["PreToolUse"], "hard", 150)),
    ("check_skill_registry",        _e(["PreToolUse"], "hard", 160)),
    ("check_machine_path",          _e(["PreToolUse"], "hard", 170)),
    ("check_secret_leak",           _e(["PreToolUse"], "hard", 180)),
    ("check_harness_routing",       _e(["PreToolUse"], "hard", 190)),
    ("check_output_format",         _e(["PreToolUse"], "hard", 200)),
    ("check_cost_tier",             _e(["PreToolUse"], "hard", 210)),
    ("check_a_focus",               _e(["PreToolUse"], "hard", 220)),
    ("check_a_flow_discipline",     _e(["PreToolUse"], "hard", 230)),
    # PreToolUse — Bash enforcement (hard)
    ("check_bash_destructive_git", _e(["PreToolUse"], "hard", 240)),
    ("check_bash_no_branch",       _e(["PreToolUse"], "hard", 250)),
    ("check_apikey",               _e(["PreToolUse"], "hard", 260)),
    ("check_delegation_gate",      _e(["PreToolUse"], "hard", 270)),
    # PreToolUse — Bash advisory (soft; source: "never block — warn + backup
    # only" — it backs up HEAD then warns; invoked via runner in Claude wiring)
    ("check_git_rebase_safety", _e(["PreToolUse"], "soft", 275)),
    # PreToolUse — Agent advisory (soft; source: "WARN-ONLY ... Never blocks")
    ("check_subagent_fanout", _e(["PreToolUse"], "soft", 280)),

    # PostToolUse — observers (soft)
    ("log_subagent_result",  _e(["PostToolUse"], "soft", 300)),
    ("auto_council_trigger", _e(["PostToolUse"], "soft", 310)),
    ("memory_capture",       _e(["PostToolUse"], "soft", 320)),

    # Stop — advisors/cleanup (soft; self_audit warns "BLOCK SHIP" but
    # never exits 2 — advisory by design per AGENTS.md Layer 1)
    ("self_audit",           _e(["Stop"], "soft", 400, context=True)),
    ("a_focus_stop",         _e(["Stop"], "soft", 410, context=True)),
    ("release_agent_claims", _e(["Stop"], "soft", 420)),
)

# NOT registered (deliberately): prompt_redactor, task_lease_reaper,
# git_safety_backup, post_wiki_edit, a_loop_distill, session_start —
# library/utility scripts that provider configs invoke directly (all
# non-blocking) and that the runner therefore refuses.


def validate_registry(registry=None, hooks_dir: Path | None = None,
                      skip_executable_check: bool = False) -> list[str]:
    """Return human-readable validation errors for a mapping or pre-dict sequence."""
    source = registry if registry is not None else HOOK_SPECS
    hdir = Path(hooks_dir) if hooks_dir is not None else HOOKS_DIR
    errors: list[str] = []
    seen_names: set[str] = set()
    seen_orders: dict[int, str] = {}

    try:
        entries = list(source.items()) if isinstance(source, dict) else list(source)
    except TypeError:
        return ["registry must be a mapping or ordered sequence of (hook_id, policy) pairs"]

    for item in entries:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            errors.append("registry entry must be a (hook_id, policy) pair")
            continue
        name, entry = item
        if not isinstance(name, str) or not name:
            errors.append("hook id must be a non-empty string")
            continue
        if name in seen_names:
            errors.append(f"{name}: duplicate hook id")
        else:
            seen_names.add(name)

        if not isinstance(entry, dict):
            errors.append(f"{name}: entry must be a mapping")
            continue
        events = entry.get("events")
        if not isinstance(events, list) or not events:
            errors.append(f"{name}: must declare at least one lifecycle event")
        else:
            for ev in events:
                if ev not in KNOWN_EVENTS:
                    errors.append(f"{name}: unknown lifecycle event {ev!r}")
        cls = entry.get("classification")
        if cls not in CLASSIFICATIONS:
            errors.append(f"{name}: classification must be one of {CLASSIFICATIONS}")
        order = entry.get("order")
        if not isinstance(order, int) or isinstance(order, bool):
            errors.append(f"{name}: order must be an int")
        elif order in seen_orders:
            errors.append(f"{name}: duplicate order {order} (also used by "
                          f"{seen_orders[order]}) — ordering must be deterministic")
        else:
            seen_orders[order] = name
    return errors


def _validated_lookup(registry=None, hooks_dir: Path | None = None) -> dict[str, dict]:
    """Validate the pre-lookup source before constructing its mapping view."""
    source = registry if registry is not None else HOOK_SPECS
    errors = validate_registry(source, hooks_dir=hooks_dir)
    if errors:
        raise RegistryError("; ".join(errors[:5]))
    entries = source.items() if isinstance(source, dict) else source
    return dict(entries)


# Public compatibility mapping for existing runner/tests. It is derived only
# after the ordered source authority has passed validation.
HOOK_REGISTRY: dict[str, dict] = _validated_lookup()


def load_registry(hooks_dir: Path | None = None) -> dict:
    """Validate and return the registry. Raises RegistryError on ANY problem —
    callers (the runner) must fail CLOSED, never downgrade."""
    return _validated_lookup(HOOK_SPECS, hooks_dir=hooks_dir)


def classification_of(name: str, registry: dict | None = None) -> str:
    reg = registry if registry is not None else HOOK_REGISTRY
    try:
        return reg[name]["classification"]
    except (KeyError, TypeError) as e:
        raise RegistryError(f"hook not registered: {name}") from e


def hooks_for_event(event: str, registry: dict | None = None) -> list[str]:
    """Registered hooks for one event in deterministic (order, name) order."""
    reg = registry if registry is not None else HOOK_REGISTRY
    names = [n for n, e in reg.items() if event in (e.get("events") or [])]
    return sorted(names, key=lambda n: (reg[n].get("order", 10**9), n))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" not in argv:
        sys.stderr.write("usage: registry.py --check\n")
        return 1
    hooks_dir = Path(os.environ.get("AWIKI_HOOKS_DIR", str(HOOKS_DIR)))
    errors = validate_registry(hooks_dir=hooks_dir)
    if errors:
        for e in errors:
            sys.stderr.write(f"registry error: {e}\n")
        return 1
    names = len(HOOK_REGISTRY)
    hard = sum(1 for v in HOOK_REGISTRY.values() if v["classification"] == "hard")
    print(f"hook registry OK: {names} hooks ({hard} hard, {names - hard} soft)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
