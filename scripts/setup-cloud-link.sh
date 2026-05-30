#!/usr/bin/env bash
# =============================================================================
# setup-cloud-link.sh — Multi-provider cloud-storage linker for A-Wiki
# =============================================================================
# Replaces setup-drive-link.sh (kept as shim). Sets up BOTH:
#   drive/  → <cloud provider>/A-Wiki-Data         (per-user, gitignored)
#   raw/    → drive/raw                            (relative symlink, repo-portable)
#
# Auto-detects 4 cloud providers:
#   Google Drive · iCloud Drive · Dropbox · OneDrive
# Falls back to Custom path → Local folder.
#
# Cross-platform: macOS, Linux, Windows Git Bash, WSL.
# POSIX-safe constructs only (macOS bash 3.2 compat).
#
# Usage:
#   bash scripts/setup-cloud-link.sh                 # interactive
#   bash scripts/setup-cloud-link.sh --auto          # pick first detected
#   bash scripts/setup-cloud-link.sh --provider google
#   bash scripts/setup-cloud-link.sh --path "/your/path"
#   bash scripts/setup-cloud-link.sh --status        # show current state
#   bash scripts/setup-cloud-link.sh --unlink        # remove links
#   bash scripts/setup-cloud-link.sh --drive-only    # skip raw/ setup
#   bash scripts/setup-cloud-link.sh --raw-only      # only set up raw/
#   bash scripts/setup-cloud-link.sh --migrate       # required if raw/ has content
# =============================================================================

set -eu  # NOT -o pipefail (not portable to old bash); not -e on read prompts

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRIVE_LINK="$REPO_ROOT/drive"
RAW_LINK="$REPO_ROOT/raw"
DRIVE_PATH_FILE="$REPO_ROOT/.drive-path"
DEFAULT_FOLDER="A-Wiki-Data"

# ── Colors (POSIX-safe, no ANSI if not TTY) ──────────────────────────────────
if [ -t 1 ]; then
    GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
    BLUE=$'\033[0;34m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; BLUE=''; BOLD=''; RESET=''
fi
ok()   { printf "%s✅ %s%s\n" "$GREEN" "$*" "$RESET"; }
warn() { printf "%s⚠️  %s%s\n" "$YELLOW" "$*" "$RESET"; }
err()  { printf "%s❌ %s%s\n" "$RED" "$*" "$RESET" >&2; }
info() { printf "%s%s%s\n" "$BLUE" "$*" "$RESET"; }

# ── OS detection ─────────────────────────────────────────────────────────────
# Returns one of: mac | linux | wsl | gitbash | other
detect_os() {
    case "$(uname -s 2>/dev/null || echo unknown)" in
        Darwin*) echo "mac" ;;
        Linux*)
            # WSL detection: /proc/version contains "Microsoft" or "WSL"
            if [ -r /proc/version ] && grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*) echo "gitbash" ;;
        *)
            # Fallback: check WINDIR for Git Bash without standard uname
            if [ -n "${WINDIR:-}" ]; then echo "gitbash"; else echo "other"; fi
            ;;
    esac
}

# ── Provider detection ───────────────────────────────────────────────────────
# Each detector echoes 0 or more candidate paths (one per line).
# Uses simple globbing — no bash 4+ features.

