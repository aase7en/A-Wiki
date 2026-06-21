#!/bin/bash
# A-Wiki Live — Cloudflare Tunnel Setup
# Run this INSIDE the Hermes container terminal
# Umbrel → Settings → Terminal → App → Hermes Agent
#
# Prerequisites:
#   1. Cloudflare account (free at cloudflare.com)
#   2. Domain added to Cloudflare DNS
#
# This creates a PERMANENT named tunnel (URL never changes)

set -e

CLOUDFLARED=/opt/data/bin/cloudflared
TUNNEL_NAME="awiki-live"
DOMAIN="${1:-}"   # e.g. awiki.yourdomain.com

if [ -z "$DOMAIN" ]; then
    echo "Usage: bash setup-cloudflare-tunnel.sh <your-subdomain.yourdomain.com>"
    echo "Example: bash setup-cloudflare-tunnel.sh awiki.mydomain.com"
    exit 1
fi

echo "=== Step 1: Download cloudflared (if needed) ==="
if [ ! -f "$CLOUDFLARED" ]; then
    mkdir -p /opt/data/bin
    curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o "$CLOUDFLARED"
    chmod +x "$CLOUDFLARED"
fi
echo "cloudflared: $($CLOUDFLARED --version 2>&1 | head -1)"

echo ""
echo "=== Step 2: Login to Cloudflare ==="
echo "A URL will appear. Open it in YOUR browser (on Mac/phone)."
echo "Log in and authorize the domain."
echo ""
$CLOUDFLARED tunnel login

echo ""
echo "=== Step 3: Create named tunnel ==="
$CLOUDFLARED tunnel create $TUNNEL_NAME
CREDFILE=$(ls /opt/data/home/.cloudflared/*.json 2>/dev/null | head -1)
echo "Credentials: $CREDFILE"

echo ""
echo "=== Step 4: Configure tunnel ==="
mkdir -p /opt/data/home/.cloudflared
cat > /opt/data/home/.cloudflared/config.yml << YAML
tunnel: $TUNNEL_NAME
credentials-file: $CREDFILE

ingress:
  - hostname: $DOMAIN
    service: http://localhost:8501
  - service: http_status:404
YAML
echo "Config written to /opt/data/home/.cloudflared/config.yml"

echo ""
echo "=== Step 5: Route DNS ==="
$CLOUDFLARED tunnel route dns $TUNNEL_NAME $DOMAIN

echo ""
echo "=== Step 6: Run tunnel ==="
echo "Starting tunnel in background..."
nohup $CLOUDFLARED tunnel run $TUNNEL_NAME > /opt/data/cloudflared.log 2>&1 &
sleep 5
echo "Tunnel PID: $(pgrep -f 'cloudflared tunnel run')"

echo ""
echo "==============================================="
echo "✅ DONE! Your permanent URL: https://$DOMAIN"
echo "==============================================="
echo ""
echo "Test: curl https://$DOMAIN/health"
echo ""
echo "Update webapp: change HERMES_BASE in awiki-live.html to https://$DOMAIN"
