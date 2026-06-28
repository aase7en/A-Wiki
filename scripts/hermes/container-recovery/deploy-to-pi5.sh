#!/bin/bash
# deploy-to-pi5.sh - Deploy container recovery daemon from A-Wiki repo to Pi5 host path
# Run this ON the Pi5 host (NOT inside container).
# Usage: bash deploy-to-pi5.sh
set -euo pipefail

HOST_RECOV_DIR="/home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes"
CANONICAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Deploying Container Recovery Daemon v2.0 ==="
echo "Source:      $CANONICAL_DIR"
echo "Target:      $HOST_RECOV_DIR"

# 1. Create target dirs
mkdir -p "$HOST_RECOV_DIR/systemd"
mkdir -p "$HOST_RECOV_DIR/recovery/health-checks"
mkdir -p "$HOST_RECOV_DIR/recovery/alerts"

# 2. Copy core files
cp "$CANONICAL_DIR/container-recovery-v2.sh" "$HOST_RECOV_DIR/"
cp "$CANONICAL_DIR/containers.conf" "$HOST_RECOV_DIR/"
cp "$CANONICAL_DIR/model-state.json" "$HOST_RECOV_DIR/"

# 3. Copy health checks
cp "$CANONICAL_DIR/recovery/health-checks/"*.sh "$HOST_RECOV_DIR/recovery/health-checks/"

# 4. Substitute placeholder in systemd service, then copy
sed "s|__HOST_RECOV_DIR__|$HOST_RECOV_DIR|g" \
  "$CANONICAL_DIR/systemd/hermes-container-recovery.service" \
  > "$HOST_RECOV_DIR/systemd/hermes-container-recovery.service"

cp "$CANONICAL_DIR/systemd/hermes-container-recovery.timer" \
   "$HOST_RECOV_DIR/systemd/"

# 5. Set execute bits
chmod +x "$HOST_RECOV_DIR/container-recovery-v2.sh"
chmod +x "$HOST_RECOV_DIR/recovery/health-checks/"*.sh

# 6. Verify result
echo ""
echo "Deployment complete. Files deployed:"
ls -la "$HOST_RECOV_DIR/"
echo ""
echo "--- systemd ---"
ls -la "$HOST_RECOV_DIR/systemd/"
echo ""
echo "--- health-checks ---"
ls -la "$HOST_RECOV_DIR/recovery/health-checks/"
echo ""
echo "=== Next steps (activation) ==="
echo "1. Add umbrel to docker group:"
echo "   sudo usermod -aG docker umbrel && sudo systemctl restart user@1000"
echo ""
echo "2. Set up Telegram env:"
echo "   locate TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from web_1:"
echo "   sudo docker exec hermes-agent_web_1 sh -c 'grep -E \"TELEGRAM_(BOT_TOKEN|CHAT_ID)\" /opt/data/.env /opt/data/.hermes/.env /opt/hermes/.env 2>/dev/null'"
echo "   Then write to: $HOST_RECOV_DIR/recovery/telegram.env (chmod 600)"
echo ""
echo "3. Install systemd user service:"
echo "   mkdir -p ~/.config/systemd/user"
echo "   cp $HOST_RECOV_DIR/systemd/hermes-container-recovery.* ~/.config/systemd/user/"
echo "   sudo loginctl enable-linger umbrel"
echo "   systemctl --user daemon-reload && systemctl --user enable --now hermes-container-recovery.timer"
echo ""
echo "4. Verify:"
echo "   systemctl --user list-timers | grep hermes"
echo "   bash $HOST_RECOV_DIR/container-recovery-v2.sh"
echo "   tail -50 $HOST_RECOV_DIR/recovery/recovery.log"
