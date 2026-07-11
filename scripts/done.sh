#!/usr/bin/env bash
# scripts/done.sh "<search_pattern>"
#
# Mark a TODO item as done in session-memory.md → commit → push
# Called by Claude when user says "เสร็จแล้ว" / "done" / "ทำเสร็จ"
#
# Usage:
#   bash scripts/done.sh "Pharmacy App"       # fuzzy match, case-insensitive
#   bash scripts/done.sh "[dream]"            # match entire tag
#   bash scripts/done.sh "gen-index"          # match keyword in description
#
# Exit: 0=ticked  1=no match  2=already done  3=ambiguous (multiple matches)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/personal_paths.sh
. "$REPO_ROOT/scripts/lib/personal_paths.sh"
MEMORY="$(awiki_session_memory_path "$REPO_ROOT" || true)"

if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/done.sh \"<search pattern>\"" >&2
  echo "  Fuzzy-matches against open TODO items in local session-memory" >&2
  exit 1
fi

if [ -z "$MEMORY" ] || [ ! -f "$MEMORY" ]; then
  echo "❌ No local session-memory found. Run: bash scripts/setup-local.sh" >&2
  exit 1
fi

PATTERN="$1"

# Find matching open TODO lines
MATCHES=$(grep -n "^- \[ \]" "$MEMORY" | grep -i "$PATTERN" || true)
MATCH_COUNT=$(echo "$MATCHES" | grep -c "." 2>/dev/null || echo 0)

if [ "$MATCH_COUNT" -eq 0 ]; then
  # Check if already done
  DONE=$(grep -n "^- \[x\]" "$MEMORY" | grep -i "$PATTERN" || true)
  if [ -n "$DONE" ]; then
    echo "✅ Already marked done:" >&2
    echo "$DONE" | sed 's/^/  /' >&2
    exit 2
  fi
  echo "❌ No open TODO matches: '$PATTERN'" >&2
  echo "   Open items:" >&2
  grep "^- \[ \]" "$MEMORY" | sed 's/^/  /' >&2
  exit 1
fi

if [ "$MATCH_COUNT" -gt 1 ]; then
  echo "⚠️  Multiple matches — be more specific:" >&2
  echo "$MATCHES" | sed 's/^/  /' >&2
  exit 3
fi

# Extract line number + item text
LINE_NUM=$(echo "$MATCHES" | cut -d: -f1)
ITEM_TEXT=$(echo "$MATCHES" | cut -d: -f2- | sed 's/^- \[ \] //')

# Replace [ ] with [x] on that exact line
sed -i "${LINE_NUM}s/^- \[ \] /- [x] /" "$MEMORY"

# Extract short label for commit message (strip markdown bold + emoji)
SHORT=$(echo "$ITEM_TEXT" | sed 's/\*\*\[.*\]\*\* //' | sed 's/ —.*//' | cut -c1-60)

echo "✅ Marked done: $SHORT" >&2

# Commit + push
cd "$REPO_ROOT"
git add "$MEMORY"
git commit -m "chore(done): ✅ $SHORT" 2>/dev/null && \
  git push origin main 2>/dev/null && \
  echo "📤 Pushed to origin/main" >&2 || \
  echo "⚠️  Push failed — changes committed locally" >&2

# Show remaining open items
REMAINING=$(grep -c "^- \[ \]" "$MEMORY" 2>/dev/null || echo 0)
echo "" >&2
echo "📋 TODOs remaining: $REMAINING" >&2
grep "^- \[ \]" "$MEMORY" | sed 's/^- \[ \] /  • /' >&2
