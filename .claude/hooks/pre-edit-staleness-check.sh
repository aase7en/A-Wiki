#!/usr/bin/env bash
# L1: Edit Guardian — lazy staleness check before any wiki/script edit
# ถ้า session ค้างนาน (>30 นาทีตั้งแต่ fetch ล่าสุด) → fetch + auto-pull ถ้า behind
# 0 tokens, ~50ms overhead เฉพาะเมื่อ stale เท่านั้น

input=$(cat)
TOOL=$(echo "$input" | jq -r '.tool_name // empty' 2>/dev/null)

# Only guard Edit/Write/MultiEdit tool calls
case "$TOOL" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac

# Only guard wiki/ scripts/ .claude/ files
FILE=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
echo "$FILE" | grep -qE '/(wiki|scripts|\.claude)/' || exit 0

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$REPO"

# Read last fetch timestamp (written by L0 session-start hook)
LAST_FETCH_FILE=".git/LAST_FETCH_TIME"
NOW=$(date +%s)
LAST=$(cat "$LAST_FETCH_FILE" 2>/dev/null || echo 0)
AGE=$((NOW - LAST))
STALE_AFTER=1800  # 30 minutes

[ "$AGE" -le "$STALE_AFTER" ] && exit 0  # fresh — skip

# Lazy fetch (quiet, background-safe)
git fetch origin main --quiet 2>/dev/null && echo "$NOW" > "$LAST_FETCH_FILE"

BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
[ "$BEHIND" -eq 0 ] && exit 0  # up-to-date, just stale timestamp

# Auto-pull before the edit goes through
echo "[sync] ⚡ session stale (${AGE}s since last sync) — pulling $BEHIND remote commit(s)..." >&2
if git pull --rebase origin main --quiet 2>/dev/null; then
  echo "[sync] ✅ auto-synced before edit — wiki is current" >&2
  echo "$NOW" > "$LAST_FETCH_FILE"
else
  echo "[sync] ⚠️  pull failed — edit may be on stale content, resolve manually after" >&2
fi

exit 0
