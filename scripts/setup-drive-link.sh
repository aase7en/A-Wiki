#!/usr/bin/env bash
# =============================================================================
# setup-drive-link.sh — Link A-Wiki/drive/ → personal data storage
# =============================================================================
# Creates A-Wiki/drive/ symlink pointing to the user's Google Drive (or other
# personal storage) so all scripts and editors can use ./drive/... paths.
#
# Each person who clones A-Wiki runs this ONCE to configure their own path.
# The symlink is never committed to git (.gitignore has "drive" and ".drive-path")
#
# Pattern: same as link-my-skills.sh but INBOUND — repo accesses user's storage.
#
# Usage:
#   bash scripts/setup-drive-link.sh                          # auto-detect Google Drive
#   bash scripts/setup-drive-link.sh --path "L:/My Drive/A-Wiki-Data"  # explicit path
#   bash scripts/setup-drive-link.sh --status                # show current link info
#   bash scripts/setup-drive-link.sh --unlink                # remove drive/ link
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LINK_TARGET="$REPO_ROOT/drive"
DRIVE_PATH_FILE="$REPO_ROOT/.drive-path"

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${RESET}"; }
warn() { echo -e "${YELLOW}⚠️  $*${RESET}"; }
err()  { echo -e "${RED}❌ $*${RESET}"; }

# ── Auto-detect Google Drive path per OS ──────────────────────────────────────
detect_drive_path() {
    local candidates=()

    if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || -n "${WINDIR:-}" ]]; then
        # Windows (Git Bash / MSYS2)
        # Default: Drive Desktop mounts to L: (user-configured)
        candidates+=("L:/My Drive/A-Wiki-Data")
        # Fallback: check common Windows Google Drive paths
        [[ -n "${USERPROFILE:-}" ]] && {
            candidates+=("$USERPROFILE/Google Drive/My Drive/A-Wiki-Data")
            candidates+=("$USERPROFILE/My Drive/A-Wiki-Data")
        }

    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS — Google Drive Desktop mounts under ~/Library/CloudStorage/
        # Glob for any Google account
        while IFS= read -r -d '' p; do
            candidates+=("$p")
        done < <(find "$HOME/Library/CloudStorage" -maxdepth 2 \
                     -name "A-Wiki-Data" -type d -print0 2>/dev/null || true)
        candidates+=("$HOME/Google Drive/My Drive/A-Wiki-Data")

    else
        # Linux / other
        candidates+=("$HOME/Google Drive/My Drive/A-Wiki-Data")
        candidates+=("$HOME/GoogleDrive/My Drive/A-Wiki-Data")
    fi

    for p in "${candidates[@]}"; do
        [[ -d "$p" ]] && echo "$p" && return 0
    done
    return 1
}

# ── Initialize folder structure inside Drive ──────────────────────────────────
init_drive_structure() {
    local drive="$1"
    mkdir -p "$drive/waste-reports"
    mkdir -p "$drive/personal-tools/userscripts"
    mkdir -p "$drive/ocr-feedback"
    mkdir -p "$drive/individual-tasks"
    echo "   📁 Drive structure initialized:"
    echo "      waste-reports/       ← raw photos + OCR results"
    echo "      personal-tools/      ← scripts for personal use (userscripts, etc.)"
    echo "      ocr-feedback/        ← OCR correction data (learning loop)"
    echo "      individual-tasks/    ← per-project data + configs"
}

# ── Show status ───────────────────────────────────────────────────────────────
cmd_status() {
    echo ""
    echo "A-Wiki Drive Link Status"
    echo "========================"
    if [[ -L "$LINK_TARGET" ]]; then
        local dest
        dest="$(readlink "$LINK_TARGET")"
        if [[ -d "$dest" ]]; then
            ok "drive/ → $dest  (symlink, active)"
        else
            warn "drive/ → $dest  (symlink, TARGET MISSING — mount your Drive)"
        fi
    elif [[ -d "$LINK_TARGET" ]]; then
        warn "drive/ is a real directory (not a symlink) — run --unlink then setup again"
    elif [[ -f "$DRIVE_PATH_FILE" ]]; then
        local p
        p="$(cat "$DRIVE_PATH_FILE")"
        if [[ -d "$p" ]]; then
            ok ".drive-path → $p  (config fallback, active)"
        else
            warn ".drive-path → $p  (config fallback, TARGET MISSING)"
        fi
    else
        warn "Not configured — run: bash scripts/setup-drive-link.sh"
    fi
    echo ""
}

