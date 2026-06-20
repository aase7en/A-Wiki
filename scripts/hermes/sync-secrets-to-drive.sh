#!/usr/bin/env bash
# Hermes Secure Sync → Google Drive (PUSH) — Cross-Platform
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

# Cross-platform Drive resolution (same as sync-all.sh)
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

DRIVE_DIR=$(resolve_drive_path) || { warn "Drive not found — set A_WIKI_DRIVE_PATH"; exit 0; }
SYNC="$DRIVE_DIR/hermes-sync"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "=== Hermes -> Drive (PUSH) ==="
echo "Profile: $PROFILE | Target: $SYNC"
$DRY_RUN && echo "Mode: DRY RUN"

mkdir -p "$SYNC/config" "$SYNC/memories"

for item in   "$PROFILE_DIR/.env:$SYNC/config/.env:.env"   "$PROFILE_DIR/auth.json:$SYNC/config/auth.json:auth.json"   "$PROFILE_DIR/SOUL.md:$SYNC/config/SOUL.md:SOUL.md"   "$MEM_DIR/MEMORY.md:$SYNC/memories/MEMORY.md:MEMORY.md"   "$MEM_DIR/USER.md:$SYNC/memories/USER.md:USER.md"; do

  IFS=':' read -r src dst label <<< "$item"
  [ -f "$src" ] || { warn "SKIP $label"; continue; }
  sz=$(wc -c < "$src" 2>/dev/null || echo 0)
  if $DRY_RUN; then
    info "DRY: $label -> $dst ($sz B)"
  else
    [ -f "$dst" ] && cp "$dst" "${dst}.bak-${TIMESTAMP}"
    cp "$src" "$dst"
    chmod 600 "$dst" 2>/dev/null || true
    info "$label -> $dst ($sz B)"
  fi
done

# A-Wiki root .env -> global.env
for ae in "$A_WIKI_DIR/.env" "$HOME/Desktop/A-Wiki/.env"; do
  [ -f "$ae" ] && { src="$ae"; break; }
done
if [ -n "${src:-}" ]; then
  if $DRY_RUN; then info "DRY: global.env -> $SYNC/global.env"; else
    cp "$src" "$SYNC/global.env"; chmod 600 "$SYNC/global.env"
    info "global.env -> $SYNC/global.env"
  fi
fi

$DRY_RUN || info "DONE!"
