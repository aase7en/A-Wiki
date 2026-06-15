#!/usr/bin/env bash
# ============================================================================
# A-Wiki Cline Session Launcher
# ============================================================================
# Full session bootstrap for Cline:
#   1. Setup hook symlinks
#   2. Enable hooks (with instructions if first time)
#   3. Start Live Dashboard
#
# Usage:
#   bash scripts/live-dashboard/start-cline.sh
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🚀 A-Wiki Cline Session Launcher"
echo "================================="
echo ""

# Step 1: Setup hook symlinks
echo "[1/3] Setting up Cline hook symlinks..."
bash scripts/cline-hooks/setup-symlinks.sh
echo ""

# Step 2: Enable hooks
echo "[2/3] Checking hooks status..."
bash scripts/cline-hooks/enable-hooks.sh
echo ""

# Step 3: Start Live Dashboard
echo "[3/3] Starting A-Wiki Live Dashboard..."
bash scripts/dashboard-ensure.sh
echo ""

echo "================================="
echo "✅ Cline session ready!"
echo ""
echo "   Hooks:   ls -la .clinerules/hooks/"
echo "   Dashboard: http://localhost:7790"
echo ""
echo "   Open Cline (Cmd+Shift+P → Cline: Open in New Tab) and start working."