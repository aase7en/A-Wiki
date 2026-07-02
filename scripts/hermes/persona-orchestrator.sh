#!/usr/bin/env bash
# persona-orchestrator.sh — POSIX wrapper for the sequential persona fan-out.
# Works on macOS, Linux, WSL, Git Bash. Calls Python via the first interpreter
# found in: python3 → python → py -3.  Mirrors scripts/batch/route.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCH_PY="$SCRIPT_DIR/persona-orchestrator.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$ORCH_PY" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$ORCH_PY" "$@"
elif command -v py >/dev/null 2>&1; then
    exec py -3 "$ORCH_PY" "$@"
else
    echo "error: python3, python, or py launcher required on PATH" >&2
    exit 127
fi
