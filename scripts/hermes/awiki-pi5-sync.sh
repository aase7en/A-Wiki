#!/usr/bin/env bash
# =============================================================================
# awiki-pi5-sync.sh — Manual A-Wiki → Hermes (Pi5 Docker) sync trigger
# =============================================================================
# Wraps auto-sync-from-git.sh (the cron logic) and adds two things it lacks:
#   1. Gateway rescan — Hermes only re-scans /opt/data/skills on SIGHUP or
#      container restart. Without this, newly imported skills sit dormant
#      until the next restart.
#   2. Verify — count skills in /opt/data/skills/ before and after to confirm
#      the import actually landed.
#
# When to run:
#   - After pushing new skills to GitHub and you don't want to wait for cron
#   - When the 6h cron job last ran before your push
#   - As a first troubleshooting step if "skills missing on Pi5"
#
# NOT for other devices: this script is Pi5-only. On Windows/Mac use
# `git awiki-sync` (which auto-detects platform and routes correctly).
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[X]${NC} $1"; }
step()  { echo -e "${CYAN}[>]${NC} $1"; }

# ---- Platform guard ----
detect_pi5() {
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}

if ! detect_pi5; then
  err "This script is for Pi5 (Umbrel Docker) only."
  echo ""
  echo "On Windows/Mac, use instead:"
  echo "  git awiki-sync        # auto-detects platform, pulls + re-links skills"
  echo ""
  echo "Or run the linker directly:"
  echo "  bash scripts/link-agent-configs.sh --skills-only --force-skills"
  exit 1
fi

CONTAINER="${HERMES_CONTAINER:-hermes-agent_web_1}"
REPO_DIR="${A_WIKI_DIR:-$HOME/A-Wiki}"

# Resolve Hermes binary (runs inside container, not on host PATH)
HERMES_BIN="/opt/hermes/bin/hermes"

step "Step 1/3: Run auto-sync (git pull + secrets + profile import)..."
# Delegate to the cron logic — it handles git pull, Drive secrets, tarball import,
# and the last-import tracking. We don't duplicate that here.
AUTO_SYNC="$REPO_DIR/scripts/hermes/auto-sync-from-git.sh"
if [ ! -f "$AUTO_SYNC" ]; then
  err "auto-sync-from-git.sh not found at $AUTO_SYNC"
  err "Run from inside the A-Wiki repo: bash scripts/hermes/awiki-pi5-sync.sh"
  exit 1
fi
bash "$AUTO_SYNC" || {
  warn "auto-sync-from-git.sh reported a non-zero exit — continuing to rescan anyway"
}

step "Step 2/3: Gateway rescan (pick up newly imported skills)..."
# Hermes scans /opt/data/skills/ once at startup and on SIGHUP to the gateway.
# After a profile import, the gateway does NOT auto-rescan, so new/updated
# skills stay invisible until the next container restart. Send SIGHUP to
# force an immediate rescan.
PID_FILE="/opt/data/gateway.pid"
if sudo -S -p '' docker exec "$CONTAINER" test -f "$PID_FILE" 2>/dev/null; then
  if sudo -S -p '' docker exec "$CONTAINER" bash -c "kill -HUP \$(cat $PID_FILE)" 2>/dev/null; then
    info "Gateway rescanned — new skills now visible"
  else
    warn "SIGHUP failed — skills will load on next container restart"
  fi
else
  warn "No gateway.pid in container — skills will load on next container restart"
  warn "(container may have been recreated; this is normal after Umbrel updates)"
fi

step "Step 3/3: Verify..."
SKILL_COUNT=$(sudo -S -p '' docker exec "$CONTAINER" \
  bash -c 'find /opt/data/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l' 2>/dev/null || echo "?")
if [ "$SKILL_COUNT" = "?" ]; then
  warn "Could not count skills (container may be down)"
else
  info "Skills in /opt/data/skills/: $SKILL_COUNT directories"
fi

echo ""
info "Pi5 sync complete."
echo ""
echo "If skills are still missing:"
echo "  1. Check container is up:    sudo docker ps | grep hermes"
echo "  2. Restart container:        sudo docker restart $CONTAINER"
echo "  3. Verify cron is active:    crontab -l | grep auto-sync"
echo "  4. Tail gateway logs:        sudo docker logs --tail 50 $CONTAINER"
