#!/usr/bin/env bash
# .claude/hooks/checkpoint-on-commit.sh
# PostToolUse hook (matcher: Bash) — fires on every Bash command.
# Filters internally: only regenerates now.md when the command was `git commit ...`.
# No debounce — commits are naturally spaced.
#
# Exits 0 always.

set +e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Extract the actual shell command from CLAUDE_TOOL_INPUT JSON
CMD=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cmd = data.get('command', '') if isinstance(data, dict) else ''
    print(cmd[:500])
except Exception:
    pass
" 2>/dev/null)

# Only act on git commit commands (and only successful ones — we use git log to verify)
echo "$CMD" | grep -qE '(^|[ &;|])git[ \t]+(-[^ ]+[ \t]+)*commit\b' || exit 0

# Confirm a fresh commit landed (within last 30s)
cd "$REPO" || exit 0
COMMIT_AGE=$(git log -1 --format=%ct 2>/dev/null)
NOW=$(date +%s)
if [ -n "$COMMIT_AGE" ] && [ "$(( NOW - COMMIT_AGE ))" -gt 30 ]; then
  # No recent commit — command may have failed (pre-commit hook etc.)
  exit 0
fi

bash scripts/regen-now.sh commit 2>/dev/null || true
exit 0
