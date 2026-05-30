#!/usr/bin/env bash
# setup-codex-hooks.sh — enable Codex Desktop hooks with portable commands.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p .codex

if [ ! -e ".codex/hooks" ] && [ -d ".claude/hooks" ]; then
  ln -s ../.claude/hooks .codex/hooks 2>/dev/null || cp -R .claude/hooks .codex/hooks
fi

cat > .codex/hooks.json <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {"type": "command", "command": "bash .codex/hooks/pre-edit-staleness-check.sh"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-claudemd-lock"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-raw-immutable"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-external-editor-drift"}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-bash-destructive-git"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-bash-no-branch"},
          {"type": "command", "command": "python3 scripts/hooks_runner.py check-secret-leak"}
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

echo "Codex Desktop hooks configured: .codex/hooks.json"