detect_google_drive() {
    local os="$1"
    case "$os" in
        mac)
            # Glob for any Google account under CloudStorage
            for d in "$HOME"/Library/CloudStorage/GoogleDrive-*/My\ Drive; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        gitbash)
            # Common Windows mount points
            for d in "L:/My Drive" "G:/My Drive" "${USERPROFILE:-}/Google Drive/My Drive" "${USERPROFILE:-}/My Drive"; do
                [ -n "$d" ] && [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        wsl)
            # WSL can see Windows Google Drive via /mnt/c/Users/...
            for d in /mnt/c/Users/*/Google\ Drive/My\ Drive /mnt/l/My\ Drive /mnt/g/My\ Drive; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        linux)
            for d in "$HOME/GoogleDrive" "$HOME/Google Drive" "$HOME/google-drive"; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
    esac
}

detect_icloud() {
    local os="$1"
    case "$os" in
        mac)
            local icloud="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
            [ -d "$icloud" ] && printf '%s\n' "$icloud"
            ;;
        gitbash)
            [ -n "${USERPROFILE:-}" ] && [ -d "$USERPROFILE/iCloudDrive" ] && printf '%s\n' "$USERPROFILE/iCloudDrive"
            ;;
    esac
}

detect_dropbox() {
    local os="$1"
    case "$os" in
        mac)
            for d in "$HOME/Library/CloudStorage/Dropbox" "$HOME/Dropbox"; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        gitbash)
            [ -n "${USERPROFILE:-}" ] && [ -d "$USERPROFILE/Dropbox" ] && printf '%s\n' "$USERPROFILE/Dropbox"
            ;;
        wsl)
            for d in /mnt/c/Users/*/Dropbox "$HOME/Dropbox"; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        linux)
            [ -d "$HOME/Dropbox" ] && printf '%s\n' "$HOME/Dropbox"
            ;;
    esac
}

detect_onedrive() {
    local os="$1"
    case "$os" in
        mac)
            for d in "$HOME"/Library/CloudStorage/OneDrive-*; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
        gitbash)
            if [ -n "${USERPROFILE:-}" ]; then
                for d in "$USERPROFILE/OneDrive" "$USERPROFILE"/OneDrive\ -\ *; do
                    [ -d "$d" ] && printf '%s\n' "$d"
                done
            fi
            ;;
        wsl)
            for d in /mnt/c/Users/*/OneDrive /mnt/c/Users/*/OneDrive\ -\ *; do
                [ -d "$d" ] && printf '%s\n' "$d"
            done
            ;;
    esac
}

# ── Symlink creation with cross-platform fallback ────────────────────────────
# create_link <target> <link_path>
#   1. Try ln -s (Unix-style)
#   2. Try PowerShell New-Item Junction (Git Bash)
#   3. Try cmd /c mklink /J (Git Bash alt)
#   4. Write .drive-path config file (universal fallback for drive/ only)
create_link() {
    local target="$1"
    local link="$2"
    local kind="$3"  # "drive" or "raw"
    local os
    os="$(detect_os)"

    # Remove old link/dir
    if [ -L "$link" ]; then rm "$link"; fi

    # Try Unix symlink first
    if ln -s "$target" "$link" 2>/dev/null; then
        printf "  symlink:   %s → %s\n" "$link" "$target"
        return 0
    fi

    # Windows fallback: junction via PowerShell
    if [ "$os" = "gitbash" ] && command -v powershell.exe >/dev/null 2>&1; then
        local win_link win_target
        win_link="$(cygpath -w "$link" 2>/dev/null || echo "$link")"
        win_target="$(cygpath -w "$target" 2>/dev/null || echo "$target")"
        if powershell.exe -NoProfile -Command \
            "New-Item -ItemType Junction -Path '$win_link' -Target '$win_target' -ErrorAction Stop" \
            >/dev/null 2>&1; then
            printf "  junction:  %s → %s\n" "$link" "$target"
            return 0
        fi
        # Try cmd /c mklink /J as alternative
        if cmd.exe /c "mklink /J \"$win_link\" \"$win_target\"" >/dev/null 2>&1; then
            printf "  mklink:    %s → %s\n" "$link" "$target"
            return 0
        fi
    fi

    # Last resort: .drive-path config (only meaningful for drive/, not raw/)
    if [ "$kind" = "drive" ]; then
        echo "$target" > "$DRIVE_PATH_FILE"
        warn "Symlink/junction failed — wrote $DRIVE_PATH_FILE (drive_path.py will resolve)"
        return 0
    fi
    err "Cannot create link $link → $target (symlink and junction both failed)"
    return 1
}

# ── Init folder structure inside drive ───────────────────────────────────────
init_drive_structure() {
    local drive="$1"
    mkdir -p "$drive/waste-reports"
    mkdir -p "$drive/personal-tools/userscripts"
    mkdir -p "$drive/ocr-feedback"
    mkdir -p "$drive/individual-tasks"
    mkdir -p "$drive/raw"
    if [ -d "$drive/.secrets" ]; then
        warn "  $drive/.secrets is a directory; replace it with a KEY=VALUE file when adding secrets"
    fi
    info "  folders ready: waste-reports/, personal-tools/, ocr-feedback/, individual-tasks/, raw/"
}

