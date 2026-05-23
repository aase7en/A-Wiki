#!/usr/bin/env bash
# .claude/hooks/checkpoint-on-todo.sh
# PostToolUse hook fired after TodoWrite calls.
# Caches the latest todo payload and regenerates wiki/context/now.md.
# Debounced 30s — TodoWrite fires often.
#
# Exits 0 always (never blocks Claude).

set +e

LOCK="/tmp/wiki-checkpoint-todo-lock"
LAST="/tmp/wiki-now-lastrun"
CACHE="/tmp/wiki-last-todos.json"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Always cache the freshest todos (even if we debounce the regen)
if [ -n "$CLAUDE_TOOL_INPUT" ]; then
  echo "$CLAUDE_TOOL_INPUT" > "$CACHE" 2>/dev/null
fi

# Debounce 30s
if [ -f "$LAST" ]; then
  DIFF=$(( $(date +%s) - $(cat "$LAST" 2>/dev/null || echo 0) ))
  [ "$DIFF" -lt 30 ] && exit 0
fi

# Lock (prevent parallel runs)
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null; true' EXIT

date +%s > "$LAST"

cd "$REPO" || exit 0
bash scripts/regen-now.sh todo 2>/dev/null || true
exit 0
