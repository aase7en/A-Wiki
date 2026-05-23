#!/usr/bin/env bash
# scripts/delegate.sh — Self-Healing Cost-Tiered LLM Router
#
# Usage:   scripts/delegate.sh <task_type> "<english_prompt>"
# Tasks:   search | lookup | summarize | reason | compare | scan | race
#
# Routing priority (always free first):
#   1. Gemini Free  (GEMINI_API_KEY direct — fastest, no routing overhead)
#   2. DeepSeek Free (DEEPSEEK_API_KEY direct — cheapest per token if paid)
#   3. OpenRouter Free models (via OPENROUTER_API_KEY)
#   4. Groq Free    (GROQ_API_KEY)
#   5. Paid fallback (OpenRouter auto / GPT-4o-mini / Haiku)
#
# Self-healing:
#   When ALL models fail → classify why → scout fresh models → retry once
#   model-not-found  → update-model-roster.sh → retry with new models
#   rate-limit       → report + suggest race mode or retry later
#   auth-error       → report which key to check
#   network          → report + retry once after 3s
#
# Exit:  0=ok  1=all failed  2=no keys  3=bad args

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROSTER_CONF="$REPO_ROOT/wiki/context/model-roster.conf"
UPDATE_SCRIPT="$REPO_ROOT/scripts/update-model-roster.sh"

# ─── Load dynamic roster (graceful if missing) ────────────────────────────────
if [ -f "$ROSTER_CONF" ]; then source "$ROSTER_CONF" 2>/dev/null || true; fi

# ─── API key aliases (normalize alternate names → canonical names) ─────────────
# GOOGLE_AI_STUDIO_KEY is the name shown in Google AI Studio UI → alias to GEMINI_API_KEY
if [ -z "${GEMINI_API_KEY:-}" ] && [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; then
  export GEMINI_API_KEY="$GOOGLE_AI_STUDIO_KEY"
fi

# ─── Hardcoded defaults (Gemini first in every tier) ──────────────────────────
TIER1_PRIMARY="${TIER1_PRIMARY:-google/gemini-2.5-flash:free}"
TIER1_FALLBACK1="${TIER1_FALLBACK1:-deepseek/deepseek-chat-v3-0324:free}"
TIER1_FALLBACK2="${TIER1_FALLBACK2:-qwen/qwen3-235b-a22b:free}"
TIER1_FALLBACK3="${TIER1_FALLBACK3:-meta-llama/llama-3.3-70b-instruct:free}"

TIER2_PRIMARY="${TIER2_PRIMARY:-google/gemini-2.5-flash:free}"
TIER2_FALLBACK1="${TIER2_FALLBACK1:-deepseek/deepseek-r1:free}"
TIER2_FALLBACK2="${TIER2_FALLBACK2:-qwen/qwen3-235b-a22b:free}"
TIER2_FALLBACK3="${TIER2_FALLBACK3:-openrouter/auto}"

TIER3_PRIMARY="${TIER3_PRIMARY:-google/gemini-2.5-flash:free}"
TIER3_FALLBACK1="${TIER3_FALLBACK1:-qwen/qwen3-30b-a3b:free}"
TIER3_FALLBACK2="${TIER3_FALLBACK2:-openai/gpt-4o-mini}"

RACE_MODELS="${RACE_MODELS:-google/gemini-2.5-flash:free deepseek/deepseek-chat-v3-0324:free qwen/qwen3-235b-a22b:free}"

# ─── Args ─────────────────────────────────────────────────────────────────────
if [ $# -lt 2 ]; then
  echo "Usage: $0 <task_type> \"<english_prompt>\"" >&2
  echo "  task_type: search | lookup | summarize | reason | compare | scan | race" >&2
  exit 3
fi

TASK_TYPE="$1"
PROMPT="$2"
TIMEOUT="${DELEGATE_TIMEOUT:-60}"

case "$TASK_TYPE" in
  search|lookup|summarize)  TIER=1 ;;
  reason|compare)           TIER=2 ;;
  scan)                     TIER=3 ;;
  race)                     TIER=0 ;;
  *)
    echo "❌ Unknown task_type '$TASK_TYPE'" >&2
    echo "   Valid: search | lookup | summarize | reason | compare | scan | race" >&2
    exit 3 ;;
esac

