#!/usr/bin/env bash
# ============================================================================
# load-global-env.sh — source the universal secrets from Drive into this shell
# ============================================================================
# Cross-platform: resolves Drive path via the same chain as drive_path.py
# (env override → drive/ link → .drive-path file → ~/.a-wiki-data fallback).
#
# Loads:
#   1. <drive>/secrets/global.env           (universal AI keys etc.)
#   2. <drive>/secrets/<repo>.env  (if --repo NAME given)  (repo-specific)
#
# Repo-specific values override global ones (loaded second).
# Idempotent: re-sourcing is safe.
#
# Usage:
#   source "$(dirname "$0")/load-global-env.sh"
#   source "$(dirname "$0")/load-global-env.sh" --repo env-wastewater-webapp
#   bash -c 'source load-global-env.sh --repo X && env | grep KEY'
#
# Flags:
#   --repo NAME    also load secrets/<NAME>.env after global.env
#   --quiet        suppress the "loaded N keys" message
#   --print        print KEY=VALUE lines instead of exporting (for debugging,
#                  values still shown — never pipe this to a committable file)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REPO_NAME=""
QUIET=0
PRINT_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --repo) REPO_NAME="${2:-${REPO_NAME}}"; shift ;;
        --repo=*) REPO_NAME="${arg#*=}" ;;
        --quiet) QUIET=1 ;;
        --print) PRINT_ONLY=1 ;;
        --help|-h) sed -n '2,30p' "${BASH_SOURCE[0]:-$0}" | sed 's/^# \{0,1\}//'; return 0 2>/dev/null || exit 0 ;;
    esac
done

# ── resolve Drive root (same order as scripts/drive_path.py) ─────────────────
resolve_drive_root() {
    if [ -n "${A_WIKI_DRIVE_PATH:-}" ]; then
        echo "$A_WIKI_DRIVE_PATH"
        return 0
    fi
    if [ -e "$REPO_ROOT/drive" ]; then
        # Resolve through symlink/junction.
        if command -v realpath >/dev/null 2>&1; then
            realpath "$REPO_ROOT/drive" 2>/dev/null && return 0
        fi
        echo "$REPO_ROOT/drive"
        return 0
    fi
    if [ -f "$REPO_ROOT/.drive-path" ]; then
        local p
        p="$(head -n 1 "$REPO_ROOT/.drive-path" | tr -d '\r')"
        if [ -n "$p" ]; then
            echo "$p"
            return 0
        fi
    fi
    echo "$HOME/.a-wiki-data"
}

DRIVE_ROOT="$(resolve_drive_root)"
SECRETS_DIR="$DRIVE_ROOT/secrets"

# ── loader core: parse a .env file and export (or print) its keys ────────────
# Strips 'export ' prefix, surrounding quotes, and comments. Later loads
# override earlier ones for the same key. Returns count via global
# LOAD_ENV_COUNT (set before each call; can't echo-and-capture because the
# `while read < file` runs in a subshell on some shells).
load_env_file() {
    local path="$1"
    LOAD_ENV_COUNT=0
    [ -f "$path" ] || return 0
    # Read into an array first so the export loop runs in THIS shell (not the
    # pipe subshell). Avoids the classic "while read in pipe loses vars" bug.
    local lines=()
    while IFS= read -r line || [ -n "$line" ]; do
        lines+=("$line")
    done < "$path"
    local line key val
    for line in "${lines[@]}"; do
        # Strip CR (Drive may sync with CRLF on Windows).
        line="${line%$'\r'}"
        # Skip blanks and comments.
        case "$line" in
            ''|'#'*|';'*) continue ;;
        esac
        # Strip optional 'export '.
        case "$line" in
            export\ *) line="${line#export }" ;;
        esac
        # Must have KEY=value.
        case "$line" in
            *=*) ;;
            *) continue ;;
        esac
        key="${line%%=*}"
        val="${line#*=}"
        # Strip surrounding quotes.
        case "$val" in
            \"*\") val="${val#\"}"; val="${val%\"}" ;;
            \'*\') val="${val#\'}"; val="${val%\'}" ;;
        esac
        # Validate key (letters/digits/underscore; must start non-digit).
        case "$key" in
            [!A-Za-z_]*) continue ;;
            *[!A-Za-z0-9_]*) continue ;;
        esac
        if [ "$PRINT_ONLY" = "1" ]; then
            printf '%s=%s\n' "$key" "$val"
        else
            export "$key=$val"
        fi
        LOAD_ENV_COUNT=$((LOAD_ENV_COUNT + 1))
    done
}

GLOBAL_PATH="$SECRETS_DIR/global.env"
REPO_PATH=""
[ -n "$REPO_NAME" ] && REPO_PATH="$SECRETS_DIR/${REPO_NAME}.env"

# ── load ─────────────────────────────────────────────────────────────────────
n_global=0
n_repo=0
if [ -f "$GLOBAL_PATH" ]; then
    load_env_file "$GLOBAL_PATH"
    n_global="$LOAD_ENV_COUNT"
else
    if [ "$QUIET" = "0" ]; then
        echo "load-global-env: WARNING — $GLOBAL_PATH not found" >&2
        echo "  Drive root resolved to: $DRIVE_ROOT" >&2
        echo "  Set A_WIKI_DRIVE_PATH or fix A-Wiki/.drive-path" >&2
    fi
fi

if [ -n "$REPO_PATH" ] && [ -f "$REPO_PATH" ]; then
    load_env_file "$REPO_PATH"
    n_repo="$LOAD_ENV_COUNT"
fi

if [ "$QUIET" = "0" ] && [ "$PRINT_ONLY" = "0" ]; then
    msg="load-global-env: $n_global keys from global.env"
    [ -n "$REPO_NAME" ] && msg="$msg + $n_repo from ${REPO_NAME}.env"
    msg="$msg (drive: $DRIVE_ROOT)"
    echo "$msg" >&2
fi
