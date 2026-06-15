#!/usr/bin/env bash
# ============================================================================
# Setup Cline Hooks Symlinks
# ============================================================================
# Creates symlinks in .clinerules/hooks/ pointing to adapter.sh.
# Idempotent — safe to re-run.
#
# Usage:
#   bash scripts/cline-hooks/setup-symlinks.sh
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.clinerules/hooks"
ADAPTER="$REPO_ROOT/scripts/cline-hooks/adapter.sh"

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

# Ensure adapter exists and is executable
if [ ! -f "$ADAPTER" ]; then
  echo "❌ adapter.sh not found at $ADAPTER"
  exit 1
fi
chmod +x "$ADAPTER"

# Create symlinks for all 4 hook events
EVENTS=("PreToolUse" "PostToolUse" "TaskComplete" "TaskStart")
for EVENT in "${EVENTS[@]}"; do
  TARGET="$HOOKS_DIR/$EVENT"
  if [ -L "$TARGET" ]; then
    # Already a symlink — update it
    ln -sf "$ADAPTER" "$TARGET"
    echo "🔄 Updated $EVENT → adapter.sh"
  elif [ ! -e "$TARGET" ]; then
    # Doesn't exist — create
    ln -sf "$ADAPTER" "$TARGET"
    echo "✅ Created $EVENT → adapter.sh"
  else
    # Exists but not a symlink — skip (user may have custom hook)
    echo "⚠️  $EVENT exists (not a symlink) — skipping"
  fi
done

echo ""
echo "✅ Cline hooks symlinks ready"
echo "   Run: ls -la $HOOKS_DIR"