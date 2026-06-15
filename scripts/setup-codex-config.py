#!/usr/bin/env python3
"""
scripts/setup-codex-config.py — Regenerate .codex/config.toml and .codex/hooks.json
for A-Wiki on any machine (Mac / Linux / WSL / Git Bash).

What it does:
  1. Copies .codex/config.toml from the tracked template (this repo contains the
     public-safe template; secrets are never written here).
  2. Writes .codex/hooks.json with full guardrail coverage matching Claude Code parity.
  3. Creates .codex/hooks/ symlink → .claude/hooks/ if .claude/hooks/ exists.
  4. Validates that required guardrail hook scripts exist.
  5. Prints a readiness summary.

Usage:
  python3 scripts/setup-codex-config.py [--check]

Options:
  --check   Validate only; do not write any files (exit 1 if parity missing).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CODEX_DIR = REPO_ROOT / ".codex"
CONFIG_TEMPLATE = CODEX_DIR / "config.toml"
HOOKS_JSON_PATH = CODEX_DIR / "hooks.json"
CLAUDE_HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
CODEX_HOOKS_DIR = CODEX_DIR / "hooks"

# These guardrails MUST be present in PreToolUse Edit|Write|MultiEdit hooks
REQUIRED_GUARDRAILS = [
    "check-cost-tier",
    "check-claudemd-lock",
    "check-raw-immutable",
    "check-harness-routing",
    "check-output-format",
    "check-source-original-file",
    "check-external-editor-drift",
]

# These guardrails MUST be in PreToolUse Bash hooks.
# check-delegation-gate belongs here (NOT under Agent) — the hook only acts on
# Bash `git push`, so wiring it under any other matcher makes it dead.
REQUIRED_BASH_GUARDRAILS = [
    "check-bash-destructive-git",
    "check-bash-no-branch",
    "check-secret-leak",
    "check-apikey",
    "check-delegation-gate",
]

HOOKS_CONFIG: dict = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {"type": "command", "command": f"python3 scripts/hooks_runner.py {g}"}
                    for g in [
                        "check-cost-tier",
                        "check-claudemd-lock",
                        "check-raw-immutable",
                        "check-source-original-file",
                        "check-external-editor-drift",
                        "check-output-format",
                        "check-harness-routing",
                    ]
                ] + [
                    {"type": "command", "command": "bash .codex/hooks/pre-edit-staleness-check.sh"},
                ],
            },
            {
                "matcher": "Agent",
                "hooks": [
                    {"type": "command", "command": "python3 scripts/hooks_runner.py check-cost-tier"},
                ],
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {"type": "command", "command": f"python3 scripts/hooks_runner.py {g}"}
                    for g in REQUIRED_BASH_GUARDRAILS
                ],
            },
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {"type": "command", "command": "bash .codex/hooks/handoff-auto-export.sh"},
                    {"type": "command", "command": "bash .codex/hooks/post-wiki-edit-gen-index.sh"},
                ],
            },
            {
                "matcher": "TodoWrite",
                "hooks": [
                    {"type": "command", "command": "bash .codex/hooks/checkpoint-on-todo.sh"},
                ],
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {"type": "command", "command": "bash .codex/hooks/checkpoint-on-commit.sh"},
                    {"type": "command", "command": "bash .codex/hooks/post-push-todo-remind.sh"},
                ],
            },
        ],
        "PostCompact": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "echo 'Context compacted. Re-read wiki/context/wiki-overview.md "
                            "and wiki/context/session-memory.md, then resume from current TODOs.'"
                        ),
                    }
                ]
            }
        ],
        "SessionStart": [
            {
                "hooks": [
                    {"type": "command", "command": "bash .codex/hooks/session-start-git-pull.sh"},
                    {"type": "command", "command": "bash .codex/hooks/wiki-context-check.sh"},
                    {"type": "command", "command": "bash .codex/hooks/session-start-binary-scan.sh"},
                    {"type": "command", "command": "bash scripts/show-active-todos.sh"},
                    {"type": "command", "command": "bash scripts/hooks/load-drive-keys.sh"},
                    {"type": "command", "command": "bash .codex/hooks/session-start-apikey-check.sh"},
                    {"type": "command", "command": "bash .codex/hooks/build-pharmacy-db.sh"},
                    {"type": "command", "command": "python3 scripts/hooks/session_start.py"},
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {"type": "command", "command": "bash scripts/agent-switch.sh stop"},
                    {"type": "command", "command": "bash .codex/hooks/stop-auto-commit.sh"},
                ]
            }
        ],
    }
}


def check_guardrail_parity(hooks_data: dict) -> list[str]:
    """Return list of missing required guardrails."""
    missing = []
    pre_tool = hooks_data.get("hooks", {}).get("PreToolUse", [])
    all_commands: list[str] = []
    for entry in pre_tool:
        for hook in entry.get("hooks", []):
            all_commands.append(hook.get("command", ""))

    for g in REQUIRED_GUARDRAILS + REQUIRED_BASH_GUARDRAILS:
        if not any(g in cmd for cmd in all_commands):
            missing.append(g)
    return missing


def setup_hooks_symlink() -> None:
    """Create .codex/hooks → .claude/hooks symlink if needed."""
    if not CLAUDE_HOOKS_DIR.exists():
        return
    if CODEX_HOOKS_DIR.is_symlink():
        return
    if CODEX_HOOKS_DIR.exists():
        return
    CODEX_HOOKS_DIR.symlink_to(Path("../.claude/hooks"))
    print(f"  ✓ Created .codex/hooks → .claude/hooks symlink")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup or validate Codex config + hooks for A-Wiki")
    parser.add_argument("--check", action="store_true", help="Validate only; do not write files")
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    CODEX_DIR.mkdir(exist_ok=True)

    if args.check:
        # Validate mode
        ok = True
        if not CONFIG_TEMPLATE.exists():
            print(f"❌ .codex/config.toml missing — run without --check to create it")
            ok = False
        if not HOOKS_JSON_PATH.exists():
            print(f"❌ .codex/hooks.json missing — run without --check to create it")
            ok = False
        else:
            try:
                hooks_data = json.loads(HOOKS_JSON_PATH.read_text())
                missing = check_guardrail_parity(hooks_data)
                if missing:
                    print(f"❌ Missing guardrails in .codex/hooks.json: {missing}")
                    ok = False
                else:
                    print("✅ .codex/hooks.json has full guardrail coverage")
            except json.JSONDecodeError as e:
                print(f"❌ .codex/hooks.json invalid JSON: {e}")
                ok = False
        if not ok:
            sys.exit(1)
        print("✅ Codex config parity check passed")
        return

    # Write mode
    print("🔧 Setting up Codex config for A-Wiki...")

    # 1. config.toml — already tracked in repo; verify it exists
    if CONFIG_TEMPLATE.exists():
        print(f"  ✅ .codex/config.toml exists (template tracked in repo)")
    else:
        print(f"  ⚠️  .codex/config.toml missing — expected tracked template in repo")

    # 2. hooks.json — always regenerate (never downgrade guardrails)
    existing_commands: list[str] = []
    if HOOKS_JSON_PATH.exists():
        try:
            old_data = json.loads(HOOKS_JSON_PATH.read_text())
            missing = check_guardrail_parity(old_data)
            if not missing:
                print(f"  ✅ .codex/hooks.json already has full guardrail coverage")
                existing_commands = [
                    h["command"]
                    for entry in old_data.get("hooks", {}).get("PreToolUse", [])
                    for h in entry.get("hooks", [])
                ]
            else:
                print(f"  ⚠️  .codex/hooks.json missing guardrails {missing} — upgrading")
        except Exception:
            pass

    HOOKS_JSON_PATH.write_text(json.dumps(HOOKS_CONFIG, indent=2, ensure_ascii=False) + "\n")
    print(f"  ✓ .codex/hooks.json written (guardrail count: {len(REQUIRED_GUARDRAILS + REQUIRED_BASH_GUARDRAILS)})")

    # 3. hooks symlink
    setup_hooks_symlink()

    # 4. Validate
    missing = check_guardrail_parity(json.loads(HOOKS_JSON_PATH.read_text()))
    if missing:
        print(f"  ❌ Still missing guardrails after write: {missing}")
        sys.exit(1)

    print("\n✅ Codex config setup complete for A-Wiki")
    print("   Run: codex doctor --summary  to verify Codex picks up the config")
    print("   Run: python3 scripts/agent-preflight.py --skip-remote  to verify A-Wiki readiness")


if __name__ == "__main__":
    main()
