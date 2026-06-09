#!/usr/bin/env bash
# route.sh — POSIX wrapper for A-Wiki universal ingest harness.
# Works on macOS, Linux, WSL, Git Bash. Calls Python via the first interpreter
# found in: python3 → python → py -3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTE_PY="$SCRIPT_DIR/route.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$ROUTE_PY" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$ROUTE_PY" "$@"
elif command -v py >/dev/null 2>&1; then
    exec py -3 "$ROUTE_PY" "$@"
else
    echo "error: python3, python, or py launcher required on PATH" >&2
    exit 127
fi
