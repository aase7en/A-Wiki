#!/usr/bin/env bash
# scripts/hooks/load-drive-keys.sh
# Load free-model API keys from drive/.secrets into the current shell env.
#
# This script is intentionally source-safe:
#   source scripts/hooks/load-drive-keys.sh
# so caller shells (delegate.sh, status hooks) can keep the exported vars.
#
# Key priority order (cost-first):
#   OPENROUTER_API_KEY — unlocks all free OpenRouter models (Gemini, DeepSeek, Qwen, Llama)
#   GEMINI_API_KEY / GOOGLE_AI_STUDIO_KEY — direct Gemini free tier (1500 req/day)
#   GROQ_API_KEY — direct Groq free tier (high rate limit, Llama)
#   ANTHROPIC_API_KEY — only if Haiku paid tier needed
#   OPENAI_API_KEY — only for Codex platform calls; never for delegation

set -euo pipefail

_AWIKI_DRIVE_KEYS_SOURCED=0
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  _AWIKI_DRIVE_KEYS_SOURCED=1
fi

_drive_keys_finish() {
  local code="${1:-0}"
  if [[ "$_AWIKI_DRIVE_KEYS_SOURCED" -eq 1 ]]; then
    return "$code"
  fi
  exit "$code"
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRIVE_SECRETS_PY="$REPO_ROOT/scripts/lib/drive_secrets.py"

# Only import if drive_secrets.py exists and drive/ is linked
if [ ! -f "$DRIVE_SECRETS_PY" ]; then
  echo "⚠️  [drive-keys] drive_secrets.py not found — skipping key load" >&2
  _drive_keys_finish 0
fi

# Fast check: skip only when the main free-tier key families are already present.
if [ -n "${OPENROUTER_API_KEY:-}" ] && \
   { [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; } && \
   [ -n "${GROQ_API_KEY:-}" ]; then
  echo "✅ [drive-keys] Free-model keys already complete in env — skip drive load" >&2
  _drive_keys_finish 0
fi

# Load keys from drive/.secrets
echo "🔑 [drive-keys] Loading free-model keys from drive/.secrets..." >&2

load_key() {
  local key_name="$1"
  local env_var="${2:-$1}"
  local val
  val=$(python3 "$DRIVE_SECRETS_PY" "$key_name" 2>/dev/null) || return 0
  if [ -n "$val" ] && [ "$val" != "None" ] && [ "$val" != "null" ]; then
    export "$env_var=$val"
    echo "  ✓ $env_var loaded" >&2
  fi
}

load_key "OPENROUTER_API_KEY"
load_key "GEMINI_API_KEY"
load_key "GOOGLE_AI_STUDIO_KEY" "GEMINI_API_KEY"
load_key "GROQ_API_KEY"
# Paid keys — load only if present; delegate.sh uses them only as last resort
load_key "ANTHROPIC_API_KEY"
load_key "DEEPSEEK_API_KEY"

_drive_keys_finish 0
