#!/usr/bin/env python3
"""
scripts/setup-zcode-config.py — Wire the canonical A-Wiki hook engine into
.zcode/config.json (machine-local, gitignored) without touching its
machine-specific MCP server section.

Why this exists (defect #1, docs/plans/2026-08-21-auto-skill-consolidation.md
§4): .zcode/config.json previously wired only SessionStart / UserPromptSubmit
(named) / PostToolUse (named) / Stop (named) and had NO PreToolUse at all —
every hard gate (raw/ immutability, skill registry, secret leak, machine
paths, source provenance, …) was dead on ZCode even though the platform
supports the full Claude hook contract (verified live 2026-08-22).

What it does:
  1. Loads .zcode/config.json (creates a minimal shell if missing).
  2. Replaces ONLY the hooks section with the canonical provider model —
     event sweeps through scripts/hooks_runner.py, never named registered
     dispatch (Phase 6 contract). The mcp section and any other keys are
     preserved verbatim.
  3. Validates that required guardrail hook scripts exist.
  4. --check validates the live hooks section against the model without
     writing (exit 1 on drift) — usable from CI/preflight.

Usage:
  python3 scripts/setup-zcode-config.py [--check]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
ZCODE_DIR = REPO_ROOT / ".zcode"
CONFIG_PATH = ZCODE_DIR / "config.json"

_SWEEP_TIMEOUT_S = 30  # > runner HOOK_TOTAL_TIMEOUT (20s) so the runner's
                       # own fail-closed budget governs, not the host kill


def _runner(event: str) -> dict:
    """Canonical ZCode lifecycle dispatch command for one provider event."""
    return {
        "type": "command",
        "command": (
            "python3 ${ZCODE_PROJECT_DIR}/scripts/hooks_runner.py"
            f" --provider zcode --event {event}"
        ),
        "timeout": _SWEEP_TIMEOUT_S,
    }


# Full canonical ZCode hook surface: registered hooks enter ONLY through
# event sweeps (the runner filters by registry matchers); the one direct
# entry is the legacy session-start utility, which is not registry policy.
HOOKS_CONFIG: dict = {
    "enabled": True,
    "events": {
        "SessionStart": [
            {
                "matcher": "startup|resume|clear|compact",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "python3 ${ZCODE_PROJECT_DIR}/scripts/hooks/"
                            "session_start.py"
                        ),
                        "timeout": 30,
                    },
                    _runner("SessionStart"),
                ],
            }
        ],
        "UserPromptSubmit": [
            {"matcher": "", "hooks": [_runner("UserPromptSubmit")]}
        ],
        "PreToolUse": [
            {"matcher": "Edit|Write|MultiEdit", "hooks": [_runner("PreToolUse")]},
            {"matcher": "Agent", "hooks": [_runner("PreToolUse")]},
            {"matcher": "Bash", "hooks": [_runner("PreToolUse")]},
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [_runner("PostToolUse")],
            },
            {"matcher": "Bash", "hooks": [_runner("PostToolUse")]},
        ],
        "Stop": [
            {"matcher": "", "hooks": [_runner("Stop")]}
        ],
        "PostCompact": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "echo 'Context compacted. Re-read "
                            "wiki/context/wiki-overview.md and "
                            "wiki/context/session-memory.md, then resume "
                            "from current TODOs.'"
                        ),
                        "timeout": 10,
                    }
                ],
            }
        ],
    },
}


def merge_config(config: dict) -> dict:
    """Return config with the canonical hooks section and everything else
    (mcp servers, machine paths) preserved verbatim. Idempotent."""
    merged = dict(config)
    merged["hooks"] = {
        "enabled": HOOKS_CONFIG["enabled"],
        "events": json.loads(json.dumps(HOOKS_CONFIG["events"])),
    }
    return merged


def check_guardrail_scripts() -> list[str]:
    """Guardrail hook scripts referenced by the model must exist."""
    errors: list[str] = []
    for rel in ("scripts/hooks_runner.py", "scripts/hooks/session_start.py"):
        if not (REPO_ROOT / rel).is_file():
            errors.append(f"missing guardrail script: {rel}")
    return errors


def hooks_parity_errors(config: dict) -> list[str]:
    """Exact structured comparison of the live hooks section vs the model."""
    live = config.get("hooks")
    if not isinstance(live, dict):
        return ["hooks section missing (not a dict)"]
    if live.get("enabled") is not True:
        return ["hooks.enabled is not True"]
    actual = live.get("events")
    expected = HOOKS_CONFIG["events"]
    if actual == expected:
        return []
    errors = []
    if not isinstance(actual, dict):
        return [f"hooks.events is {type(actual).__name__}, expected dict"]
    for event in sorted(set(expected) | set(actual)):
        if event not in actual:
            errors.append(f"hooks.events missing {event}")
        elif actual[event] != expected[event]:
            errors.append(f"hooks.events[{event}] differs from canonical model")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Setup or validate ZCode hooks wiring for A-Wiki")
    parser.add_argument("--check", action="store_true",
                        help="Validate only; do not write files")
    args = parser.parse_args(argv)

    errors = check_guardrail_scripts()
    if errors:
        print("❌ " + "; ".join(errors))
        return 1

    if args.check:
        if not CONFIG_PATH.is_file():
            print("❌ .zcode/config.json missing — run without --check to create it")
            return 1
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        parity = hooks_parity_errors(config)
        if parity:
            print(f"❌ .zcode/config.json hook parity errors: {parity[:5]}")
            return 1
        print("✅ .zcode/config.json has canonical hook wiring")
        return 0

    print("🔧 Wiring ZCode hooks for A-Wiki...")
    if CONFIG_PATH.is_file():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        source = "existing .zcode/config.json (mcp section preserved)"
    else:
        config = {}
        source = "new minimal config"
    merged = merge_config(config)

    ZCODE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"  ✓ hooks section written from canonical model ({source})")
    print("  ✓ PreToolUse hard gates now live: raw-immutable, skill-registry,"
          " secret-leak, machine-path, source-provenance, claim-gate, …")
    return 0


if __name__ == "__main__":
    sys.exit(main())
