#!/usr/bin/env bash
# =============================================================================
# Hermes Secure Sync — Cross-Platform (Mac / Windows / Linux / Pi5)
# =============================================================================
# PUBLIC (GitHub) + PRIVATE (Google Drive or SCP) — two-layer sync.
# Auto-detects OS and picks the right transport for secrets.
#
# Usage:
#   bash scripts/hermes/sync-all.sh              # pull mode (any device)
#   bash scripts/hermes/sync-all.sh --push       # push mode (Mac -> Drive+Git)
#   bash scripts/hermes/sync-all.sh --dry-run    # preview only
#   bash scripts/hermes/sync-all.sh --to-pi5     # push secrets directly to Pi5 via SCP
# =============================================================================
set -euo pipefail

# ---- PATH fix (macOS broken PATH compatibility) ----
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:$PATH"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[X]${NC} $1"; exit 1; }
step()  { echo -e "${CYAN}[>]${NC} $1"; }

# ---- Platform Detection ----
detect_platform() {
  case "$(uname -s 2>/dev/null || echo 'Unknown')" in
    Darwin)  echo "macos" ;;
    Linux)   echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)       echo "unknown" ;;
  esac
}

detect_pi5() {
  # Check if this is the Raspberry Pi 5 running Umbrel
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}

PLATFORM=$(detect_platform)
IS_PI5=false
detect_pi5 && IS_PI5=true

# ---- Flags ----
DRY_RUN=false; PUSH_MODE=false; TO_PI5=false
for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
  [[ "$arg" == "--push" ]] && PUSH_MODE=true
  [[ "$arg" == "--to-pi5" ]] && TO_PI5=true
done

# ---- Paths ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
A_WIKI_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROFILE="${HERMES_PROFILE:-tech_and_ai_architect}"

# Resolve Hermes binary
HERMES_BIN=""
for candidate in \
  "$HOME/.hermes/hermes-agent/venv/bin/hermes" \
  "/opt/hermes/bin/hermes" \
  "hermes"; do
  [ -x "$candidate" ] && { HERMES_BIN="$candidate"; break; }
done

# Resolve Google Drive path (cross-platform)
resolve_drive_path() {
  # 1. Environment variable (explicit override)
  [ -n "${A_WIKI_DRIVE_PATH:-}" ] && [ -d "$A_WIKI_DRIVE_PATH" ] && { echo "$A_WIKI_DRIVE_PATH"; return; }

  # 2. A-Wiki drive/ symlink (macOS/Linux convention)
  for d in "$A_WIKI_DIR/drive" "$HOME/Desktop/A-Wiki/drive" "$HOME/A-Wiki/drive"; do
    [ -d "$d" ] && [ -d "$d/hermes-sync" ] && { echo "$d"; return; }
  done

  # 3. macOS Google Drive paths
  if [ "$PLATFORM" = "macos" ]; then
    for d in "$HOME/Library/CloudStorage/GoogleDrive-"*/"My Drive/A-Wiki-Data"; do
      [ -d "$d" ] && { echo "$d"; return; }
    done
  fi

  # 4. Windows Google Drive paths
  if [ "$PLATFORM" = "windows" ]; then
    for d in "G:/My Drive/A-Wiki-Data" "C:/Users/$USER/Google Drive/A-Wiki-Data"; do
      [ -d "$d" ] && { echo "$d"; return; }
    done
  fi

  # 5. Linux (rclone mount or similar)
  if [ "$PLATFORM" = "linux" ]; then
    for d in "$HOME/GoogleDrive/A-Wiki-Data" "/mnt/gdrive/A-Wiki-Data"; do
      [ -d "$d" ] && { echo "$d"; return; }
    done
  fi

  return 1
}

echo "============================================"
echo "  Hermes Secure Sync"
echo "  Platform: $PLATFORM | Pi5: $IS_PI5"
echo "  Profile:  $PROFILE"
echo "  A-Wiki:   $A_WIKI_DIR"
$DRY_RUN && echo "  Mode:     DRY RUN"
$PUSH_MODE && echo "  Mode:     PUSH"
$TO_PI5 && echo "  Mode:     SCP to Pi5"
echo "============================================"

