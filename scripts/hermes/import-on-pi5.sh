#!/bin/bash
# =============================================================================
# Hermes Config Import — Run on Raspberry Pi 5
# =============================================================================
# This script imports the Hermes profile exported from MacBook.
# 
# Prerequisites:
#   1. Hermes Agent installed on Pi5
#   2. Export package transferred to Pi5 (hermes-export-*.tar.gz)
#   3. .env and auth.json copied separately (secrets)
#
# Usage on Pi5:
#   chmod +x import-on-pi5.sh
#   ./import-on-pi5.sh [hermes-export-YYYYMMDD.tar.gz]
# =============================================================================
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }
step()  { echo -e "${CYAN}[→]${NC} $1"; }

PACKAGE="${1:-hermes-export-20260620.tar.gz}"
PROFILE="tech_and_ai_architect"
HERMES_HOME="$HOME/.hermes"

echo "============================================"
echo "  Hermes Config Import — Pi5 Restore"
echo "  Package: $PACKAGE"
echo "  Profile: $PROFILE"
echo "============================================"
echo ""

# ---- Check prerequisites ----
step "Checking prerequisites..."
command -v hermes >/dev/null 2>&1 || { err "Hermes not installed. Run: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"; exit 1; }
[ -f "$PACKAGE" ] || { err "Package '$PACKAGE' not found. Transfer it first."; exit 1; }
info "Hermes found: $(hermes version 2>/dev/null | head -1 || echo 'OK')"
info "Package found: $(du -h "$PACKAGE" | cut -f1)"

# ---- Step 1: Backup existing profile (if any) ----
step "Step 1/5: Backing up existing profile..."
if [ -d "$HERMES_HOME/profiles/$PROFILE" ]; then
  BACKUP="${PROFILE}-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
  tar -czf "$HOME/$BACKUP" -C "$HERMES_HOME/profiles" "$PROFILE" 2>/dev/null || true
  info "Backup: $HOME/$BACKUP"
else
  info "No existing profile to backup"
fi

# ---- Step 2: Extract and import profile ----
step "Step 2/5: Extracting package..."
TMPDIR="/tmp/hermes-import-$$"
mkdir -p "$TMPDIR"
tar -xzf "$PACKAGE" -C "$TMPDIR"
info "Extracted to $TMPDIR"

step "Step 3/5: Importing profile..."
# Remove existing profile first
rm -rf "$HERMES_HOME/profiles/$PROFILE" 2>/dev/null || true
# Copy the profile directory
cp -r "$TMPDIR/$PROFILE" "$HERMES_HOME/profiles/"
info "Profile copied to $HERMES_HOME/profiles/$PROFILE"

# ---- Step 3: Adjust paths for Pi5 ----
step "Step 4/5: Adjusting paths for Pi5..."
CONFIG="$HERMES_HOME/profiles/$PROFILE/config.yaml"

# Fix common Mac→Pi5 paths
if [ -f "$CONFIG" ]; then
  # Replace Mac home directory with Pi5 home
  if grep -q "/Users/" "$CONFIG" 2>/dev/null; then
    warn "Found Mac paths in config. Adjusting..."
    # Show the Mac paths
    grep "/Users/" "$CONFIG" | head -5
    echo ""
    echo "  You should manually update: hermes config set terminal.cwd /home/pi/A-Wiki"
  fi
fi

# ---- Step 4: Verify skills ----
step "Step 5/5: Verifying skills..."
SKILL_COUNT=$(find "$HERMES_HOME/profiles/$PROFILE/skills" -name "SKILL.md" 2>/dev/null | wc -l)
info "Skills imported: $SKILL_COUNT"

# ---- Summary ----
echo ""
echo "============================================"
echo "  ✅ Import Complete"
echo "============================================"
echo ""
echo "  Profile:  $PROFILE"
echo "  Skills:   $SKILL_COUNT"
echo "  Config:   $CONFIG"
echo ""
echo "  ⚠️  NEXT: Copy secrets (.env + auth.json)"
echo "     scp ~/.hermes/profiles/$PROFILE/.env pi@umbrel.local:$HERMES_HOME/profiles/$PROFILE/"
echo "     scp ~/.hermes/profiles/$PROFILE/auth.json pi@umbrel.local:$HERMES_HOME/profiles/$PROFILE/"
echo ""
echo "  Then adjust paths:"
echo "     hermes -p $PROFILE config set terminal.cwd /home/pi/A-Wiki"
echo ""
echo "  Verify:"
echo "     hermes -p $PROFILE doctor"
echo "     hermes -p $PROFILE profile show $PROFILE"
echo ""

# Cleanup
rm -rf "$TMPDIR"
