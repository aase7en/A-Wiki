#!/usr/bin/env bash
# ============================================================================
# git_safe.sh — git wrapper that tolerates index.lock contention
# ============================================================================
# A-Wiki has background sync agents (Hermes, live dashboard) that can hold
# .git/index.lock briefly. This wrapper retries git commands that fail due
# to lock contention, with exponential backoff. Source it, then call
# `git_safe <args>` instead of `git <args>` for non-interactive ops.
#
# Usage:
#   source scripts/lib/git_safe.sh
#   git_safe add -A
#   git_safe commit -m "..."
#   git_safe push origin main
#
# Or set git alias: git config alias.safe '!bash scripts/lib/git_safe.sh'
# ============================================================================

# Max attempts + initial backoff (seconds). Total worst-case wait ≈ 1+2+4+8 = 15s.
GIT_SAFE_MAX_TRIES=5
GIT_SAFE_INITIAL_BACKOFF=1

git_safe() {
    local try=1
    local backoff="$GIT_SAFE_INITIAL_BACKOFF"
    local out rc
    while [ "$try" -le "$GIT_SAFE_MAX_TRIES" ]; do
        out="$(git "$@" 2>&1)"
        rc=$?
        if [ "$rc" = "0" ]; then
            printf '%s' "$out"
            return 0
        fi
        # Detect lock contention specifically — don't retry on real errors.
        case "$out" in
            *"index.lock"*|*"Another git process"*|*"Device or resource busy"*|*"Unable to create"*)
                if [ "$try" -lt "$GIT_SAFE_MAX_TRIES" ]; then
                    # Try to clear a stale lock if no git process is actually running.
                    # (Safe: a live git process holds the OS file lock; rm would fail.)
                    if [ -f ".git/index.lock" ]; then
                        # Only remove if older than 30s (likely stale, not active).
                        local lock_age=$(( $(date +%s) - $(stat -c %Y ".git/index.lock" 2>/dev/null || stat -f %m ".git/index.lock" 2>/dev/null || echo 0) ))
                        if [ "$lock_age" -gt 30 ]; then
                            rm -f .git/index.lock 2>/dev/null && \
                                echo "git_safe: removed stale index.lock (age ${lock_age}s)" >&2
                        fi
                    fi
                    sleep "$backoff"
                    backoff=$(( backoff * 2 ))
                    try=$((try + 1))
                    continue
                fi
                ;;
        esac
        # Non-lock error — print + return the real exit code.
        printf '%s' "$out" >&2
        return "$rc"
    done
    printf '%s\n' "git_safe: gave up after $GIT_SAFE_MAX_TRIES tries (lock contention)" >&2
    return 1
}