# ================================================================
# PUSH MODE (Mac → Drive + Git)
# ================================================================
if $PUSH_MODE; then

  step "Step 1/4: Push secrets to Google Drive..."
  DRIVE_DIR=$(resolve_drive_path) || warn "Google Drive not found — secrets NOT synced"

  if [ -n "${DRIVE_DIR:-}" ]; then
    SYNC_DIR="$DRIVE_DIR/hermes-sync"
    mkdir -p "$SYNC_DIR/config" "$SYNC_DIR/memories"

    PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
    MEM_DIR="$PROFILE_DIR/memories"

    for item in \
      "$PROFILE_DIR/.env:$SYNC_DIR/config/.env:.env" \
      "$PROFILE_DIR/auth.json:$SYNC_DIR/config/auth.json:auth.json" \
      "$PROFILE_DIR/SOUL.md:$SYNC_DIR/config/SOUL.md:SOUL.md" \
      "$MEM_DIR/MEMORY.md:$SYNC_DIR/memories/MEMORY.md:MEMORY.md" \
      "$MEM_DIR/USER.md:$SYNC_DIR/memories/USER.md:USER.md"; do

      IFS=':' read -r src dst label <<< "$item"
      if [ -f "$src" ]; then
        if $DRY_RUN; then
          info "DRY: $label -> $dst"
        else
          [ -f "$dst" ] && cp "$dst" "${dst}.bak"
          cp "$src" "$dst"
          chmod 600 "$dst" 2>/dev/null || true
          info "$label -> $dst"
        fi
      else
        warn "SKIP $label (not found: $src)"
      fi
    done
  fi

  step "Step 2/4: Push to Pi5 via SCP..."
  if $TO_PI5 || $IS_PI5; then
    warn "Already on Pi5 or target is Pi5 — skip SCP"
  else
    if command -v ssh >/dev/null 2>&1; then
      PI5_HOST="${PI5_HOST:-umbrel.local}"
      if ssh -o ConnectTimeout=3 -o BatchMode=yes "$PI5_HOST" echo ok 2>/dev/null; then
        info "Pi5 reachable at $PI5_HOST"
        if ! $DRY_RUN; then
          # Copy secrets directly to Pi5
          scp "$PROFILE_DIR/.env"      "$PI5_HOST:/tmp/hermes-secrets/.env"      2>/dev/null || warn "scp .env failed"
          scp "$PROFILE_DIR/auth.json" "$PI5_HOST:/tmp/hermes-secrets/auth.json" 2>/dev/null || warn "scp auth.json failed"
          scp "$PROFILE_DIR/SOUL.md"   "$PI5_HOST:/tmp/hermes-secrets/SOUL.md"   2>/dev/null || warn "scp SOUL.md failed"
          scp "$MEM_DIR/MEMORY.md"     "$PI5_HOST:/tmp/hermes-secrets/MEMORY.md" 2>/dev/null || warn "scp MEMORY.md failed"
          scp "$MEM_DIR/USER.md"       "$PI5_HOST:/tmp/hermes-secrets/USER.md"   2>/dev/null || warn "scp USER.md failed"
          # Trigger Pi5 import
          ssh "$PI5_HOST" "mkdir -p ~/hermes-secrets && cp /tmp/hermes-secrets/* ~/hermes-secrets/ && echo 'Secrets ready at ~/hermes-secrets/'" 2>/dev/null || warn "Pi5 copy failed"
          info "Secrets pushed to Pi5"
        else
          info "DRY: scp secrets -> $PI5_HOST"
        fi
      else
        warn "Pi5 not reachable — skip SCP (secrets are in Google Drive)"
      fi
    else
      warn "SSH not available — skip SCP"
    fi
  fi

  step "Step 3/4: Export Hermes profile package..."
  if [ -x "$HERMES_BIN" ]; then
    if $DRY_RUN; then
      info "DRY: hermes profile export"
    else
      bash "$SCRIPT_DIR/export-macbook-config.sh" "$PROFILE" 2>&1 || warn "Export skipped"
    fi
  else
    warn "Hermes binary not found — skip export"
  fi

  step "Step 4/4: Git commit + push..."
  if $DRY_RUN; then
    info "DRY: git add + commit + push"
  else
    cd "$A_WIKI_DIR"
    git add scripts/hermes/ docs/runbooks/hermes-multi-device.md AGENTS.md 2>/dev/null || true
    if ! git diff --cached --quiet 2>/dev/null; then
      git commit -m "chore(hermes): sync config + secure sync scripts" 2>&1
      git push 2>&1
      info "Pushed to GitHub"
    else
      info "Git: nothing to commit"
    fi
  fi

  echo ""
  info "PUSH COMPLETE"
  echo "  GitHub:   https://github.com/aase7en/A-Wiki"
  echo "  Drive:    $DRIVE_DIR/hermes-sync/"
  echo "  Pi5:      SCP to $PI5_HOST"

