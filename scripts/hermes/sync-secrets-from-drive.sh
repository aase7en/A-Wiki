#!/usr/bin/env bash
# Hermes Secure Sync <- Google Drive (PULL) — Cross-Platform
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:$PATH"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }

DRY_RUN=false; [[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

PROFILE="${HERMES_PROFILE:-tech_and_ai_architect}"
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
MEM_DIR="$PROFILE_DIR/memories"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
A_WIKI_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Cross-platform Drive resolution
resolve_drive_path() {
  [ -n "${A_WIKI_DRIVE_PATH:-}" ] && [ -d "$A_WIKI_DRIVE_PATH" ] && { echo "$A_WIKI_DRIVE_PATH"; return; }
  for d in "$A_WIKI_DIR/drive" "$HOME/Desktop/A-Wiki/drive" "$HOME/A-Wiki/drive"; do
    [ -d "$d" ] && { echo "$d"; return; }
  done
  case "$(uname -s)" in
    Darwin)
      for d in "$HOME/Library/CloudStorage/GoogleDrive-"*/"My Drive/A-Wiki-Data"; do
        [ -d "$d" ] && { echo "$d"; return; }
      done ;;
    MINGW*|MSYS*|CYGWIN*)
      for d in "G:/My Drive/A-Wiki-Data" "$USERPROFILE/Google Drive/A-Wiki-Data"; do
        [ -d "$d" ] && { echo "$d"; return; }
      done ;;
  esac
  return 1
}

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

DRIVE_DIR=$(resolve_drive_path) || { warn "Drive not found."; warn "Use: sync-all.sh --push --to-pi5 (from Mac) or set A_WIKI_DRIVE_PATH"; exit 0; }
SYNC="$DRIVE_DIR/hermes-sync"

echo "=== Drive -> Hermes (PULL) ==="
echo "Profile: $PROFILE | Source: $SYNC"
$DRY_RUN && echo "Mode: DRY RUN"

[ -d "$SYNC/config" ] || { warn "No hermes-sync/ in Drive. Run sync-all.sh --push on Mac first."; exit 0; }

for item in   "$SYNC/config/.env:$PROFILE_DIR/.env:.env"   "$SYNC/config/auth.json:$PROFILE_DIR/auth.json:auth.json"   "$SYNC/config/SOUL.md:$PROFILE_DIR/SOUL.md:SOUL.md"   "$SYNC/memories/MEMORY.md:$MEM_DIR/MEMORY.md:MEMORY.md"   "$SYNC/memories/USER.md:$MEM_DIR/USER.md:USER.md"; do

  IFS=':' read -r src dst label <<< "$item"
  [ -f "$src" ] || { warn "SKIP $label (not in Drive)"; continue; }
  sz=$(wc -c < "$src" 2>/dev/null || echo 0)
  if $DRY_RUN; then
    info "DRY: $label <- $src ($sz B)"
  else
    mkdir -p "$(dirname "$dst")"
    [ -f "$dst" ] && cp "$dst" "${dst}.bak-${TIMESTAMP}"
    cp "$src" "$dst"
    chmod 600 "$dst" 2>/dev/null || true
    info "$label <- $src ($sz B)"
  fi
done

# A-Wiki .env
for ae in "$A_WIKI_DIR/.env" "$HOME/Desktop/A-Wiki/.env"; do
  [ -d "$(dirname "$ae")" ] && { A_ENV="$ae"; break; }
done
if [ -n "${A_ENV:-}" ] && [ -f "$SYNC/global.env" ]; then
  if $DRY_RUN; then info "DRY: A-Wiki .env <- $SYNC/global.env"; else
    [ -f "$A_ENV" ] && cp "$A_ENV" "${A_ENV}.bak-${TIMESTAMP}"
    cp "$SYNC/global.env" "$A_ENV"
    chmod 600 "$A_ENV" 2>/dev/null || true
    info "A-Wiki .env <- $SYNC/global.env"
  fi
fi

# Pi5 Docker import
if hostname 2>/dev/null | grep -qi "umbrel\|raspberry"; then
  CONTAINER="${HERMES_CONTAINER:-hermes-agent_web_1}"
  if command -v docker >/dev/null 2>&1 && ! $DRY_RUN; then
    docker cp "$PROFILE_DIR/.env"      "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/.env"      2>/dev/null || true
    docker cp "$PROFILE_DIR/auth.json" "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/auth.json" 2>/dev/null || true
    docker cp "$PROFILE_DIR/SOUL.md"   "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/SOUL.md"   2>/dev/null || true
    docker cp "$MEM_DIR/MEMORY.md"     "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/memories/MEMORY.md" 2>/dev/null || true
    docker cp "$MEM_DIR/USER.md"       "$CONTAINER:/home/node/.hermes/profiles/$PROFILE/memories/USER.md"   2>/dev/null || true
    info "Pi5 Docker container updated"
  fi
fi

$DRY_RUN || info "DONE!"
