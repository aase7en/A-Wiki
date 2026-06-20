#!/bin/bash
# Hermes Session Backup — Export + compress → drive/backups/hermes/
# Cron: 0 2 * * * bash scripts/hermes/backup-sessions.sh
set -e

TIMESTAMP=$(date +%Y%m%d)
BACKUP_DIR="$HOME/A-Wiki/drive/backups/hermes/sessions"
mkdir -p "$BACKUP_DIR"

echo "=== $(date): Session Backup ==="

# Pi5 (Docker) vs MacBook (native)
if [ -f /.dockerenv ] || docker ps >/dev/null 2>&1; then
  # Docker mode (Pi5)
  CONTAINER="hermes-agent_web_1"
  PROFILE="tech_and_ai_architect"
  sudo -S -p '' docker exec "$CONTAINER" /opt/hermes/bin/hermes -p "$PROFILE" sessions export /tmp/sessions.jsonl 2>&1
  sudo -S -p '' docker cp "$CONTAINER:/tmp/sessions.jsonl" /tmp/sessions.jsonl
else
  # Native mode (MacBook)
  HERMES_BIN="${HERMES_BIN:-$HOME/.hermes/hermes-agent/venv/bin/hermes}"
  "$HERMES_BIN" -p tech_and_ai_architect sessions export /tmp/sessions.jsonl 2>&1
fi

# Compress
gzip -f /tmp/sessions.jsonl
mv /tmp/sessions.jsonl.gz "$BACKUP_DIR/sessions-${TIMESTAMP}.jsonl.gz"

# Keep only last 30 days
ls -t "$BACKUP_DIR"/sessions-*.jsonl.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "Backup: $BACKUP_DIR/sessions-${TIMESTAMP}.jsonl.gz ($(du -h "$BACKUP_DIR/sessions-${TIMESTAMP}.jsonl.gz" | cut -f1))"
echo "=== Done ==="