# ================================================================
# PULL MODE (any device: Git + Drive/SCP → local)
# ================================================================
else

  step "Step 1/3: Git pull latest..."
  cd "$A_WIKI_DIR"
  BEFORE=$(git rev-parse HEAD 2>/dev/null || echo "")
  git pull --ff-only 2>&1 || warn "git pull failed (check network)"
  AFTER=$(git rev-parse HEAD 2>/dev/null || echo "")
  if [ "$BEFORE" != "$AFTER" ] && [ -n "$BEFORE" ]; then
    info "Git updated: ${BEFORE:0:7} -> ${AFTER:0:7}"
  else
    info "Git: up to date"
  fi

  step "Step 2/3: Pull secrets..."

  DRIVE_DIR=$(resolve_drive_path) || true
  PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
  MEM_DIR="$PROFILE_DIR/memories"

  if [ -n "${DRIVE_DIR:-}" ]; then
    # Drive is available — pull from there
    SYNC_DIR="$DRIVE_DIR/hermes-sync"
    info "Drive found: pulling from $SYNC_DIR"

    for item in \
      "$SYNC_DIR/config/.env:$PROFILE_DIR/.env:.env" \
      "$SYNC_DIR/config/auth.json:$PROFILE_DIR/auth.json:auth.json" \
      "$SYNC_DIR/config/SOUL.md:$PROFILE_DIR/SOUL.md:SOUL.md" \
      "$SYNC_DIR/memories/MEMORY.md:$MEM_DIR/MEMORY.md:MEMORY.md" \
      "$SYNC_DIR/memories/USER.md:$MEM_DIR/USER.md:USER.md"; do

      IFS=':' read -r src dst label <<< "$item"
      if [ -f "$src" ]; then
        if $DRY_RUN; then
          info "DRY: $label <- $src"
        else
          mkdir -p "$(dirname "$dst")"
          [ -f "$dst" ] && cp "$dst" "${dst}.bak"
          cp "$src" "$dst"
          chmod 600 "$dst" 2>/dev/null || true
          info "$label <- $src"
        fi
      else
        warn "$label: not in Drive"
      fi
    done
  else
    warn "Google Drive not mounted on this device"
    warn "Secrets not updated. Run on Mac: sync-all.sh --push --to-pi5"
    warn "Or set A_WIKI_DRIVE_PATH=/path/to/GoogleDrive/A-Wiki-Data"
  fi

  # Pi5 Docker import
  if $IS_PI5; then
    step "Step 3/3: Pi5 Docker container import..."
    CONTAINER="${HERMES_CONTAINER:-hermes-agent_web_1}"
    if $DRY_RUN; then
      info "DRY: docker cp + import"
    else
      if command -v docker >/dev/null 2>&1; then
        docker cp "$PROFILE_DIR/.env"       "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/.env"      2>/dev/null || true
        docker cp "$PROFILE_DIR/auth.json"  "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/auth.json" 2>/dev/null || true
        docker cp "$PROFILE_DIR/SOUL.md"    "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/SOUL.md"   2>/dev/null || true
        docker cp "$MEM_DIR/MEMORY.md"      "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/memories/MEMORY.md" 2>/dev/null || true
        docker cp "$MEM_DIR/USER.md"        "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/memories/USER.md"   2>/dev/null || true
        info "Pi5 Docker secrets updated"
      else
        warn "Docker not found"
      fi
    fi
  else
    # Import Hermes profile if new package available
    step "Step 3/3: Import profile package..."
    LATEST=$(ls -t "$SCRIPT_DIR"/hermes-export-*.tar.gz 2>/dev/null | head -1 || echo "")
    if [ -n "$LATEST" ] && [ -x "$HERMES_BIN" ]; then
      if $DRY_RUN; then
        info "DRY: hermes profile import $LATEST"
      else
        "$HERMES_BIN" profile import "$LATEST" 2>&1 && info "Profile imported" || warn "Import skipped"
      fi
    fi
  fi

  echo ""
  info "SYNC COMPLETE"
  echo "  Secrets: $([ -f "$PROFILE_DIR/.env" ] && echo 'OK' || echo 'MISSING')"
  echo "  Profile: $PROFILE"
fi
