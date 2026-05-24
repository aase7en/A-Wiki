#!/bin/bash
# Show active TODOs from session-memory.md on session start
# Runs as part of SessionStart hook
# Source: A-Wiki Phase 1 — Hook Pipeline Activation

SESSION_FILE="wiki/context/session-memory.md"

if [ ! -f "$SESSION_FILE" ]; then
    exit 0
fi

# Extract most recent todo list (last --- block with TODO/Next items)
TODOS=$(awk '
    /^---/ { in_block = 1; next }
    /^---/ && in_block { in_block = 0; next }
    in_block && /TODO|Next|Action|Pending|☐|□|\[ \]/ { print $0 }
' "$SESSION_FILE" 2>/dev/null | head -20)

if [ -n "$TODOS" ]; then
    echo "📋 Active TODOs (from session-memory.md):"
    echo "$TODOS" | while IFS= read -r line; do
        echo "  $line"
    done
    echo ""
fi