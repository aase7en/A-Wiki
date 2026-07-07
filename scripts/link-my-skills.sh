#!/usr/bin/env bash
# ============================================================================
# link-my-skills.sh — DEPRECATED shim, kept for backward compatibility.
# Use scripts/link-agent-configs.sh directly (covers more harnesses + .env).
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEW_SCRIPT="$SCRIPT_DIR/link-agent-configs.sh"

echo "note: link-my-skills.sh is deprecated — use scripts/link-agent-configs.sh (covers Kilo/Hermes/Gemini/Antigravity/ZCode/Windsurf/OpenClaw + .env too)" >&2

if [ $# -eq 0 ]; then
    exec bash "$NEW_SCRIPT" --agent claude --agent codex --agent cline --skills-only
fi

case "$1" in
    --claude) exec bash "$NEW_SCRIPT" --agent claude --skills-only ;;
    --codex)  exec bash "$NEW_SCRIPT" --agent codex --skills-only ;;
    --cline)  exec bash "$NEW_SCRIPT" --agent cline --skills-only ;;
    --list)   exec bash "$NEW_SCRIPT" --list ;;
    *)
        echo "Usage: $0 [--claude|--codex|--cline|--list]" >&2
        exit 1
        ;;
esac
