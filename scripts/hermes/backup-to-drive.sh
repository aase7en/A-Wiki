#!/bin/bash
# Hermes → Google Drive Backup
# Collects sessions, config, memories → drive/backups/hermes/
# Cron: 0 3 * * * bash scripts/hermes/backup-to-drive.sh
set -e

A_WIKI="${A_WIKI_DIR:-$HOME/A-Wiki}"
DRIVE="$A_WIKI/drive/backups/hermes"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
HERMES_BIN="${HERMES_BIN:-$HOME/.hermes/hermes-agent/venv/bin/hermes}"
PROFILE="tech_and_ai_architect"

mkdir -p "$DRIVE/sessions" "$DRIVE/config" "$DRIVE/memories"

echo "=== $(date): Drive Backup ==="

# 1. Sessions
echo "[1/3] Exporting sessions..."
"$HERMES_BIN" -p "$PROFILE" sessions export /tmp/hermes-sessions.jsonl 2>/dev/null || true
if [ -f /tmp/hermes-sessions.jsonl ]; then
  gzip -f /tmp/hermes-sessions.jsonl
  cp /tmp/hermes-sessions.jsonl.gz "$DRIVE/sessions/sessions-${TIMESTAMP}.jsonl.gz"
  echo "  Sessions: $(du -h $DRIVE/sessions/sessions-${TIMESTAMP}.jsonl.gz | cut -f1)"
fi

# 2. Config
echo "[2/3] Backing up config..."
cp "$HOME/.hermes/profiles/$PROFILE/config.yaml" "$DRIVE/config/config-${TIMESTAMP}.yaml" 2>/dev/null || true
cp "$HOME/.hermes/profiles/$PROFILE/SOUL.md" "$DRIVE/config/SOUL-${TIMESTAMP}.md" 2>/dev/null || true

# 3. Memories
echo "[3/3] Backing up memories..."
cp "$HOME/.hermes/profiles/$PROFILE/memories/MEMORY.md" "$DRIVE/memories/MEMORY-${TIMESTAMP}.md" 2>/dev/null || true
cp "$HOME/.hermes/profiles/$PROFILE/memories/USER.md" "$DRIVE/memories/USER-${TIMESTAMP}.md" 2>/dev/null || true

# Cleanup — keep 30 days
for dir in sessions config memories; do
  ls -t "$DRIVE/$dir"/ 2>/dev/null | tail -n +31 | while read f; do
    rm -f "$DRIVE/$dir/$f"
  done
done

echo "=== Done: $DRIVE ==="
