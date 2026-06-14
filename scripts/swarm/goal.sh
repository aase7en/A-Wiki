#!/usr/bin/env bash
# scripts/swarm/goal.sh — Shell entry point for AG2 Goal Orchestrator
#
# Usage:
#   bash scripts/swarm/goal.sh "<goal>"              # full execution
#   bash scripts/swarm/goal.sh "<goal>" --dry-run    # plan only, no external calls
#   bash scripts/swarm/goal.sh "<goal>" --json       # JSON output
#   bash scripts/swarm/goal.sh "<goal>" --mode plan  # same as --dry-run
#
# Cost-first: always dry-run first to see the plan before committing tokens.
#
# Requires:
#   .venv-ag2/  (python3.10 -m venv .venv-ag2 && pip install -r requirements-ag2.txt)
#   OPENAI_API_KEY env var for Planner (or set via drive/.secrets)
#   OPENROUTER_API_KEY / GEMINI_API_KEY for Executors (free models via delegate.sh)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# ── Arg parsing ───────────────────────────────────────────────────────────────
GOAL=""
EXTRA_ARGS=()
for arg in "$@"; do
  if [ -z "$GOAL" ] && [[ "$arg" != --* ]]; then
    GOAL="$arg"
  else
    EXTRA_ARGS+=("$arg")
  fi
done

if [ -z "$GOAL" ]; then
  echo "Usage: $0 \"<goal>\" [--dry-run] [--json] [--mode plan|execute|full]" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  bash scripts/swarm/goal.sh \"Summarize recent IoT research in A-Wiki\" --dry-run" >&2
  echo "  bash scripts/swarm/goal.sh \"Find all pharmacy entries missing SP data\" --json" >&2
  exit 1
fi

# ── Python runtime: prefer .venv-ag2, fallback to system ─────────────────────
PYTHON=""
if [ -f "$REPO_ROOT/.venv-ag2/bin/python3" ]; then
  PYTHON="$REPO_ROOT/.venv-ag2/bin/python3"
elif command -v python3.10 &>/dev/null; then
  PYTHON="python3.10"
elif command -v python3 &>/dev/null; then
  PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PYTHON="python3"
  else
    echo "⚠️  Python $PY_VER found but AG2 requires >=3.10" >&2
    echo "   Install: python3.10 -m venv .venv-ag2 && pip install -r requirements-ag2.txt" >&2
    echo "   Falling back to dry-run mode (no AG2 needed)..." >&2
    EXTRA_ARGS+=("--dry-run")
    PYTHON="python3"
  fi
else
  echo "❌ python3 not found" >&2
  exit 1
fi

# ── Load keys from drive/.secrets if not already in env ──────────────────────
DRIVE_SECRETS="$REPO_ROOT/scripts/lib/drive_secrets.py"
if [ -f "$DRIVE_SECRETS" ]; then
  load_key() {
    local k="$1" v
    [ -n "${!k:-}" ] && return 0
    v=$(python3 "$DRIVE_SECRETS" "$k" 2>/dev/null) || return 0
    [ -z "$v" ] || [ "$v" = "None" ] || export "$k=$v"
  }
  load_key OPENAI_API_KEY
  load_key OPENROUTER_API_KEY
  load_key GEMINI_API_KEY
  load_key GROQ_API_KEY
fi

# ── Execute ───────────────────────────────────────────────────────────────────
echo "🎯 A-Wiki Goal: $GOAL" >&2
exec "$PYTHON" scripts/swarm/ag2-goal.py --goal "$GOAL" "${EXTRA_ARGS[@]}"
