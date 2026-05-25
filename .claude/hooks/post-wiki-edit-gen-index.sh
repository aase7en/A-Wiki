#!/usr/bin/env bash
# PostToolUse: auto-run gen-index.py after wiki/ edits (debounced 120s).
# gen-index.py internally chains build-vec-index.py — fastembed/apsw must be
# importable. We prefer the repo's .venv (where requirements.txt installs go)
# and fall back to system python3 only as a last resort.
LAST="/tmp/wiki-genindex-lastrun"
LOCK="/tmp/wiki-genindex-lock"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -x "$REPO/.venv/bin/python3" ]; then
  PY="$REPO/.venv/bin/python3"
elif [ -x "$REPO/.venv/Scripts/python.exe" ]; then
  PY="$REPO/.venv/Scripts/python.exe"  # Git Bash on Windows
else
  PY="python3"
fi

# Check if edited file is inside wiki/
FILE=$(echo "$CLAUDE_TOOL_INPUT" | "$PY" -c "
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
# Don't swallow stderr — vec build failures (e.g. missing fastembed) should
# surface so the user can fix the venv instead of debugging stale embeddings.
"$PY" scripts/gen-index.py \
  && echo "[post-edit] ✅ gen-index.py refreshed" >&2 \
  || echo "[post-edit] ⚠️  gen-index.py failed (see stderr above)" >&2