# ── Resolve current drive path (for raw/ setup that depends on drive/) ───────
resolve_drive_path() {
    if [ -L "$DRIVE_LINK" ]; then
        # readlink portable: use python3 for realpath if available
        if command -v python3 >/dev/null 2>&1; then
            python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$DRIVE_LINK"
        else
            readlink "$DRIVE_LINK"
        fi
        return 0
    fi
    if [ -f "$DRIVE_PATH_FILE" ]; then
        cat "$DRIVE_PATH_FILE"
        return 0
    fi
    return 1
}

# ── Status command ───────────────────────────────────────────────────────────
cmd_status() {
    echo ""
    echo "A-Wiki Cloud Link Status"
    echo "========================"
    echo "OS detected: $(detect_os)"
    echo ""

    # drive/
    if [ -L "$DRIVE_LINK" ]; then
        local dest
        dest="$(resolve_drive_path)"
        if [ -d "$dest" ]; then
            ok "drive/ → $dest  (symlink, active)"
        else
            warn "drive/ → $dest  (symlink, TARGET MISSING — mount your cloud drive)"
        fi
    elif [ -d "$DRIVE_LINK" ] && [ ! -L "$DRIVE_LINK" ]; then
        warn "drive/ is a real directory, not a symlink"
    elif [ -f "$DRIVE_PATH_FILE" ]; then
        local p; p="$(cat "$DRIVE_PATH_FILE")"
        if [ -d "$p" ]; then
            ok ".drive-path → $p  (config fallback, active)"
        else
            warn ".drive-path → $p  (TARGET MISSING)"
        fi
    else
        warn "drive/ not configured — run: bash scripts/setup-cloud-link.sh"
    fi

    # raw/
    if [ -L "$RAW_LINK" ]; then
        local raw_dest
        if command -v python3 >/dev/null 2>&1; then
            raw_dest="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$RAW_LINK")"
        else
            raw_dest="$(readlink "$RAW_LINK")"
        fi
        if [ -d "$raw_dest" ]; then
            ok "raw/   → $raw_dest  (symlink, active)"
        else
            warn "raw/   → $raw_dest  (symlink, TARGET MISSING)"
        fi
    elif [ -d "$RAW_LINK" ] && [ ! -L "$RAW_LINK" ]; then
        warn "raw/ is a real directory, not linked (run setup to migrate)"
    else
        warn "raw/ not configured"
    fi
    echo ""
}

# ── Unlink ───────────────────────────────────────────────────────────────────
cmd_unlink() {
    [ -L "$DRIVE_LINK" ] && rm "$DRIVE_LINK" && ok "Removed drive/ symlink"
    [ -L "$RAW_LINK" ] && rm "$RAW_LINK" && ok "Removed raw/ symlink"
    [ -f "$DRIVE_PATH_FILE" ] && rm "$DRIVE_PATH_FILE" && ok "Removed .drive-path"
    echo "Links cleared. Run setup again to relink."
}

