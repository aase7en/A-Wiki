#!/usr/bin/env bash
# Launch Claude Code through claude-code-router (ccr) — multi-provider backend.
# Regenerates ~/.claude-code-router/config.json from Drive secrets, then `ccr code`.
#
# Usage:  bash scripts/launch-ccr.sh [extra ccr args...]
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v ccr >/dev/null 2>&1; then
  echo "ERROR: 'ccr' not found. Install:  npm i -g @musistudio/claude-code-router" >&2
  exit 1
fi

# Pick a python
PY="python3"; command -v python3 >/dev/null 2>&1 || PY="python"

echo "→ regenerating ccr config from Drive .secrets ..."
"$PY" scripts/gen-ccr-config.py

echo "→ starting Claude Code via ccr ..."
exec ccr code "$@"
