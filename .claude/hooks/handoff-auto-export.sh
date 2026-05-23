#!/usr/bin/env bash
# .claude/hooks/handoff-auto-export.sh — PostToolUse: lightweight handoff state update
#
# Triggered after Edit|Write|MultiEdit — updates only the uncommitted changes section
# in handoff.md so state is always current even if Claude stops unexpectedly.
#
# Debounced: skips if last run was <60s ago (avoids IO on every keystroke).

LOCK="/tmp/wiki-handoff-lock"
LAST_RUN_FILE="/tmp/wiki-handoff-lastrun"
HANDOFF="handoff.md"

# Debounce: skip if ran within last 60 seconds
if [ -f "$LAST_RUN_FILE" ]; then
  LAST=$(cat "$LAST_RUN_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  DIFF=$(( NOW - LAST ))
  if [ "$DIFF" -lt 60 ]; then
    exit 0
  fi
fi

# Lock: prevent concurrent runs (PostToolUse can fire in parallel)
if ! mkdir "$LOCK" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null; true' EXIT

# Only run if handoff.md exists
[ -f "$HANDOFF" ] || exit 0

# Record timestamp
date +%s > "$LAST_RUN_FILE"

# Delegate to main script (quick mode = update uncommitted only)
bash scripts/agent-switch.sh quick 2>/dev/null || true
