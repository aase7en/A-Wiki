#!/usr/bin/env bash
# ============================================================================
# run-task.sh — Routine Pattern Execution with Iron Law Pre-Flight Check
# ============================================================================
# Usage:
#   bash run-task.sh <task-name> [task-args...]
#
# Tasks:
#   start       Begin a new session (validates git, checks Iron Laws)
#   end         End a session (writes summary, verifies no debug prints)
#   scoute-models  Scout available free AI models via OpenRouter
#   commit      Commit with automated summary generation
#
# All tasks run pre-flight hooks that enforce Iron Laws before execution.
# ============================================================================

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_PY="$REPO_ROOT/agent-skills/automations/hooks.py"

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Iron Law Pre-Flight ──
pre_flight() {
    log_info "Running Iron Law pre-flight checks..."

    # Check git remote
    if ! git -C "$REPO_ROOT" remote -v | grep -q "origin"; then
        log_error "IRON LAW VIOLATION: No git remote 'origin' configured."
        exit 1
    fi
    log_info "✅ Git origin validated."

    # Check main branch
    BRANCH=$(git -C "$REPO_ROOT" branch --show-current)
    if [ "$BRANCH" != "main" ]; then
        log_error "IRON LAW VIOLATION: On branch '$BRANCH'. Must be on 'main'."
        exit 1
    fi
    log_info "✅ On branch 'main'."

    # Run Python hooks if available
    if [ -f "$HOOKS_PY" ]; then
        python "$HOOKS_PY" pre-flight
        log_info "✅ Python hooks passed."
    fi

    log_info "🎯 All Iron Law checks passed. Ready to execute."
}

# ── Tasks ──
task_start() {
    log_info "Starting new session..."
    pre_flight

    # Read session continuity
    if [ -f "$REPO_ROOT/.local/session-memory.md" ]; then
        log_info "Previous session found. Last 5 entries:"
        grep -E "^## \[" "$REPO_ROOT/.local/session-memory.md" | tail -5
    fi

    log_info "✅ Session initialized."
}

task_end() {
    log_info "Ending session..."

    # Verify no debug prints
    if [ -f "$HOOKS_PY" ]; then
        python "$HOOKS_PY" session-end
    fi

    # Write session summary interactively or from args
    TITLE="${1:-$(date '+%Y-%m-%d %H:%M') session}"
    STATUS="${2:-completed}"
    CONTEXT="${3:-}"
    NEXT="${4:-}"

    if [ -f "$HOOKS_PY" ]; then
        python "$HOOKS_PY" summary "$TITLE" "$STATUS" "$CONTEXT" "$NEXT"
    else
        cat >> "$REPO_ROOT/.local/session-memory.md" <<- EOF

## [$(date '+%Y-%m-%d %H:%M')] — $TITLE
**Status:** $STATUS
**Context:** $CONTEXT
**Next:** $NEXT
---
EOF
    fi

    log_info "✅ Session ended. Summary written."
}

task_models() {
    log_info "Scouting available free AI models..."
    # Perform scouting via curl to OpenRouter
    if command -v curl &> /dev/null; then
        RESPONSE=$(curl -s --max-time 10 "https://openrouter.ai/api/v1/models" 2>/dev/null || echo "")
        if [ -n "$RESPONSE" ]; then
            echo "$RESPONSE" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = data.get('data', [])
    free = [m for m in models if m.get('pricing', {}).get('prompt') == '0' and m.get('pricing', {}).get('completion') == '0']
    print(f'Found {len(free)} free models:')
    for m in free:
        name = m.get('id', 'unknown')
        ctx = m.get('context_length', '?')
        print(f'  • {name} (context: {ctx})')
except:
    print('Could not parse model list')
" 2>/dev/null || echo "⚠️  Could not scout models — check network / API status."
        else
            log_warn "OpenRouter API not reachable. Try web search fallback."
        fi
    else
        log_warn "curl not available. Cannot scout models."
    fi
    log_info "✅ Model scouting complete."
}

task_commit() {
    log_info "Preparing commit..."

    # Show staged changes
    git -C "$REPO_ROOT" diff --cached --stat

    # Verify
    if [ -f "$HOOKS_PY" ]; then
        python "$HOOKS_PY" session-end
    fi

    log_info "Ready to commit. Use: git commit -m \"type(scope): message\""
}

# ── Main Dispatch ──
case "${1:-help}" in
    start)
        task_start
        ;;
    end)
        shift
        task_end "$@"
        ;;
    scout|scout-models|models)
        task_models
        ;;
    commit|pre-commit)
        task_commit
        ;;
    pre-flight|check)
        pre_flight
        ;;
    *)
        echo "Usage: $0 <task> [args...]"
        echo ""
        echo "Tasks:"
        echo "  start        Begin new session (validates Iron Laws)"
        echo "  end [title] [status] [ctx] [next]"
        echo "               End session and write summary"
        echo "  scout-models Scout free AI models from OpenRouter"
        echo "  commit       Prepare for commit (verify, stat)"
        echo "  pre-flight   Run Iron Law checks only"
        ;;
esac
