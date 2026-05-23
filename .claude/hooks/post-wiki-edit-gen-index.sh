#!/usr/bin/env bash
# PostToolUse: auto-run gen-index.py after wiki/ edits (debounced 120s)
LAST="/tmp/wiki-genindex-lastrun"
LOCK="/tmp/wiki-genindex-lock"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Check if edited file is inside wiki/
FILE=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c "
import sys,json
try: print(json.load(sys.stdin).get('file_path',''))
except: print('')
" 2>/dev/null)
[[ "$FILE" == *"/wiki/"* ]] || exit 0

# Debounce 120s
if [ -f "$LAST" ]; then
  DIFF=$(( $(date +%s) - $(cat "$LAST" 2>/dev/null || echo 0) ))
  [ "$DIFF" -lt 120 ] && exit 0
fi

# Lock (prevent parallel runs)
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
date +%s > "$LAST"

cd "$REPO"
python3 scripts/gen-index.py 2>/dev/null \
  && echo "[post-edit] ✅ gen-index.py refreshed" >&2 \
  || echo "[post-edit] ⚠️  gen-index.py failed" >&2