# ─── Key check ────────────────────────────────────────────────────────────────
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ] && \
   [ -z "${OPENROUTER_API_KEY:-}" ] && [ -z "${GROQ_API_KEY:-}" ] && \
   [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "❌ No API keys found. Set at least one:" >&2
  echo "   OPENROUTER_API_KEY=sk-or-... (recommended — unlocks all models)" >&2
  echo "   GEMINI_API_KEY=AIza...        (Google Gemini 2.5 Flash free)" >&2
  echo "   DEEPSEEK_API_KEY=sk-...       (direct DeepSeek API)" >&2
  echo "   → claude.ai/code → Project Settings → Environment Variables" >&2
  exit 2
fi

# ─── JSON escape prompt ───────────────────────────────────────────────────────
ESCAPED=$(printf '%s' "$PROMPT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')

# ─── Failure tracking ─────────────────────────────────────────────────────────
declare -a TRIED_MODELS=()
declare -a FAIL_REASONS=()

_track_fail() {
  local model="$1" reason="$2"
  TRIED_MODELS+=("$model")
  FAIL_REASONS+=("$reason")
}

# ─── Response parser + error classifier ───────────────────────────────────────
# Writes response to stdout (exit 0) or classifies error to LAST_ERROR (exit 1)
LAST_ERROR=""
_extract_smart() {
  local fmt="$1"
  python3 "$(dirname "${BASH_SOURCE[0]}")/_extract_response.py" "$fmt"
}

# ─── Engine wrappers ──────────────────────────────────────────────────────────
try_gemini_direct() {
  # Direct Google AI Studio — free 1500 req/day, no OpenRouter fee
  [ -z "${GEMINI_API_KEY:-}" ] && return 1
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"contents\":[{\"parts\":[{\"text\":$ESCAPED}]}]}" 2>/dev/null) || {
      _track_fail "gemini-2.5-flash(direct)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart gemini 2>"$err_out"; then
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "gemini-2.5-flash(direct)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_deepseek_direct() {
  # Direct DeepSeek API — cheapest for deepseek models
  [ -z "${DEEPSEEK_API_KEY:-}" ] && return 1
  local model="$1"
  local native
  case "$model" in
    *deepseek-r1*|*reasoner*) native="deepseek-reasoner" ;;
    *deepseek*)               native="deepseek-chat" ;;
    *) return 1 ;;
  esac
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    https://api.deepseek.com/chat/completions \
    -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$native\",\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "deepseek-direct($native)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart openai 2>"$err_out"; then
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "deepseek-direct($native)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_openrouter_model() {
  local model="$1"
  [ -z "${OPENROUTER_API_KEY:-}" ] && return 1
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "openrouter($model)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart openai 2>"$err_out"; then
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "openrouter($model)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_groq_model() {
  [ -z "${GROQ_API_KEY:-}" ] && return 1
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"llama-3.3-70b-versatile\",\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "groq(llama-3.3-70b)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart openai 2>"$err_out"; then
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "groq(llama-3.3-70b)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_anthropic_haiku() {
  [ -z "${ANTHROPIC_API_KEY:-}" ] && return 1
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"claude-haiku-4-5\",\"max_tokens\":2048,\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "anthropic(haiku)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart anthropic 2>"$err_out"; then
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "anthropic(haiku)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

# ─── Parallel race mode ───────────────────────────────────────────────────────
run_race() {
  local tmpdir
  tmpdir=$(mktemp -d)
  trap "rm -rf '$tmpdir'" RETURN

  local pids=() models=()
  local i=0

  for model in $RACE_MODELS; do
    local out="$tmpdir/out_${i}" done_flag="$tmpdir/ok_${i}"
    (
      try_openrouter_model "$model" > "$out" 2>/dev/null && touch "$done_flag"
    ) &
    pids+=($!)
    models+=("$model")
    i=$((i+1))
  done

  local deadline=$(($(date +%s) + TIMEOUT))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    for j in $(seq 0 $((i-1))); do
      if [ -f "$tmpdir/ok_${j}" ] && [ -s "$tmpdir/out_${j}" ]; then
        cat "$tmpdir/out_${j}"
        for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
        return 0
      fi
    done
    local all_done=true
    for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null && { all_done=false; break; }; done
    $all_done && break
    sleep 0.2
  done

  # Race fallback: try Gemini direct (not via OpenRouter)
  try_gemini_direct && return 0
  return 1
}

