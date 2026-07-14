#!/usr/bin/env bash
# setup-optional-mcp.sh — opt-in installers for tool-shaped MCP servers
# (Graphify, GBrain, Context7). None are auto-installed by setup-local.sh —
# all are heavier than a drop-in skill (own runtime/DB, or a hosted service
# needing an API key), so they stay opt-in like GitNexus (see
# scripts/setup-gitnexus.sh).
#
# Usage:
#   bash scripts/setup-optional-mcp.sh --graphify
#   bash scripts/setup-optional-mcp.sh --gbrain
#   bash scripts/setup-optional-mcp.sh --context7
#
# Docs: wiki/entities/ai-tools/{graphify,gbrain,context7}.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

info()  { echo "→ $*"; }
ok()    { echo "✅ $*"; }
warn()  { echo "⚠️  $*"; }
die()   { echo "❌ $*" >&2; exit 1; }

setup_graphify() {
  info "Graphify: delegating to existing scripts/install-graphify.sh"
  bash scripts/install-graphify.sh
  echo ""
  ok "Graphify installed."
  echo "Merge the 'graphify' entry from .mcp.json.example into your .mcp.json (disabled: false to enable)."
  echo "Docs: wiki/entities/ai-tools/graphify.md"
}

setup_gbrain() {
  info "GBrain requires the Bun runtime (not pip/npm)."
  if ! command -v bun >/dev/null 2>&1; then
    warn "Bun not found. Install first: curl -fsSL https://bun.sh/install | bash"
    die "Then re-run: bash scripts/setup-optional-mcp.sh --gbrain"
  fi
  ok "Bun found: $(bun --version)"

  info "Installing gbrain CLI (bun install -g github:garrytan/gbrain)..."
  bun install -g github:garrytan/gbrain

  info "Initializing local PGLite brain (no Docker, ~2s)..."
  gbrain init --pglite

  echo ""
  ok "GBrain CLI ready."
  echo "Register the MCP server yourself (asks for API keys interactively):"
  echo "    claude mcp add gbrain -- gbrain serve"
  echo "Or merge the 'gbrain' entry from .mcp.json.example into your .mcp.json (disabled: false to enable)."
  echo ""
  echo "Verify:  gbrain doctor"
  echo "Import:  gbrain import wiki/     # index A-Wiki's own wiki/ as a starting corpus"
  echo "Docs:    wiki/entities/ai-tools/gbrain.md"
}

setup_context7() {
  info "Context7 (upstash/context7): hosted MCP + live version-specific library docs."
  if ! command -v npx >/dev/null 2>&1; then
    die "npx not found. Install Node.js first, then re-run: bash scripts/setup-optional-mcp.sh --context7"
  fi

  warn "Context7 needs a CONTEXT7_API_KEY (free tier available at https://context7.com/dashboard)."
  echo "    Store it in drive/.secrets — never in .mcp.json, repo files, or chat:"
  echo "      python3 scripts/lib/drive_secrets.py --check   # verify drive/.secrets is reachable"
  echo ""
  info "Running the vendor's own installer (registers correctly for Claude Code):"
  if npx -y ctx7 setup --claude; then
    ok "Context7 installer finished."
  else
    warn "Installer did not complete — falling back to manual reference:"
    echo "    Server URL: https://mcp.context7.com/mcp"
    echo "    Auth: pass CONTEXT7_API_KEY as a header (see docs.context7.com for your client's exact syntax)"
  fi
  echo ""
  echo "Docs: wiki/entities/ai-tools/context7.md"
}

case "${1:-}" in
  --graphify) setup_graphify ;;
  --gbrain)   setup_gbrain ;;
  --context7) setup_context7 ;;
  *)
    echo "Usage: $0 --graphify | --gbrain | --context7"
    exit 1
    ;;
esac
