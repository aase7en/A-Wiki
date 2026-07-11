#!/usr/bin/env bash
# session-start-apikey-check.sh
# Check availability of free-model API keys at session start.
# Output appears in SessionStart hook messages so user knows which free tiers are live.

set -euo pipefail

# Lean mode (token-save): skip informational session-start output
if [ "${AWIKI_LEAN_SESSION_START:-0}" = "1" ]; then exit 0; fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOAD_KEYS="$REPO_ROOT/scripts/hooks/load-drive-keys.sh"
if [[ -f "$LOAD_KEYS" ]]; then
  # shellcheck source=scripts/hooks/load-drive-keys.sh
  source "$LOAD_KEYS" >/dev/null 2>&1 || true
fi

AVAILABLE=()
MISSING=()

[[ -n "${OPENROUTER_API_KEY:-}" ]] && AVAILABLE+=("OpenRouter") || MISSING+=("OPENROUTER_API_KEY")
[[ -n "${GROQ_API_KEY:-}" ]]       && AVAILABLE+=("Groq")       || MISSING+=("GROQ_API_KEY")
[[ -n "${GEMINI_API_KEY:-}" || -n "${GOOGLE_AI_STUDIO_KEY:-}" ]] && AVAILABLE+=("Gemini") || MISSING+=("GEMINI_API_KEY")

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo "✅ Free-model keys ready: ${AVAILABLE[*]} — Tier-1 delegation fully operational"
elif [[ ${#AVAILABLE[@]} -gt 0 ]]; then
  echo "⚠️  Free-model partial: ✅ ${AVAILABLE[*]} | ❌ missing: ${MISSING[*]}"
else
  echo "❌ No free-model keys found (${MISSING[*]}) — all search/lookup will use Claude (costs tokens)"
  echo "   Set via: export OPENROUTER_API_KEY=... GROQ_API_KEY=... GEMINI_API_KEY=..."
fi