# ─── Smart failure report + auto-heal ────────────────────────────────────────
show_failure_and_heal() {
  local count=${#TRIED_MODELS[@]}
  echo "" >&2
  echo "⚠️  All $count model(s) failed. Attempt log:" >&2
  for i in $(seq 0 $((count-1))); do
    echo "   ✗ ${TRIED_MODELS[$i]} → ${FAIL_REASONS[$i]}" >&2
  done

  # Classify dominant failure pattern
  local has_model_not_found=false
  local has_rate_limit=false
  local has_auth_error=false
  local has_network=false

  for reason in "${FAIL_REASONS[@]}"; do
    [[ "$reason" == MODEL_NOT_FOUND* ]] && has_model_not_found=true
    [[ "$reason" == RATE_LIMIT* ]]      && has_rate_limit=true
    [[ "$reason" == AUTH_ERROR* ]]      && has_auth_error=true
    [[ "$reason" == network* ]]         && has_network=true
  done

  if $has_auth_error; then
    echo "" >&2
    echo "🔑 AUTH ERROR detected — check your API key(s):" >&2
    echo "   Set via: claude.ai/code → Project Settings → Environment Variables" >&2
    echo "   Keys needed: OPENROUTER_API_KEY | GEMINI_API_KEY | DEEPSEEK_API_KEY" >&2
    return 1
  fi

  if $has_model_not_found; then
    echo "" >&2
    echo "🔄 Model(s) no longer available — scouting fresh lineup from OpenRouter..." >&2
    if [ -n "${OPENROUTER_API_KEY:-}" ] && [ -x "$UPDATE_SCRIPT" ]; then
      bash "$UPDATE_SCRIPT" >/dev/null 2>&1 && {
        echo "✅ Roster updated — retrying with new models..." >&2
        # Reload updated roster
        [ -f "$ROSTER_CONF" ] && source "$ROSTER_CONF" 2>/dev/null || true
        return 2  # signal: retry
      } || echo "⚠️  Scout failed (network?) — using cached roster" >&2
    else
      echo "   (set OPENROUTER_API_KEY to enable auto-scout)" >&2
    fi
    return 1
  fi

  if $has_rate_limit; then
    echo "" >&2
    echo "⏱️  RATE LIMIT hit on all models. Options:" >&2
    echo "   • Try again in 1-2 minutes" >&2
    echo "   • Use 'race' mode to hit multiple providers simultaneously" >&2
    echo "   • Add more API keys (GROQ_API_KEY is free + high rate limit)" >&2
    return 1
  fi

  if $has_network; then
    echo "" >&2
    echo "🌐 NETWORK issues — retrying in 3s..." >&2
    sleep 3
    return 2  # signal: retry
  fi

  echo "" >&2
  echo "💡 Try: bash scripts/update-model-roster.sh  (scout current free models)" >&2
  return 1
}

# ─── Run tier with auto-heal ──────────────────────────────────────────────────
run_tier() {
  local attempt="${1:-1}"

  case "$TIER" in
    0)  # race mode — parallel
      run_race && return 0
      ;;

    1)  # search / lookup / summarize — Gemini free FIRST
      try_gemini_direct                          && return 0
      try_openrouter_model "$TIER1_PRIMARY"      && return 0
      try_deepseek_direct  "$TIER1_FALLBACK1"    && return 0
      try_openrouter_model "$TIER1_FALLBACK1"    && return 0
      try_openrouter_model "$TIER1_FALLBACK2"    && return 0
      try_groq_model                             && return 0
      try_openrouter_model "$TIER1_FALLBACK3"    && return 0
      ;;

    2)  # reason / compare — Gemini free FIRST
      try_gemini_direct                          && return 0
      try_openrouter_model "$TIER2_PRIMARY"      && return 0
      try_deepseek_direct  "$TIER2_FALLBACK1"    && return 0
      try_openrouter_model "$TIER2_FALLBACK1"    && return 0
      try_openrouter_model "$TIER2_FALLBACK2"    && return 0
      try_openrouter_model "$TIER2_FALLBACK3"    && return 0
      ;;

    3)  # scan / long-context — Gemini free FIRST
      try_gemini_direct                          && return 0
      try_openrouter_model "$TIER3_PRIMARY"      && return 0
      try_openrouter_model "$TIER3_FALLBACK1"    && return 0
      try_openrouter_model "$TIER3_FALLBACK2"    && return 0
      try_anthropic_haiku                        && return 0
      ;;
  esac

  # All models failed — smart diagnosis + possible heal
  local heal_result
  show_failure_and_heal; heal_result=$?

  if [ "$heal_result" -eq 2 ] && [ "$attempt" -eq 1 ]; then
    # Healed (roster updated / network retry) — try once more
    echo "🔁 Retrying with updated configuration..." >&2
    TRIED_MODELS=()
    FAIL_REASONS=()
    run_tier 2
    return $?
  fi

  return 1
}

# ─── Execute ──────────────────────────────────────────────────────────────────
run_tier 1
