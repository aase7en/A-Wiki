#!/usr/bin/env bash
# setup-gitnexus.sh — Index A-Wiki (or any repo) with GitNexus + register MCP
# Usage: bash scripts/setup-gitnexus.sh [path-to-repo]
# Default: indexes current repo (A-Wiki itself)
#
# License note: GitNexus is PolyForm Noncommercial — personal/wiki = OK,
#               commercial = obtain license from upstream.
# Docs:        wiki/entities/ai-tools/gitnexus.md
# Upstream:    https://github.com/abhigyanpatwari/GitNexus

set -euo pipefail

REPO_PATH="${1:-$(pwd)}"
cd "$REPO_PATH"

# --- 1. Check Node.js ---
if ! command -v npx >/dev/null 2>&1; then
  echo "❌ npx not found. Install Node.js 18+ first." >&2
  exit 1
fi

# --- 2. Ensure .gitnexus/ is gitignored ---
if [ -f .gitignore ] && ! grep -qE '^\.gitnexus/?$' .gitignore; then
  echo "" >> .gitignore
  echo "# GitNexus code-graph cache (per-machine)" >> .gitignore
  echo ".gitnexus/" >> .gitignore
  echo "✅ Added .gitnexus/ to .gitignore"
fi

# --- 3. Index repo ---
echo "📊 Analyzing $REPO_PATH with GitNexus..."
npx -y gitnexus analyze

# --- 4. Register MCP (interactive) ---
echo ""
echo "🔌 To register GitNexus as MCP in Claude Code, run:"
echo "    npx gitnexus setup"
echo ""
echo "Or merge the 'gitnexus' entry from .mcp.json.example into your .mcp.json"

# --- 5. Smoke test ---
echo ""
echo "🧪 Smoke test: list 5 indexed symbols"
npx -y gitnexus query "function" --limit 5 || true

echo ""
echo "✅ Setup complete. See wiki/entities/ai-tools/gitnexus.md for usage."
