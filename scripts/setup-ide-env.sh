#!/usr/bin/env bash
# ============================================================================
# setup-ide-env.sh — make every terminal (incl. IDE-embedded) auto-source the
# global env from Drive.
# ============================================================================
# Strategy: inject ONE source line into the user's shell rc file
# (.bashrc on Git Bash / Linux, .zshrc on macOS). Every terminal — including
# the embedded terminals in VSCode, Windsurf, Devin, Cursor — starts a login
# shell that reads the rc file, so this single hook reaches them all without
# touching per-IDE settings.json (which is fragile and format-sensitive).
#
# The injected line is idempotent and guarded so it sources only when the
# loader exists; safe to re-run.
#
# Usage:
#   bash scripts/setup-ide-env.sh              # inject (default)
#   bash scripts/setup-ide-env.sh --status     # show what's injected where
#   bash scripts/setup-ide-env.sh --remove     # take the hook back out
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="$SCRIPT_DIR/load-global-env.sh"

MODE="inject"
for arg in "$@"; do
    case "$arg" in
        --status) MODE="status" ;;
        --remove) MODE="remove" ;;
        --help|-h) sed -n '2,20p' "${BASH_SOURCE[0]:-$0}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    esac
done

# The marker lines we add/remove — searchable, idempotent.
MARK_BEGIN="# >>> A-Wiki global env (setup-ide-env.sh) >>>"
MARK_END="# <<< A-Wiki global env <<<"
# Use a resolved path so the hook works from any cwd. $0 is this script; the
# loader sits beside it. Quote for paths with spaces (Windows "My Drive").
HOOK_LINE="source \"$LOADER\" --quiet 2>/dev/null || true"

# Candidate rc files, in priority order. We inject into the FIRST that exists
# (or the first we can create). Bash is the default on Git Bash + Linux;
# zsh is default on macOS.
rc_candidates() {
    case "$(uname -s)" in
        Darwin*) echo "$HOME/.zshrc $HOME/.bashrc" ;;
        Linux*)  echo "$HOME/.bashrc $HOME/.zshrc" ;;
        MINGW*|MSYS*|CYGWIN*) echo "$HOME/.bashrc $HOME/.bash_profile" ;;
        *) echo "$HOME/.bashrc $HOME/.profile" ;;
    esac
}

find_rc() {
    for rc in $(rc_candidates); do
        if [ -f "$rc" ]; then
            echo "$rc"
            return 0
        fi
    done
    # None exist — create the first candidate so we have somewhere to inject.
    local first
    first="$(rc_candidates | cut -d' ' -f1)"
    mkdir -p "$(dirname "$first")"
    : > "$first"
    echo "$first"
}

block_present() {
    grep -qF "$MARK_BEGIN" "$1" 2>/dev/null
}

case "$MODE" in
    status)
        echo "IDE env hook status"
        echo "  loader: $LOADER ($([ -f "$LOADER" ] && echo present || echo MISSING))"
        echo ""
        for rc in $(rc_candidates); do
            if [ ! -f "$rc" ]; then
                echo "  [ -- ] $rc (not present)"
            elif block_present "$rc"; then
                echo "  [✅ ] $rc (hook injected)"
            else
                echo "  [ -- ] $rc (no hook)"
            fi
        done
        ;;
    inject)
        if [ ! -f "$LOADER" ]; then
            echo "ERROR — loader not found at $LOADER" >&2
            exit 1
        fi
        rc="$(find_rc)"
        if block_present "$rc"; then
            echo "Already injected in $rc — nothing to do."
            exit 0
        fi
        {
            echo ""
            echo "$MARK_BEGIN"
            echo "# Auto-source A-Wiki secrets/global.env (+ <repo>.env) into every"
            echo "# terminal, including IDE-embedded (VSCode/Windsurf/Devin). Safe to"
            echo "# remove; re-run setup-ide-env.sh to restore."
            echo "$HOOK_LINE"
            echo "$MARK_END"
        } >> "$rc"
        echo "Injected hook into $rc"
        echo "Open a new terminal (or run 'source $rc') to pick up global env in IDE terminals."
        ;;
    remove)
        removed=0
        for rc in $(rc_candidates); do
            [ -f "$rc" ] || continue
            if ! block_present "$rc"; then continue; fi
            # Delete from MARK_BEGIN through MARK_END inclusive.
            # awk is portable across the Git Bash / macOS / Linux trio.
            awk -v b="$MARK_BEGIN" -v e="$MARK_END" '
                $0 == b { skip=1; next }
                $0 == e { skip=0; next }
                !skip { print }
            ' "$rc" > "$rc.tmp" && mv "$rc.tmp" "$rc"
            echo "Removed hook from $rc"
            removed=$((removed + 1))
        done
        [ "$removed" = "0" ] && echo "No hook found in any rc file."
        ;;
esac
