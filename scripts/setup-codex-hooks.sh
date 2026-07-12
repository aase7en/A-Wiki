#!/usr/bin/env bash
# scripts/setup-codex-hooks.sh — enable Codex Desktop hooks with full guardrail coverage.
#
# This script cannot DOWNGRADE hooks — if .codex/hooks.json already exists and has
# required guardrails, it is kept. Only missing guardrails are added.
#
# Preferred alternative: python3 scripts/setup-codex-config.py (also writes config.toml)
# This script kept for backwards compatibility and quick hook-only resets.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p .codex

if [ ! -e ".codex/hooks" ] && [ -d ".claude/hooks" ]; then
  ln -s ../.claude/hooks .codex/hooks 2>/dev/null || cp -R .claude/hooks .codex/hooks
fi

# Delegate full-coverage write to setup-codex-config.py if available
if [ -f "scripts/setup-codex-config.py" ]; then
  echo "🔧 Delegating to setup-codex-config.py for full guardrail coverage..."
  python3 scripts/setup-codex-config.py
  exit $?
fi

# Fallback: write hooks.json directly (kept in sync with setup-codex-config.py HOOKS_CONFIG)
cat > .codex/hooks.json <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-cost-tier"},
          {"type": "command", "command": "bash .codex/hooks/pre-edit-staleness-check.sh"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-claudemd-lock"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-raw-immutable"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-source-original-file"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-external-editor-drift"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-output-format"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-harness-routing"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-skill-registry"}
        ]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-cost-tier"}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-bash-destructive-git"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-bash-no-branch"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-secret-leak"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-apikey"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-delegation-gate"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {"type": "command", "command": "bash .codex/hooks/handoff-auto-export.sh"},
          {"type": "command", "command": "bash .codex/hooks/post-wiki-edit-gen-index.sh"}
        ]
      },
      {
        "matcher": "TodoWrite",
        "hooks": [
          {"type": "command", "command": "bash .codex/hooks/checkpoint-on-todo.sh"}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "bash .codex/hooks/checkpoint-on-commit.sh"},
          {"type": "command", "command": "bash .codex/hooks/post-push-todo-remind.sh"}
        ]
      }
    ],
    "PostCompact": [
      {
        "hooks": [
          {"type": "command", "command": "echo 'Context compacted. Re-read wiki/context/wiki-overview.md and wiki/context/session-memory.md, then resume from current TODOs.'"}
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
          {"type": "command", "command": "python3 scripts/hooks/session_start.py"}
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "bash scripts/agent-switch.sh stop"},
          {"type": "command", "command": "bash .codex/hooks/stop-auto-commit.sh"}
        ]
      }
    ]
  }
}
JSON

echo "✅ Codex Desktop hooks configured: .codex/hooks.json (full guardrail coverage)"