# ── raw/ migration (handles existing real dir safely) ────────────────────────
# Returns: 0 = ok to symlink now; 1 = needs --migrate flag
migrate_raw() {
    local drive_raw="$1"
    local migrate_flag="$2"  # "1" if user passed --migrate

    # raw/ doesn't exist → ok
    if [ ! -e "$RAW_LINK" ] && [ ! -L "$RAW_LINK" ]; then
        return 0
    fi

    # raw/ is already a symlink
    if [ -L "$RAW_LINK" ]; then
        local raw_target
        if command -v python3 >/dev/null 2>&1; then
            raw_target="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$RAW_LINK")"
        else
            raw_target="$(readlink "$RAW_LINK")"
        fi
        if [ "$raw_target" = "$drive_raw" ]; then
            ok "raw/ already linked correctly"
            return 1  # signal: no-op needed
        fi
        # Wrong target — remove and recreate
        rm "$RAW_LINK"
        return 0
    fi

    # raw/ is a real directory — check if empty
    if [ -d "$RAW_LINK" ]; then
        # Count files (not just dirs) inside raw/
        local file_count
        file_count="$(find "$RAW_LINK" -type f 2>/dev/null | wc -l | tr -d ' ')"
        if [ "$file_count" -eq 0 ]; then
            info "  raw/ is empty (only empty subdirs) — safe to remove"
            # Remove all empty subdirs then raw/ itself
            find "$RAW_LINK" -depth -type d -empty -delete 2>/dev/null || true
            return 0
        fi
        # Has content — require --migrate
        if [ "$migrate_flag" != "1" ]; then
            warn "raw/ contains $file_count files NOT in drive/raw/."
            echo "  To migrate safely, re-run with --migrate flag."
            echo "  Preview of files to move:"
            find "$RAW_LINK" -type f -maxdepth 3 | head -10 | sed 's/^/    /'
            return 2  # signal: error
        fi
        # Do the migration
        info "  Migrating raw/ → drive/raw via rsync (checksum mode)..."
        if command -v rsync >/dev/null 2>&1; then
            rsync -av --checksum --remove-source-files "$RAW_LINK/" "$drive_raw/"
            find "$RAW_LINK" -depth -type d -empty -delete 2>/dev/null || true
            ok "Migration complete"
            return 0
        else
            err "rsync not found — install rsync to use --migrate"
            return 2
        fi
    fi

    return 0
}

# ── Setup drive/ link ────────────────────────────────────────────────────────
setup_drive() {
    local drive_path="$1"
    local force="${2:-0}"  # 1 = relink even if existing valid link points elsewhere

    # Idempotency: if drive/ already valid, check whether target matches
    if [ -L "$DRIVE_LINK" ]; then
        local current
        current="$(resolve_drive_path)"
        if [ "$current" = "$drive_path" ]; then
            ok "drive/ already linked correctly → $current"
            echo "$current" > "$DRIVE_PATH_FILE"
            # Still ensure folder structure exists (cheap mkdir -p)
            [ -d "$current" ] && init_drive_structure "$current"
            return 0
        fi
        # Existing link points elsewhere — refuse silent overwrite
        if [ "$force" != "1" ]; then
            warn "drive/ already linked to: $current"
            warn "Requested target differs: $drive_path"
            warn "Refusing silent relink. Use --unlink first, or --path '$drive_path' --force"
            return 0  # non-fatal — keep existing link
        fi
    fi

    if [ ! -d "$drive_path" ]; then
        info "  Creating $drive_path"
        mkdir -p "$drive_path"
    fi

    # If drive/ exists as real dir (not symlink), refuse — too risky to delete
    if [ -d "$DRIVE_LINK" ] && [ ! -L "$DRIVE_LINK" ]; then
        err "drive/ is a real directory (not symlink). Remove it manually first."
        return 1
    fi

    create_link "$drive_path" "$DRIVE_LINK" "drive"
    echo "$drive_path" > "$DRIVE_PATH_FILE"
    init_drive_structure "$drive_path"
}

# ── Setup raw/ link (depends on drive/) ──────────────────────────────────────
setup_raw() {
    local migrate_flag="$1"
    local drive_path
    drive_path="$(resolve_drive_path)" || {
        err "drive/ not set up yet — run without --raw-only first, or after setting up drive/"
        return 1
    }
    local drive_raw="$drive_path/raw"
    mkdir -p "$drive_raw"

    # Migration step
    local mig_result
    migrate_raw "$drive_raw" "$migrate_flag"
    mig_result=$?
    if [ $mig_result -eq 1 ]; then
        return 0  # already linked, nothing to do
    elif [ $mig_result -eq 2 ]; then
        return 1  # error
    fi

    # On Windows junction must be absolute; on Unix prefer relative
    local link_target
    if [ "$(detect_os)" = "gitbash" ]; then
        link_target="$drive_raw"
    else
        link_target="drive/raw"  # relative — portable across repo moves
    fi

    # Create from inside REPO_ROOT so relative path resolves correctly
    (cd "$REPO_ROOT" && create_link "$link_target" "raw" "raw")
}

