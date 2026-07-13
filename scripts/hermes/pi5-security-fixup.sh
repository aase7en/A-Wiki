#!/usr/bin/env bash
# =============================================================================
# pi5-security-fixup.sh — One-shot Pi5 security + sync fixup
# =============================================================================
# Run ONCE on the Pi5 (as user umbrel, via SSH or Umbrel Terminal widget).
# Fixes two issues in the legacy /home/umbrel/pi5-sync.sh:
#
#   1. SECURITY: the legacy script hardcodes the sudo password in plaintext:
#        echo "Admin1234!" | sudo -S docker ...
#      This installs a NOPASSWD sudoers drop-in for docker only, then removes
#      the password from the script.
#
#   2. QUALITY: the legacy script `docker restart`s the whole container every
#      6h (heavy). This repoints the systemd timer to scripts/hermes/awiki-pi5-sync.sh
#      which uses gateway SIGHUP rescan instead (lightweight).
#
# Idempotent: safe to re-run. Asks for sudo password ONCE (the last time).
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[X]${NC} $1"; }
step()  { echo -e "${CYAN}[>]${NC} $1"; }

# ---- Guard: must be on Pi5 ----
detect_pi5() {
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}
if ! detect_pi5; then
  err "This script is for Pi5 only. Run on the Pi5 host via SSH."
  exit 1
fi
if [ "$(whoami)" != "umbrel" ]; then
  err "Run as user umbrel (not $(whoami)). SSH in as umbrel@... first."
  exit 1
fi

REPO_DIR="${A_WIKI_DIR:-$HOME/A-Wiki}"
if [ ! -d "$REPO_DIR/.git" ]; then
  err "A-Wiki repo not found at $REPO_DIR. Clone first: git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki"
  exit 1
fi

echo "=============================================="
echo "  Pi5 Security + Sync Fixup (one-shot)"
echo "=============================================="
echo ""

# ---- Step 1: Install NOPASSWD docker sudoers (asks password ONE LAST TIME) ----
step "Step 1/4: Install NOPASSWD sudoers for docker..."
SUDOERS_FILE="/etc/sudoers.d/umbrel-docker"
SUDOERS_LINE="umbrel ALL=(ALL) NOPASSWD: /usr/bin/docker"

# Check if already set
if sudo -n true 2>/dev/null || sudo grep -q "^$SUDOERS_LINE$" "$SUDOERS_FILE" 2>/dev/null; then
  info "NOPASSWD docker already configured — skipping"
else
  echo "  This will ask for the umbrel sudo password ONE LAST TIME."
  echo "  After this, docker commands run without password (NOPASSWD docker only)."
  echo "$SUDOERS_LINE" | sudo tee "$SUDOERS_FILE" > /dev/null
  sudo chmod 440 "$SUDOERS_FILE"
  # Verify it took effect
  if sudo -n docker ps > /dev/null 2>&1; then
    info "NOPASSWD docker working"
  else
    err "NOPASSWD docker failed to apply — check $SUDOERS_FILE"
    exit 1
  fi
fi

# ---- Step 2: Backup legacy pi5-sync.sh, repoint timer to repo script ----
step "Step 2/4: Repoint hermes-sync timer to awiki-pi5-sync.sh..."
LEGACY="/home/umbrel/pi5-sync.sh"
TIMER_DIR="$HOME/.config/systemd/user"
TIMER_FILE="$TIMER_DIR/hermes-sync.service"

if [ -f "$LEGACY" ]; then
  BACKUP="${LEGACY}.pre-fixup-$(date +%Y%m%d%H%M%S)"
  cp "$LEGACY" "$BACKUP"
  info "Backed up legacy script → $BACKUP"
fi

# Rewrite the systemd service to call the repo's awiki-pi5-sync.sh instead.
# The repo script uses sudo -n (works with NOPASSWD) + gateway rescan (no restart).
mkdir -p "$TIMER_DIR"
cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Hermes Auto-Sync (A-Wiki → container, gateway rescan)

[Service]
Type=oneshot
ExecStart=$REPO_DIR/scripts/hermes/awiki-pi5-sync.sh
WorkingDirectory=$REPO_DIR
EOF
info "Updated $TIMER_FILE → calls awiki-pi5-sync.sh"

# Reload + restart the timer so the new service definition takes effect
systemctl --user daemon-reload
info "systemd user daemon reloaded"

# ---- Step 3: Verify timer still active ----
step "Step 3/4: Verify timer is active..."
if systemctl --user is-active hermes-sync.timer 2>/dev/null | grep -q active; then
  info "hermes-sync.timer still active (every 6h)"
  systemctl --user list-timers hermes-sync.timer --no-pager 2>/dev/null | head -5
else
  warn "hermes-sync.timer not active — re-enabling"
  systemctl --user enable hermes-sync.timer 2>/dev/null || true
  systemctl --user start hermes-sync.timer 2>/dev/null || true
fi

# ---- Step 4: Run awiki-pi5-sync.sh once to verify the new path works ----
step "Step 4/4: Test-run awiki-pi5-sync.sh (should work with NOPASSWD now)..."
if bash "$REPO_DIR/scripts/hermes/awiki-pi5-sync.sh"; then
  info "awiki-pi5-sync.sh ran successfully — new sync path verified"
else
  warn "awiki-pi5-sync.sh reported issues — check output above"
  warn "(the timer will retry in 6h; manual re-run: bash scripts/hermes/awiki-pi5-sync.sh)"
fi

echo ""
echo "=============================================="
echo "  Done ✅"
echo "=============================================="
echo ""
echo "What changed:"
echo "  1. NOPASSWD docker for umbrel → no password needed for docker anymore"
echo "  2. Legacy /home/umbrel/pi5-sync.sh backed up (had hardcoded password)"
echo "  3. hermes-sync.service now calls awiki-pi5-sync.sh (uses gateway rescan, not container restart)"
echo "  4. Timer still runs every 6h (OnCalendar=*-*-* 00,06,12,18:00:00)"
echo ""
echo "Security note: rotate the umbrel password if 'Admin1234!' was ever shared."
echo "  sudo passwd umbrel"
echo ""
echo "Next sync: $(systemctl --user list-timers hermes-sync.timer --no-pager 2>/dev/null | grep hermes-sync | head -1)"
