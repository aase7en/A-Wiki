#!/usr/bin/env bash
# =============================================================================
# pre-commit-awiki.sh — USA-1 §5 Layer 2 (local commit gate)
# =============================================================================
# Comprehensive pre-commit gate that runs BEFORE a commit lands. Combines:
#   1. Skill-registry drift check (delegates to pre_commit_skill_surfaces.sh)
#   2. Secret leak scan on the staged diff (uses security_patterns.yaml)
#   3. Machine-specific path scan on the staged diff (USA-1 §5.1 / §4.3)
#
# This is Layer 2 of the three-layer defense (Layer 1 = PreToolUse hooks,
# Layer 2 = this pre-commit gate, Layer 3 = CI workflow). No single layer is
# trusted alone.
#
# Install: bash scripts/install-git-hooks.sh   (or symlink manually)
# Override (emergency): PRE_COMMIT_SKIP_AWIKI=1
# =============================================================================
set -euo pipefail

if [ "${PRE_COMMIT_SKIP_AWIKI:-0}" = "1" ]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Colors (POSIX-safe).
if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RESET=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; RESET=''
fi

BLOCKED=false

# python3 first: macOS ships no bare `python`. Invoking it here silently
# disabled the secret scan below (see the SCAN_RESULT block).
if [ -x ".venv/bin/python3" ]; then
    PY=".venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    printf "%s🚫 [pre-commit] no python3 on PATH — security scan cannot run.%s\n" "$RED" "$RESET" >&2
    printf "   Install python3, or override with PRE_COMMIT_SKIP_AWIKI=1 if you accept the risk.\n" >&2
    exit 1
fi

# ── 1. Skill-registry drift (existing check, delegated) ─────────────────────
# This script exits 1 on drift; under set -e we'd abort, so capture instead.
if ! bash scripts/hooks/pre_commit_skill_surfaces.sh >/dev/null 2>&1; then
    printf "%s🚫 [pre-commit] Skill surface drift detected.%s\n" "$RED" "$RESET" >&2
    printf "   Fix: python3 scripts/regen-skill-surfaces.py\n" >&2
    BLOCKED=true
fi

# ── 2 + 3. Secret + machine-path scan on staged diff ────────────────────────
# Pipe the staged unified diff to a single Python scan that loads
# security_patterns.yaml and flags any secret or machine-path pattern.
STAGED_DIFF="$(git diff --cached --unified=0 -- ':!*.lock' ':!*.sum' 2>/dev/null || true)"
if [ -n "$STAGED_DIFF" ]; then
    # Fail CLOSED. The previous form was
    #   ... | python scripts/hooks/_scan_staged_diff.py 2>/dev/null || true
    # which turned "python not found" into an empty SCAN_RESULT — read by the
    # test below as "no findings". The scan silently never ran on macOS.
    # Capture status and output separately so a broken scanner blocks loudly.
    SCAN_ERR="$(mktemp)"
    set +e
    SCAN_RESULT=$(printf '%s' "$STAGED_DIFF" | "$PY" scripts/hooks/_scan_staged_diff.py 2>"$SCAN_ERR")
    SCAN_STATUS=$?
    set -e
    if [ "$SCAN_STATUS" -ne 0 ]; then
        printf "%s🚫 [pre-commit] Security scan FAILED TO RUN (exit %s) — not treating that as clean.%s\n" "$RED" "$SCAN_STATUS" "$RESET" >&2
        sed 's/^/   /' "$SCAN_ERR" >&2
        printf "   Override: PRE_COMMIT_SKIP_AWIKI=1\n" >&2
        BLOCKED=true
    fi
    rm -f "$SCAN_ERR"
    if [ -n "$SCAN_RESULT" ]; then
        printf "%s🚫 [pre-commit] Security finding in staged diff:%s\n" "$RED" "$RESET" >&2
        printf '%s\n' "$SCAN_RESULT" >&2
        printf "   Override: PRE_COMMIT_SKIP_AWIKI=1\n" >&2
        BLOCKED=true
    fi
fi

if [ "$BLOCKED" = "true" ]; then
    exit 1
fi

printf "%s✅ [pre-commit] AWiki safety gate passed.%s\n" "$GREEN" "$RESET" >&2
exit 0