# ── Interactive provider menu ────────────────────────────────────────────────
choose_provider() {
    local os
    os="$(detect_os)"

    # Gather candidates per provider (first one only for menu display)
    local google icloud dropbox onedrive
    google="$(detect_google_drive "$os" | head -1)"
    icloud="$(detect_icloud "$os" | head -1)"
    dropbox="$(detect_dropbox "$os" | head -1)"
    onedrive="$(detect_onedrive "$os" | head -1)"

    echo "" >&2
    echo "A-Wiki Cloud Link Setup" >&2
    echo "=======================" >&2
    echo "Detecting cloud-backed storage on $os..." >&2
    echo "" >&2
    echo "Available providers:" >&2
    printf "  1) Google Drive    %s\n" "${google:-(not detected)}" >&2
    printf "  2) iCloud Drive    %s\n" "${icloud:-(not detected)}" >&2
    printf "  3) Dropbox         %s\n" "${dropbox:-(not detected)}" >&2
    printf "  4) OneDrive        %s\n" "${onedrive:-(not detected)}" >&2
    echo "  5) Custom path     (enter manually)" >&2
    echo "  6) Local fallback  ~/.a-wiki-data  (no cloud backup)" >&2
    echo "" >&2

    # Default: first detected provider
    local default=1
    if [ -z "$google" ] && [ -n "$icloud" ]; then default=2;
    elif [ -z "$google$icloud" ] && [ -n "$dropbox" ]; then default=3;
    elif [ -z "$google$icloud$dropbox" ] && [ -n "$onedrive" ]; then default=4;
    elif [ -z "$google$icloud$dropbox$onedrive" ]; then default=5
    fi

    printf "Pick provider [1-6, default=%d]: " "$default" >&2
    local choice
    read -r choice
    [ -z "$choice" ] && choice="$default"

    case "$choice" in
        1) [ -z "$google" ] && { err "Google Drive not detected"; return 1; }; printf '%s' "$google" ;;
        2) [ -z "$icloud" ] && { err "iCloud not detected"; return 1; }; printf '%s' "$icloud" ;;
        3) [ -z "$dropbox" ] && { err "Dropbox not detected"; return 1; }; printf '%s' "$dropbox" ;;
        4) [ -z "$onedrive" ] && { err "OneDrive not detected"; return 1; }; printf '%s' "$onedrive" ;;
        5)
            printf "Enter custom path: " >&2
            local custom; read -r custom
            [ -z "$custom" ] && { err "No path entered"; return 1; }
            printf '%s' "$custom"
            ;;
        6) printf '%s' "$HOME/.a-wiki-data" ;;
        *) err "Invalid choice: $choice"; return 1 ;;
    esac
}

# ── Auto-pick first available provider (non-interactive) ─────────────────────
auto_pick_provider() {
    local os
    os="$(detect_os)"
    local p
    for fn in detect_google_drive detect_icloud detect_dropbox detect_onedrive; do
        p="$($fn "$os" | head -1)"
        [ -n "$p" ] && { printf '%s' "$p"; return 0; }
    done
    # Last resort: local fallback
    printf '%s' "$HOME/.a-wiki-data"
}

# ── Provider-by-name lookup ──────────────────────────────────────────────────
pick_provider_by_name() {
    local name="$1"
    local os
    os="$(detect_os)"
    case "$name" in
        google|gdrive|googledrive) detect_google_drive "$os" | head -1 ;;
        icloud) detect_icloud "$os" | head -1 ;;
        dropbox) detect_dropbox "$os" | head -1 ;;
        onedrive) detect_onedrive "$os" | head -1 ;;
        local) printf '%s' "$HOME/.a-wiki-data" ;;
        *) err "Unknown provider: $name"; return 1 ;;
    esac
}

