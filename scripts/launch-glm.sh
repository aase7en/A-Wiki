#!/usr/bin/env bash
# Launch Claude Code on Z.ai GLM Coding Plan (subscription) — direct, no ccr.
# Points the Anthropic-compatible endpoint at Z.ai with the coding-plan key.
# Use this to run GLM instead of Opus (saves Anthropic quota).
#
# Usage:  bash scripts/launch-glm.sh [extra claude args...]
set -euo pipefail
cd "$(dirname "$0")/.."

PY="python3"; command -v python3 >/dev/null 2>&1 || PY="python"
KEY="$("$PY" scripts/lib/drive_secrets.py ZHIPU_API_KEY)"
[ -n "$KEY" ] || { echo "ZHIPU_API_KEY not found in drive/.secrets" >&2; exit 1; }

export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_AUTH_TOKEN="$KEY"
unset ANTHROPIC_API_KEY 2>/dev/null || true
# Z.ai coding plan maps Claude model names -> GLM automatically; pin if desired:
# export ANTHROPIC_MODEL="glm-4.6"

echo "-> launching Claude Code on Z.ai GLM (subscription) ..."
exec claude "$@"
