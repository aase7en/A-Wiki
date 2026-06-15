#!/usr/bin/env bash
# ============================================================================
# Enable Cline Native Hooks
# ============================================================================
# Attempts to enable hooksEnabled in Cline settings.
#
# Cline stores hooksEnabled in VS Code global state (Protobuf), not in a
# plain JSON file we can safely edit.  This script tries two approaches:
#   1. VS Code command (preferred, if code CLI is available)
#   2. Instructions for manual enable (fallback)
#
# Usage:
#   bash scripts/cline-hooks/enable-hooks.sh
# ============================================================================
set -euo pipefail

echo "🪝 A-Wiki — Enable Cline Hooks"
echo ""

# ── Check if Cline extension is installed ───────────────────────────────────
CLINE_EXTS=$(find ~/.vscode/extensions -maxdepth 1 -name "saoudrizwan.claude-dev-*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$CLINE_EXTS" -eq 0 ]; then
  echo "⚠️  Cline extension (saoudrizwan.claude-dev) not found"
  echo "   Install from: https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev"
  exit 0
fi

# ── Check if symlinks are set up ────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MISSING=0
for EVENT in PreToolUse PostToolUse TaskComplete TaskStart; do
  if [ ! -L "$REPO_ROOT/.clinerules/hooks/$EVENT" ]; then
    MISSING=1
    echo "⚠️  Missing symlink: .clinerules/hooks/$EVENT"
  fi
done

if [ "$MISSING" -eq 1 ]; then
  echo "   Running setup-symlinks.sh..."
  bash "$REPO_ROOT/scripts/cline-hooks/setup-symlinks.sh"
fi

# ── Attempt 1: Check if already enabled ─────────────────────────────────────
# We can't reliably read Protobuf state, so we assume the user needs to
# enable it manually if this is their first time.

echo "📋 To enable Cline hooks:"
echo ""
echo "   1. Open VS Code Command Palette (Cmd+Shift+P)"
echo "   2. Type 'Cline: Settings' and open it"
echo "   3. Find 'Enable Hooks' and turn it ON"
echo "   4. Restart VS Code (or reload window)"
echo ""
echo "   Or, in Cline's chat panel:"
echo "   - Click the gear icon ⚙️ (Settings)"
echo "   - Scroll to 'Hooks' section"
echo "   - Toggle 'Enable Hooks' ON"
echo ""

# ── Attempt 2: Try VS Code settings file edit ───────────────────────────────
# Cline v3.8+ may read hooksEnabled from VS Code workspace settings.
# Try writing it (best-effort, non-destructive).
VSCODE_SETTINGS="$HOME/Library/Application Support/Code/User/settings.json"
if [ -f "$VSCODE_SETTINGS" ]; then
  if grep -q '"cline.*hooksEnabled"' "$VSCODE_SETTINGS" 2>/dev/null; then
    echo "✅ Found hooksEnabled in VS Code settings — already configured"
  else
    echo "💡 Tip: Add this to your VS Code settings.json for auto-enable:"
    echo '   "cline.hooksEnabled": true'
    echo ""
  fi
fi

echo "After enabling hooks, verify with:"
echo "  ls -la .clinerules/hooks/"
echo "  # Should show 4 symlinks → scripts/cline-hooks/adapter.sh"
echo ""
echo "✅ enable-hooks.sh — completed (manual step required for first time)"