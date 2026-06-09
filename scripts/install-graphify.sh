#!/usr/bin/env bash
# install-graphify.sh — Install Graphify knowledge graph skill for Claude Code
#
# Graphify transforms files (code, PDF, markdown, images) into interactive
# knowledge graphs. It self-installs its SKILL.md to ~/.claude/skills/graphify/
# so Claude Code discovers it automatically after setup.
#
# Docs:     wiki/entities/ai-tools/graphify.md
# Upstream: https://github.com/safishamsi/graphify
# PyPI:     graphifyy (note: two y's)

set -euo pipefail

REQUIRED_PYTHON_MINOR=10

# --- helpers ---
info()  { echo "→ $*"; }
ok()    { echo "✅ $*"; }
warn()  { echo "⚠️  $*"; }
die()   { echo "❌ $*" >&2; exit 1; }

# --- 1. Python version check ---
PYTHON=$(command -v python3 || command -v python || die "Python not found. Install Python 3.10+")
PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt "$REQUIRED_PYTHON_MINOR" ) ]]; then
  die "Python $PY_VERSION found, but 3.$REQUIRED_PYTHON_MINOR+ required."
fi
info "Python $PY_VERSION ✓"

# --- 2. Detect install method (pipx preferred on managed systems) ---
USE_PIPX=0
if "$PYTHON" -m pip install --dry-run graphifyy 2>&1 | grep -q "externally-managed"; then
  if command -v pipx >/dev/null 2>&1; then
    info "Externally-managed Python detected → using pipx"
    USE_PIPX=1
  else
    warn "Externally-managed Python and pipx not found."
    warn "Install pipx first: pip install --user pipx"
    warn "Or use: brew install pipx  (macOS)"
    die "Cannot install without pipx on managed Python environment."
  fi
fi

# --- 3. Install graphifyy ---
if command -v graphify >/dev/null 2>&1; then
  CURRENT_VERSION=$(graphify --version 2>/dev/null || echo "unknown")
  info "Graphify already installed ($CURRENT_VERSION) — upgrading"
fi

if [[ "$USE_PIPX" -eq 1 ]]; then
  info "Installing via pipx..."
  pipx install graphifyy || pipx upgrade graphifyy
else
  info "Installing via pip..."
  "$PYTHON" -m pip install --upgrade graphifyy
fi

# Verify install
if ! command -v graphify >/dev/null 2>&1; then
  warn "graphify command not found in PATH after install."
  warn "Windows users: add %APPDATA%\\Python\\Python3xx\\Scripts to PATH"
  warn "Or try: python -m graphify install"
fi

# --- 4. Install SKILL.md to Claude Code skills directory ---
info "Installing Graphify skill to Claude Code..."
if command -v graphify >/dev/null 2>&1; then
  graphify install
  ok "SKILL.md installed → ~/.claude/skills/graphify/"
else
  warn "Could not run 'graphify install' — skill not auto-linked."
  warn "Run manually: graphify install"
fi

# --- 5. Summary ---
echo ""
ok "Graphify installed and ready."
echo ""
echo "Quick start:"
echo "  graphify .                      # build knowledge graph for current dir"
echo "  graphify query \"how does X work\" # query the graph"
echo "  graphify path \"NodeA\" \"NodeB\"   # find shortest path"
echo ""
echo "MCP server (add to .mcp.json):"
echo "  {\"command\": \"graphify\", \"args\": [\"serve\", \"--mode\", \"stdio\"]}"
echo ""
echo "See: wiki/entities/ai-tools/graphify.md"
