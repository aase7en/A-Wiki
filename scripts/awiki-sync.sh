#!/usr/bin/env bash
# =============================================================================
# awiki-sync.sh — One-command A-Wiki sync (git pull + skill re-link)
# =============================================================================
# Registered as `git awiki-sync` by scripts/install-git-hooks.sh.
# Auto-detects platform and routes to the right mechanism:
#
#   Windows / Mac (native agents):
#     git pull --ff-only
#     bash scripts/link-agent-configs.sh --skills-only --force-skills
#     bash scripts/link-agent-configs.sh --status
#
#   Pi5 (Hermes Docker container):
#     git pull --ff-only
#     bash scripts/hermes/awiki-pi5-sync.sh   (docker cp + gateway rescan)
#
# Usage:
#   git awiki-sync              # full sync for current platform
#   bash scripts/awiki-sync.sh  # same thing, without the alias
#
# The post-merge hook (scripts/hooks/post_merge_relink.sh) does the link half
# automatically after every `git pull`. This command is for when you want to
# pull AND see status output, or trigger a force-skills re-link explicitly.
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[X]${NC} $1"; }
step()  { echo -e "${CYAN}[>]${NC} $1"; }

# ---- Platform detection (same logic as scripts/hermes/sync-all.sh) ----
detect_platform() {
  case "$(uname -s 2>/dev/null || echo 'Unknown')" in
    Darwin)  echo "macos" ;;
    Linux)   echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)       echo "unknown" ;;
  esac
}

detect_pi5() {
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}

PLATFORM=$(detect_platform)
IS_PI5=false
detect_pi5 && IS_PI5=true

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

step "Step 1/3: git pull..."
if git pull --ff-only origin main 2>&1; then
  info "Pull OK ($(git rev-parse --short HEAD))"
else
  warn "git pull reported issues — continuing anyway (check output above)"
fi

step "Step 2/3: Re-link skills..."
if [ "$IS_PI5" = "true" ]; then
  # Pi5: Hermes runs in Docker — host symlinks don't reach the container.
  # Delegate to the Docker-aware wrapper (docker cp + profile import + rescan).
  info "Pi5 detected — using Docker-aware sync"
  bash "$REPO_ROOT/scripts/hermes/awiki-pi5-sync.sh"
else
  # Windows / Mac: native agent homes — re-link skills as symlinks/junctions
  # pointing back into this repo (single source of truth).
  info "$PLATFORM detected — re-linking native agent skills"
  bash "$REPO_ROOT/scripts/link-agent-configs.sh" --skills-only --force-skills
fi

step "Step 3/3: Status..."
if [ "$IS_PI5" = "true" ]; then
  # Pi5 status is verified inside awiki-pi5-sync.sh (skill count in container)
  info "See Pi5 sync output above for skill count"
else
  bash "$REPO_ROOT/scripts/link-agent-configs.sh" --status || true
fi

echo ""
info "Sync complete."
