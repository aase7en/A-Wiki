#!/usr/bin/env bash
# scripts/live-dashboard/awiki-live-init.sh — Universal A-Wiki Live initializer
# ===========================================================================
# Idempotent: safe to call multiple times per session.
# - Ensures the Live Dashboard daemon is running (port 7790)
# - Emits a session_start event so the dashboard shows this session
#
# Usage:
#   bash scripts/live-dashboard/awiki-live-init.sh [agent_name]
#
# Examples:
#   bash scripts/live-dashboard/awiki-live-init.sh kilo
#   bash scripts/live-dashboard/awiki-live-init.sh cursor
#   bash scripts/live-dashboard/awiki-live-init.sh cline
#
# Auto-called by:
#   - Claude Code  → .claude/hooks/session_start.py (already exists)
#   - Codex        → .codex/hooks.json → session_start.py (already exists)
#   - Kilo         → .kilo/command/awiki-session-start.md
#   - Cursor       → .cursorrules (session-start instruction)
#   - Windsurf     → .windsurfrules (session-start instruction)
#   - Cline        → .clinerules (session-start instruction)
#   - Copilot      → .github/copilot-instructions.md (session-start instruction)
#   - VS Code      → .vscode/tasks.json runOn:folderOpen (dashboard only)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENT="${1:-unknown}"

# 1. Ensure dashboard daemon is running (idempotent)
bash "$REPO_ROOT/scripts/dashboard-ensure.sh" --no-browser

# 2. Emit session_start event
python3 "$REPO_ROOT/scripts/live-dashboard/event_logger.py" session_start agent="$AGENT"

echo "A-Wiki Live initialized (agent=$AGENT, dashboard on :7790)"
