#!/bin/bash
# Show active TODOs from session-memory.md on session start
# Runs as part of SessionStart hook
# Source: A-Wiki Phase 1 — Hook Pipeline Activation

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/personal_paths.sh
. "$REPO_ROOT/scripts/lib/personal_paths.sh"

SESSION_FILE="$(awiki_session_memory_path "$REPO_ROOT" || true)"

if [ -z "$SESSION_FILE" ] || [ ! -f "$SESSION_FILE" ]; then
    exit 0
fi

# Extract only unchecked items from the canonical Active TODOs block.
TODOS=$(awk '
    /^## .*Active TODOs/ { in_block = 1; next }
    in_block && /^## / { in_block = 0 }
    in_block && /^- \[ \] / { print $0 }
' "$SESSION_FILE" 2>/dev/null | head -"${AWIKI_TODO_LIMIT:-12}")

if [ -n "$TODOS" ]; then
    echo "📋 Active TODOs (from session-memory.md):"
    echo "$TODOS" | while IFS= read -r line; do
        echo "  $line"
    done
    echo ""
fi
