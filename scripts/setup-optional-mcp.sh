#!/usr/bin/env bash
# setup-optional-mcp.sh — opt-in installers for tool-shaped MCP servers
# (Graphify, GBrain). Neither is auto-installed by setup-local.sh — both are
# heavier than a drop-in skill (own runtime/DB), so they stay opt-in like
# GitNexus (see scripts/setup-gitnexus.sh).
#
# Usage:
#   bash scripts/setup-optional-mcp.sh --graphify
#   bash scripts/setup-optional-mcp.sh --gbrain
#
# Docs: wiki/entities/ai-tools/{graphify,gbrain}.md

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

case "${1:-}" in
  --graphify) setup_graphify ;;
  --gbrain)   setup_gbrain ;;
  *)
    echo "Usage: $0 --graphify | --gbrain"
    exit 1
    ;;
esac