# ── Main setup orchestrator ──────────────────────────────────────────────────
cmd_setup() {
    local provider_path="${SETUP_PATH:-}"
    local mode="${SETUP_MODE:-both}"     # both | drive-only | raw-only
    local migrate_flag="${MIGRATE_FLAG:-0}"
    local auto="${AUTO_MODE:-0}"
    local provider_name="${PROVIDER_NAME:-}"

    # Non-TTY → force auto mode
    if [ ! -t 0 ] && [ -z "$provider_path" ] && [ -z "$provider_name" ]; then
        warn "Non-interactive terminal detected — switching to --auto mode"
        auto=1
    fi

    # Determine drive_path (unless raw-only and drive already set up)
    local drive_path=""
    if [ "$mode" = "raw-only" ]; then
        if drive_path="$(resolve_drive_path)"; then
            info "Using existing drive/ → $drive_path"
        else
            err "raw-only mode requires drive/ to be set up first"
            return 1
        fi
    else
        if [ -n "$provider_path" ]; then
            drive_path="$provider_path"
            # Append default folder if user gave a parent path
            case "$drive_path" in
                */"$DEFAULT_FOLDER"|*/"$DEFAULT_FOLDER"/) ;;
                *) drive_path="$drive_path/$DEFAULT_FOLDER" ;;
            esac
        elif [ -n "$provider_name" ]; then
            local parent
            parent="$(pick_provider_by_name "$provider_name")" || return 1
            [ -z "$parent" ] && { err "Provider $provider_name not detected on this machine"; return 1; }
            drive_path="$parent/$DEFAULT_FOLDER"
        elif [ "$auto" = "1" ]; then
            local parent
            parent="$(auto_pick_provider)"
            drive_path="$parent/$DEFAULT_FOLDER"
            info "Auto-picked: $drive_path"
        else
            local parent
            parent="$(choose_provider)" || return 1
            printf "Folder name under provider [default: %s]: " "$DEFAULT_FOLDER" >&2
            local folder
            read -r folder
            [ -z "$folder" ] && folder="$DEFAULT_FOLDER"
            drive_path="$parent/$folder"
            echo "" >&2
            printf "Will create/use: %s\n" "$drive_path" >&2
            printf "Proceed? [Y/n]: " >&2
            local confirm; read -r confirm
            case "$confirm" in
                n|N|no|NO) info "Aborted"; return 0 ;;
            esac
        fi
    fi

    # Step 1: drive/
    if [ "$mode" != "raw-only" ]; then
        echo ""
        info "[1/2] drive/ link"
        setup_drive "$drive_path" "${FORCE_FLAG:-0}" || return 1
    fi

    # Step 2: raw/
    if [ "$mode" != "drive-only" ]; then
        echo ""
        info "[2/2] raw/ link (→ drive/raw)"
        setup_raw "$migrate_flag" || return 1
    fi

    echo ""
    ok "Setup complete!"
    echo "  Verify: bash scripts/setup-cloud-link.sh --status"
    echo "  Backup userscript: cp scripts/userscripts/waste-form-ocr-fill.user.js drive/personal-tools/userscripts/"
}

# ── Argument parsing ─────────────────────────────────────────────────────────
SETUP_MODE="both"
SETUP_PATH=""
PROVIDER_NAME=""
AUTO_MODE=0
MIGRATE_FLAG=0
FORCE_FLAG=0
CMD="setup"

while [ $# -gt 0 ]; do
    case "$1" in
        --status)      CMD="status"; shift ;;
        --unlink)      CMD="unlink"; shift ;;
        --auto)        AUTO_MODE=1; shift ;;
        --drive-only)  SETUP_MODE="drive-only"; shift ;;
        --raw-only)    SETUP_MODE="raw-only"; shift ;;
        --migrate)     MIGRATE_FLAG=1; shift ;;
        --force)       FORCE_FLAG=1; shift ;;
        --path)
            [ $# -lt 2 ] && { err "--path requires argument"; exit 1; }
            SETUP_PATH="$2"; shift 2
            ;;
        --provider)
            [ $# -lt 2 ] && { err "--provider requires argument"; exit 1; }
            PROVIDER_NAME="$2"; shift 2
            ;;
        --help|-h)
            sed -n '/^# Usage:/,/^# ====/p' "$0" | sed 's/^# \{0,1\}//' | head -20
            exit 0
            ;;
        *) err "Unknown flag: $1"; exit 1 ;;
    esac
done

export SETUP_MODE SETUP_PATH PROVIDER_NAME AUTO_MODE MIGRATE_FLAG FORCE_FLAG

case "$CMD" in
    status) cmd_status ;;
    unlink) cmd_unlink ;;
    setup)  cmd_setup ;;
esac
