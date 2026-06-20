#!/bin/bash
# =============================================================================
# Hermes Auto-Sync — Pi5 pulls latest config from GitHub daily
# =============================================================================
# Cron: 0 8 * * * cd ~/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh
# =============================================================================
set -e

CONTAINER="hermes-agent_web_1"
HERMES_BIN="/opt/hermes/bin/hermes"
PROFILE="tech_and_ai_architect"
REPO_DIR="$HOME/A-Wiki"
LOCK_FILE="/tmp/hermes-auto-sync.lock"
LAST_IMPORT_FILE="/tmp/hermes-last-import.txt"

[ -f "$LOCK_FILE" ] && { echo "Another sync running. Skip."; exit 0; }
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

echo "=== $(date): Hermes Auto-Sync ==="

cd "$REPO_DIR"
BEFORE=$(git rev-parse HEAD 2>/dev/null)
git pull --ff-only 2>&1
AFTER=$(git rev-parse HEAD 2>/dev/null)

if [ "$BEFORE" = "$AFTER" ]; then
  echo "No new commits."
  exit 0
fi

echo "New: ${BEFORE:0:7} → ${AFTER:0:7}"

LATEST=$(ls -t scripts/hermes/hermes-export-*.tar.gz 2>/dev/null | head -1)
[ -z "$LATEST" ] && { echo "No package."; exit 0; }

PKG_TIME=$(stat -c %Y "$LATEST" 2>/dev/null || echo 0)
LAST_TIME=$(cat "$LAST_IMPORT_FILE" 2>/dev/null || echo 0)
[ "$PKG_TIME" -le "$LAST_TIME" ] && { echo "Already imported."; exit 0; }

echo "Importing $LATEST..."
sudo -S -p '' docker cp "$LATEST" "$CONTAINER:/tmp/hermes-auto-import.tar.gz"
sudo -S -p '' docker exec "$CONTAINER" "$HERMES_BIN" profile import /tmp/hermes-auto-import.tar.gz 2>&1
sudo -S -p '' docker exec "$CONTAINER" "$HERMES_BIN" -p "$PROFILE" config set terminal.cwd "$REPO_DIR" 2>&1

echo "$PKG_TIME" > "$LAST_IMPORT_FILE"
echo "=== Done ✅ ==="