# ── Remove link ───────────────────────────────────────────────────────────────
cmd_unlink() {
    [[ -L "$LINK_TARGET" ]] && rm "$LINK_TARGET" && ok "Removed drive/ symlink"
    [[ -f "$DRIVE_PATH_FILE" ]] && rm "$DRIVE_PATH_FILE" && ok "Removed .drive-path"
    echo "drive/ link cleared. Run setup again to relink."
}

# ── Main setup ────────────────────────────────────────────────────────────────
cmd_setup() {
    local explicit_path="${1:-}"
    local drive_path=""

    echo ""
    echo "A-Wiki Drive Link Setup"
    echo "======================="

    if [[ -n "$explicit_path" ]]; then
        drive_path="$explicit_path"
        echo "Using specified path: $drive_path"
        if [[ ! -d "$drive_path" ]]; then
            warn "Path does not exist yet — creating it..."
            mkdir -p "$drive_path"
        fi
    else
        echo "Auto-detecting Google Drive..."
        if drive_path="$(detect_drive_path)"; then
            echo "Found: $drive_path"
        else
            warn "Google Drive A-Wiki-Data folder not found."
            echo ""
            echo "Options:"
            echo "  1. Mount Google Drive Desktop, then create folder:"
            echo "        L:\\My Drive\\A-Wiki-Data          (Windows)"
            echo "        ~/Library/CloudStorage/...        (Mac)"
            echo "  2. Specify path manually:"
            echo "        bash scripts/setup-drive-link.sh --path '/your/path'"
            echo "  3. Using fallback local folder: ~/.a-wiki-data"
            echo ""
            drive_path="$HOME/.a-wiki-data"
            mkdir -p "$drive_path"
            warn "Fallback: $drive_path (not synced to cloud)"
        fi
    fi

    # Remove old link/config
    [[ -L "$LINK_TARGET" ]] && rm "$LINK_TARGET"
    [[ -d "$LINK_TARGET" && ! -L "$LINK_TARGET" ]] && {
        warn "drive/ is a real directory, not touching it. Remove it manually if needed."
    }
    [[ -f "$DRIVE_PATH_FILE" ]] && rm "$DRIVE_PATH_FILE"

    # Try symlink first
    echo ""
    if ln -s "$drive_path" "$LINK_TARGET" 2>/dev/null; then
        ok "drive/ → $drive_path"
    else
        # Windows may need Developer Mode or admin for symlinks
        warn "Symlink creation failed."
        echo "   This usually means Windows needs Developer Mode enabled, or run as admin."
        echo "   Using .drive-path config file as fallback..."
        echo "$drive_path" > "$DRIVE_PATH_FILE"
        ok ".drive-path → $drive_path  (scripts will read this automatically)"
    fi

    # Init folder structure
    echo ""
    init_drive_structure "$drive_path"

    echo ""
    ok "Setup complete!"
    echo "   Use ./drive/ (or A-Wiki/drive/) to access your personal storage."
    echo "   The drive/ link is in .gitignore — only you see it locally."
    echo ""
    echo "Next step: backup your userscript"
    echo "   cp scripts/userscripts/waste-form-ocr-fill.user.js drive/personal-tools/userscripts/"
}

# ── Entrypoint ────────────────────────────────────────────────────────────────
case "${1:-}" in
    --status)
        cmd_status
        ;;
    --unlink)
        cmd_unlink
        ;;
    --path)
        [[ -z "${2:-}" ]] && { err "Missing path argument. Usage: --path '/your/path'"; exit 1; }
        cmd_setup "$2"
        ;;
    "")
        cmd_setup ""
        ;;
    *)
        echo "Usage: bash scripts/setup-drive-link.sh [--path PATH | --status | --unlink]"
        exit 1
        ;;
esac
