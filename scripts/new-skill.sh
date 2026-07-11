#!/usr/bin/env bash
# new-skill.sh — POSIX wrapper for scripts/new-skill.py (scaffold + register a skill).
# Works on macOS, Linux, WSL, Git Bash. Calls Python via the first interpreter
# found in: python3 → python → py -3.  Mirrors scripts/hermes/telegram-command-router.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEW_SKILL_PY="$SCRIPT_DIR/new-skill.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$NEW_SKILL_PY" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$NEW_SKILL_PY" "$@"
elif command -v py >/dev/null 2>&1; then
    exec py -3 "$NEW_SKILL_PY" "$@"
else
    echo "error: python3, python, or py launcher required on PATH" >&2
    exit 127
fi
