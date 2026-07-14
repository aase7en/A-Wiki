#!/usr/bin/env bash
# =============================================================================
# setup-agent-drive.sh — Per-agent Drive isolation skeleton (USA-1 §4)
# =============================================================================
# Creates the .~<agent>/ directory tree on the resolved A-Wiki-Data Drive for
# one or all agents. Idempotent — safe to re-run.
#
# Each agent gets its own isolated state on Drive (sessions, worktrees, memory,
# hooks-state, large-artifacts). This stops agent state from polluting the repo
# or mixing with other agents (USA-1 hybrid Drive layer, Goal #2).
#
# This does NOT move existing data — it only creates empty dirs. Hermes has an
# existing shared pool (hermes-sync/) that chunk C4 optionally migrates.
#
# Usage:
#   bash scripts/setup-agent-drive.sh                # all 9 agents
#   bash scripts/setup-agent-drive.sh codex          # one agent
#   bash scripts/setup-agent-drive.sh codex zcode    # multiple
#   bash scripts/setup-agent-drive.sh --status       # show state
#
# Cross-platform: macOS, Linux, Windows Git Bash, WSL. POSIX-safe.
# =============================================================================
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRIVE_LINK="$REPO_ROOT/drive"
DRIVE_PATH_FILE="$REPO_ROOT/.drive-path"

# The 9 USA-1 agents. Add future agents here (one line).
AGENTS="claude codex gemini zcode hermes kilo cline antigravity windsurf openclaw"

# Per-agent subtree (USA-1 §4.2).
SUBDIRS="sessions worktrees memory hooks-state large-artifacts"

# ── Resolve Drive path ───────────────────────────────────────────────────────
resolve_drive() {
    # 1. drive/ junction already resolves it
    if [ -d "$DRIVE_LINK" ] && [ ! -L "$DRIVE_LINK" -o -d "$DRIVE_LINK/" ]; then
        # Follow the link to the real path (works for macOS symlink + Windows junction)
        local resolved
        resolved="$(cd "$DRIVE_LINK" 2>/dev/null && pwd -P 2>/dev/null || true)"
        if [ -n "$resolved" ] && [ -d "$resolved" ]; then
            echo "$resolved"
            return 0
        fi
    fi
    # 2. .drive-path file
    if [ -r "$DRIVE_PATH_FILE" ]; then
        local p
        p="$(cat "$DRIVE_PATH_FILE" | tr -d '[:space:]')"
        if [ -n "$p" ] && [ -d "$p" ]; then
            echo "$p"
            return 0
        fi
    fi
    # 3. Not resolved — caller should warn + point at setup-cloud-link.sh
    return 1
}

# ── Colors (POSIX-safe) ──────────────────────────────────────────────────────
if [ -t 1 ]; then
    GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
    BLUE=$'\033[0;34m'; RESET=$'\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; BLUE=''; RESET=''
fi
ok()   { printf "%s✅ %s%s\n" "$GREEN" "$*" "$RESET"; }
warn() { printf "%s⚠️  %s%s\n" "$YELLOW" "$*" "$RESET"; }
err()  { printf "%s❌ %s%s\n" "$RED" "$*" "$RESET" >&2; }
info() { printf "%s%s%s\n" "$BLUE" "$*" "$RESET"; }

# ── Status mode ──────────────────────────────────────────────────────────────
show_status() {
    local drive_root
    if ! drive_root="$(resolve_drive)"; then
        err "Drive not resolved. Run: bash scripts/setup-cloud-link.sh --auto"
        return 1
    fi
    info "Drive root: $drive_root"
    echo ""
    printf "%-18s %-12s %s\n" "AGENT" "EXISTS" "PATH"
    printf "%-18s %-12s %s\n" "-----" "------" "----"
    for agent in $AGENTS; do
        local dir="$drive_root/.~$agent"
        if [ -d "$dir" ]; then
            local n
            n=$(find "$dir" -mindepth 1 -maxdepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')
            printf "%-18s %-12s %s (%s files)\n" "$agent" "yes" "$dir" "$n"
        else
            printf "%-18s %-12s -\n" "$agent" "no"
        fi
    done
}

# ── Create skeleton for one agent ────────────────────────────────────────────
create_agent_skeleton() {
    local agent="$1"
    local drive_root="$2"
    local agent_dir="$drive_root/.~$agent"
    mkdir -p "$agent_dir"
    for sub in $SUBDIRS; do
        mkdir -p "$agent_dir/$sub"
    done
    # Drop a tiny README so the dirs aren't empty on a fresh Drive
    if [ ! -f "$agent_dir/README.md" ]; then
        cat > "$agent_dir/README.md" <<EOF
# .~$agent/ — agent-isolated state (USA-1 §4)

Auto-created by scripts/setup-agent-drive.sh. Per-agent Drive isolation so
$agent state does not pollute the repo or other agents.

Subdirs: $(echo "$SUBDIRS" | tr '\n' ' ')

This directory is gitignored (see .gitignore \`.\~\` rule) and lives on the
resolved A-Wiki-Data Drive. Never commit contents to the public repo.
EOF
    fi
    ok "$agent: $agent_dir"
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    local args=("$@")
    # Handle --status
    for a in "${args[@]:-}"; do
        if [ "$a" = "--status" ]; then
            show_status
            return $?
        fi
    done

    local drive_root
    if ! drive_root="$(resolve_drive)"; then
        err "Drive not resolved. Run first: bash scripts/setup-cloud-link.sh --auto"
        err "Then re-run: bash scripts/setup-agent-drive.sh"
        return 1
    fi
    info "Drive root: $drive_root"
    echo ""

    # Pick targets: explicit args, else all agents.
    local targets=()
    local have_explicit=false
    for a in "${args[@]:-}"; do
        case "$a" in
            --*) ;;
            *) targets+=("$a"); have_explicit=true ;;
        esac
    done
    if [ "$have_explicit" = "false" ]; then
        # shellcheck disable=SC2206
        targets=( $AGENTS )
    fi

    info "Creating .~<agent>/ skeletons for: ${targets[*]}"
    for agent in "${targets[@]}"; do
        # Validate agent name (only lowercase letters — guards against typos / path injection)
        if ! echo "$agent" | grep -qE '^[a-z]+$'; then
            warn "skip invalid agent name: $agent"
            continue
        fi
        create_agent_skeleton "$agent" "$drive_root"
    done
    echo ""
    ok "Done. Agents now have isolated Drive state under $drive_root/.~<agent>/"
    info "These dirs are gitignored — never commit their contents."
}

main "$@"
