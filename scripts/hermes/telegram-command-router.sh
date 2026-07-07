#!/usr/bin/env bash
# telegram-command-router.sh — POSIX wrapper for the Telegram slash-command router.
# Works on macOS, Linux, WSL, Git Bash. Calls Python via the first interpreter
# found in: python3 → python → py -3.  Mirrors scripts/batch/route.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTER_PY="$SCRIPT_DIR/telegram-command-router.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$ROUTER_PY" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$ROUTER_PY" "$@"
elif command -v py >/dev/null 2>&1; then
    exec py -3 "$ROUTER_PY" "$@"
else
    echo "error: python3, python, or py launcher required on PATH" >&2
    exit 127
fi
