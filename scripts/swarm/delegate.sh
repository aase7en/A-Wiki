#!/usr/bin/env bash
# scripts/delegate.sh — Self-Healing Cost-Tiered LLM Router
#
# Usage:   scripts/delegate.sh <task_type> "<english_prompt>"
# Tasks:   search | lookup | summarize | reason | compare | scan | race
#
# Routing priority (scout first, then cheapest capable):
#   1. free-current dynamic roster
#   2. cheap-capable provider route discovered at runtime
#   3. platform-low-scout / low-cost CLI agent when available
#   4. provider seeds only if scout cannot produce a live choice
#
# Self-healing:
#   When ALL models fail → classify why → scout fresh models → retry once
#   model-not-found  → model-scout-current.py → update-model-roster.sh → retry
#   rate-limit       → report + suggest race mode or retry later
#   auth-error       → report which key to check
#   network          → report + retry once after 3s
#
# Exit:  0=ok  1=all failed  2=no keys  3=bad args

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROSTER_CONF="$REPO_ROOT/wiki/context/model-roster.conf"
POLICY_SCRIPT="$REPO_ROOT/scripts/model-router-policy.py"
POLICY_CONF="${MODEL_ROUTER_POLICY_CONF:-$REPO_ROOT/.tmp/model-router-policy.conf}"
SCOUT_SCRIPT="$REPO_ROOT/scripts/model-scout-current.py"
SCOUT_JSON="${MODEL_SCOUT_CURRENT_JSON:-$REPO_ROOT/.tmp/model-scout-current.json}"
SCOUT_REPORT="${MODEL_SCOUT_CURRENT_REPORT:-$REPO_ROOT/.tmp/model-scout-current.md}"
UPDATE_SCRIPT="$REPO_ROOT/scripts/update-model-roster.sh"
LOAD_DRIVE_KEYS_SH="$REPO_ROOT/scripts/hooks/load-drive-keys.sh"

refresh_model_scout() {
  local mode="${1:-cached}"
  [ -f "$SCOUT_SCRIPT" ] || return 1
  if [ "$mode" != "force" ] && [ -f "$SCOUT_JSON" ] && [ -z "${MODEL_SCOUT_FORCE:-}" ]; then
    return 0
  fi
  python3 "$SCOUT_SCRIPT" --out "$SCOUT_JSON" --report "$SCOUT_REPORT" --quiet >/dev/null 2>&1 || \
    python3 "$SCOUT_SCRIPT" --offline --out "$SCOUT_JSON" --report "$SCOUT_REPORT" --quiet >/dev/null 2>&1 || true
}

CAPABILITY_SCOUT_SCRIPT="$REPO_ROOT/scripts/model-capability-scout.py"
refresh_capability_scout() {
  # Best-effort leaderboard capability refresh (offline-ok). Never blocks routing.
  [ -f "$CAPABILITY_SCOUT_SCRIPT" ] || return 0
  [ -f "$REPO_ROOT/.tmp/model-capability-cache.json" ] && [ -z "${CAPABILITY_SCOUT_FORCE:-}" ] && return 0
  python3 "$CAPABILITY_SCOUT_SCRIPT" --offline-ok --quiet >/dev/null 2>&1 &
  disown "$!" 2>/dev/null || true
}

# ─── Load local router policy (graceful if missing) ──────────────────────────
refresh_model_scout cached || true
refresh_capability_scout || true

# Ensure Live Dashboard is running (fire-and-forget — no-op if already up)
if [ "${AWIKI_DISABLE_DASHBOARD_AUTOSTART:-0}" != "1" ] && [ -f "$REPO_ROOT/scripts/dashboard-ensure.sh" ]; then
  bash "$REPO_ROOT/scripts/dashboard-ensure.sh" &>/dev/null &
fi
if [ -f "$POLICY_SCRIPT" ]; then
  python3 "$POLICY_SCRIPT" --scout "$SCOUT_JSON" --out "$POLICY_CONF" --quiet >/dev/null 2>&1 || true
fi
if [ -f "$POLICY_CONF" ]; then
  source "$POLICY_CONF" 2>/dev/null || true
elif [ -f "$ROSTER_CONF" ]; then
  source "$ROSTER_CONF" 2>/dev/null || true
fi

# ─── API key aliases (normalize alternate names → canonical names) ─────────────
# GOOGLE_AI_STUDIO_KEY is the name shown in Google AI Studio UI → alias to GEMINI_API_KEY
if [ -z "${GEMINI_API_KEY:-}" ] && [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; then
  export GEMINI_API_KEY="$GOOGLE_AI_STUDIO_KEY"
fi

# ─── Drive-backed key fallback ─────────────────────────────────────────────────
# SessionStart hooks cannot persist exports back into Codex's parent process.
# To make delegation work reliably from Desktop/CLI, delegate.sh must load
# missing keys itself on demand.
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ] && \
   [ -z "${OPENROUTER_API_KEY:-}" ] && [ -z "${GROQ_API_KEY:-}" ] && \
   [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$LOAD_DRIVE_KEYS_SH" ]; then
  # shellcheck source=scripts/hooks/load-drive-keys.sh
  source "$LOAD_DRIVE_KEYS_SH" >/dev/null 2>&1 || true
fi

if [ -z "${GEMINI_API_KEY:-}" ] && [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; then
  export GEMINI_API_KEY="$GOOGLE_AI_STUDIO_KEY"
fi

# ─── Dashboard-saved key fallback ─────────────────────────────────────────────
# Keys saved via live dashboard Settings → API Keys tab (stored gitignored)
DASHBOARD_KEYS_ENV="$REPO_ROOT/.tmp/live-dashboard-keys.env"
if [ -f "$DASHBOARD_KEYS_ENV" ]; then
  # shellcheck source=/dev/null
  set -a; source "$DASHBOARD_KEYS_ENV" 2>/dev/null || true; set +a
fi

# ─── Emergency seed defaults only; seed only; replaced by scout ───────────────
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

GEMINI_DIRECT_MODEL_SEED="${GEMINI_DIRECT_MODEL_SEED:-gemini-2.5-flash}"
GEMINI_DIRECT_MODEL="${GEMINI_DIRECT_MODEL:-$GEMINI_DIRECT_MODEL_SEED}"
GROQ_DIRECT_MODEL_SEED="${GROQ_DIRECT_MODEL_SEED:-llama-3.3-70b-versatile}"
GROQ_DIRECT_MODEL="${GROQ_DIRECT_MODEL:-$GROQ_DIRECT_MODEL_SEED}"
ANTHROPIC_LOW_MODEL_SEED="${ANTHROPIC_LOW_MODEL_SEED:-claude-haiku-4-5}"
ANTHROPIC_LOW_MODEL="${ANTHROPIC_LOW_MODEL:-$ANTHROPIC_LOW_MODEL_SEED}"

# GLM / Z.ai direct route (Z.ai international endpoint; editable via dashboard)
ZHIPU_DIRECT_MODEL_SEED="${ZHIPU_DIRECT_MODEL_SEED:-glm-4.6}"
ZHIPU_DIRECT_MODEL="${ZHIPU_DIRECT_MODEL:-$ZHIPU_DIRECT_MODEL_SEED}"
ZHIPU_API_URL="${ZHIPU_API_URL:-https://api.z.ai/api/paas/v4/chat/completions}"

# ─── Model config (live dashboard settings) ────────────────────────────────────
# Reads .tmp/model-config.json (saved by dashboard Settings panel) to disable
# specific models and apply custom model IDs without touching this file.
MODEL_CONFIG_JSON="$REPO_ROOT/.tmp/model-config.json"
if [ -f "$MODEL_CONFIG_JSON" ]; then
  eval "$(python3 -c "
import json, sys
try:
    cfg = json.load(open('$MODEL_CONFIG_JSON'))
    for m in cfg.get('models', []):
        mid = m.get('id', '').upper().replace('-', '_')
        if not m.get('enabled', True) and mid:
            print('export AWIKI_DISABLE_' + mid + '=1')
        model_val = m.get('model_id', '')
        if model_val:
            if m.get('id') == 'gemini':    print('export GEMINI_DIRECT_MODEL=' + model_val)
            elif m.get('id') == 'groq':    print('export GROQ_DIRECT_MODEL=' + model_val)
            elif m.get('id') == 'anthropic': print('export ANTHROPIC_LOW_MODEL=' + model_val)
            elif m.get('id') == 'zhipu':
                print('export ZHIPU_DIRECT_MODEL=' + model_val)
                api_url = m.get('api_url', '')
                if api_url: print('export ZHIPU_API_URL=' + api_url)
except Exception:
    pass
" 2>/dev/null)" || true
fi

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
   [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${ZHIPU_API_KEY:-}" ]; then
  echo "❌ No API keys found. Set at least one:" >&2
  echo "   OPENROUTER_API_KEY=sk-or-... (recommended — unlocks all models)" >&2
  echo "   GEMINI_API_KEY=AIza...        (direct Google AI Studio route; free)" >&2
  echo "   DEEPSEEK_API_KEY=sk-...       (direct DeepSeek route; free tier)" >&2
  echo "   ZHIPU_API_KEY=...             (GLM 5.2 / Z.ai; set via dashboard ⚙️)" >&2
  echo "   → Dashboard: http://localhost:7790/ → ⚙️ Settings → API Keys" >&2
  echo "   → Or: claude.ai/code → Project Settings → Environment Variables" >&2
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
  _log_event "delegate_fail" "model=$model" "reason=$reason"
}

# ─── Cost annotator ───────────────────────────────────────────────────────────
# Appends a cost estimate line to stdout after the response body.
# Estimates are labels only. Current pricing must come from model-scout-current.py.
# Only active when MIN_COST_ANNOTATE=true (off by default).
MIN_COST_ANNOTATE="${MIN_COST_ANNOTATE:-false}"
_cost_annotate() {
  local model_name="$1"
  $MIN_COST_ANNOTATE || return 0
  # Rough per-token ranges (input + output, 500 tokens avg)
  case "$model_name" in
    *gemini*flash*|*gemini-2.5-flash*)   local cost="~$0.00 (free tier)" ;;
    *deepseek*r1*|*reasoner*)            local cost="~$0.00014" ;;
    *deepseek*chat*v3*)                  local cost="~$0.00009" ;;
    *deepseek*)                          local cost="~$0.00008" ;;
    *qwen3*235b*|*qwen3-235b*)           local cost="~$0.00 (free)" ;;
    *llama-3.3*70b*|*llama*3.3*70b*)     local cost="~$0.00 (free/Groq)" ;;
    *qwen3*30b*|*qwen3-30b*)             local cost="~$0.00 (free)" ;;
    *gpt-4o-mini*)                       local cost="~$0.00015" ;;
    *claude*haiku*|*claude-haiku*)       local cost="~$0.00025" ;;
    *glm*|*zhipu*)                       local cost="~$0.0001 (GLM/Z.ai)" ;;
    *openrouter/auto*)                   local cost="~$0.001 (varies)" ;;
    *)                                   local cost="~$0.00 (unknown/free)" ;;
  esac
  echo ""
  echo "# [cost-estimate] ${cost}  (model: ${model_name})"
}

# ─── Response parser + error classifier ───────────────────────────────────────
# Writes response to stdout (exit 0) or classifies error to LAST_ERROR (exit 1)
LAST_ERROR=""
# _extract_response.py lives in scripts/ (one level up from scripts/swarm/).
# Resolve via REPO_ROOT so the path is correct regardless of caller CWD.
EXTRACT_PY="$REPO_ROOT/scripts/_extract_response.py"
_extract_smart() {
  local fmt="$1"
  python3 "$EXTRACT_PY" "$fmt"
}

# ─── Live Dashboard Event Logger ──────────────────────────────────────────────
EVENT_LOGGER="$REPO_ROOT/scripts/live-dashboard/event_logger.py"
_log_event() {
  # Non-blocking: fire-and-forget background python3 call
  [ -f "$EVENT_LOGGER" ] && python3 "$EVENT_LOGGER" "$@" >/dev/null 2>&1 &
  disown "$!" 2>/dev/null || true
}

# ─── Provider enable guard ─────────────────────────────────────────────────────
# Dashboard toggles write AWIKI_DISABLE_<ID>=1 (via model-config.json parser above).
# Each engine calls this so disabled providers are skipped (return 1 → fallthrough).
_provider_enabled() {
  local var="AWIKI_DISABLE_${1}"
  [ -z "${!var:-}" ]
}

# ─── Engine wrappers ──────────────────────────────────────────────────────────
try_gemini_direct() {
  # Direct Google AI Studio — free 1500 req/day, no OpenRouter fee
  [ -z "${GEMINI_API_KEY:-}" ] && return 1
  _provider_enabled GEMINI || return 1
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=${GEMINI_DIRECT_MODEL}(gemini-direct)" "task=$TASK_TYPE"
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_DIRECT_MODEL}:generateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"contents\":[{\"parts\":[{\"text\":$ESCAPED}]}]}" 2>/dev/null) || {
      _track_fail "${GEMINI_DIRECT_MODEL}(direct)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart gemini 2>"$err_out"; then
    _log_event "delegate_done" "model=${GEMINI_DIRECT_MODEL}(gemini-direct)" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "${GEMINI_DIRECT_MODEL}(direct)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_deepseek_direct() {
  # Direct DeepSeek API aliases are provider aliases, not durable policy model ids.
  [ -z "${DEEPSEEK_API_KEY:-}" ] && return 1
  _provider_enabled DEEPSEEK || return 1
  local model="$1"
  local native
  case "$model" in
    *deepseek-r1*|*reasoner*) native="deepseek-reasoner" ;;
    *deepseek*)               native="deepseek-chat" ;;
    *) return 1 ;;
  esac
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=deepseek-direct($native)" "task=$TASK_TYPE"
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
    _log_event "delegate_done" "model=deepseek-direct($native)" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "deepseek-direct($native)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_openrouter_model() {
  local model="$1"
  [ -z "${OPENROUTER_API_KEY:-}" ] && return 1
  _provider_enabled OPENROUTER || return 1
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=$model" "task=$TASK_TYPE"
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
    _log_event "delegate_done" "model=$model" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "openrouter($model)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_groq_model() {
  [ -z "${GROQ_API_KEY:-}" ] && return 1
  _provider_enabled GROQ || return 1
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=$GROQ_DIRECT_MODEL(groq)" "task=$TASK_TYPE"
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$GROQ_DIRECT_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "groq($GROQ_DIRECT_MODEL)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart openai 2>"$err_out"; then
    _log_event "delegate_done" "model=$GROQ_DIRECT_MODEL(groq)" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    _cost_annotate "$GROQ_DIRECT_MODEL(groq)"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "groq($GROQ_DIRECT_MODEL)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_anthropic_haiku() {
  [ -z "${ANTHROPIC_API_KEY:-}" ] && return 1
  _provider_enabled ANTHROPIC || return 1
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=$ANTHROPIC_LOW_MODEL(anthropic)" "task=$TASK_TYPE"
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$ANTHROPIC_LOW_MODEL\",\"max_tokens\":2048,\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "anthropic(haiku)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart anthropic 2>"$err_out"; then
    _log_event "delegate_done" "model=$ANTHROPIC_LOW_MODEL(anthropic)" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    _cost_annotate "$ANTHROPIC_LOW_MODEL"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "anthropic(haiku)" "$LAST_ERROR"
  rm -f "$err_out"; return 1
}

try_zhipu_direct() {
  # GLM / Z.ai — OpenAI-compatible chat completions (Bearer auth).
  # Endpoint + model id are dashboard-configurable (Z.ai international by default).
  [ -z "${ZHIPU_API_KEY:-}" ] && return 1
  _provider_enabled ZHIPU || return 1
  local _t0; _t0=$(date +%s 2>/dev/null || echo 0)
  _log_event "delegate_start" "model=$ZHIPU_DIRECT_MODEL(zhipu)" "task=$TASK_TYPE"
  local err_out
  err_out=$(mktemp)
  local resp
  resp=$(curl -sS --max-time "$TIMEOUT" -X POST \
    "$ZHIPU_API_URL" \
    -H "Authorization: Bearer $ZHIPU_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$ZHIPU_DIRECT_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":$ESCAPED}]}" 2>/dev/null) || {
      _track_fail "zhipu($ZHIPU_DIRECT_MODEL)" "network-timeout"
      rm -f "$err_out"; return 1
    }
  if printf '%s' "$resp" | _extract_smart openai 2>"$err_out"; then
    _log_event "delegate_done" "model=$ZHIPU_DIRECT_MODEL(zhipu)" "duration_ms=$(( ( $(date +%s 2>/dev/null || echo $_t0) - _t0 ) * 1000 ))"
    _cost_annotate "$ZHIPU_DIRECT_MODEL(zhipu)"
    rm -f "$err_out"; return 0
  fi
  LAST_ERROR=$(cat "$err_out" 2>/dev/null || echo "unknown")
  _track_fail "zhipu($ZHIPU_DIRECT_MODEL)" "$LAST_ERROR"
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
  if [ "$count" -gt 0 ]; then
    for i in $(seq 0 $((count-1))); do
      echo "   ✗ ${TRIED_MODELS[$i]} → ${FAIL_REASONS[$i]}" >&2
    done
  fi

  # Classify dominant failure pattern
  local has_model_not_found=false
  local has_rate_limit=false
  local has_auth_error=false
  local has_network=false

  if [ "$count" -gt 0 ]; then
    for reason in "${FAIL_REASONS[@]}"; do
      [[ "$reason" == MODEL_NOT_FOUND* ]] && has_model_not_found=true
      [[ "$reason" == RATE_LIMIT* ]]      && has_rate_limit=true
      [[ "$reason" == AUTH_ERROR* ]]      && has_auth_error=true
      [[ "$reason" == network* ]]         && has_network=true
    done
  fi

  if $has_auth_error; then
    echo "" >&2
    echo "🔑 AUTH ERROR detected — check your API key(s):" >&2
    refresh_model_scout force || true
    echo "   Set via: claude.ai/code → Project Settings → Environment Variables" >&2
    echo "   Keys needed: OPENROUTER_API_KEY | GEMINI_API_KEY | DEEPSEEK_API_KEY" >&2
    return 1
  fi

  if $has_model_not_found; then
    echo "" >&2
    echo "🔄 Model(s) no longer available — scouting current model/pricing..." >&2
    refresh_model_scout force || true
    if [ -n "${OPENROUTER_API_KEY:-}" ] && [ -x "$UPDATE_SCRIPT" ]; then
      bash "$UPDATE_SCRIPT" >/dev/null 2>&1 && {
        echo "✅ Roster updated — retrying with new models..." >&2
        # Reload updated router policy
        if [ -f "$POLICY_SCRIPT" ]; then
          python3 "$POLICY_SCRIPT" --scout "$SCOUT_JSON" --out "$POLICY_CONF" --quiet >/dev/null 2>&1 || true
        fi
        [ -f "$POLICY_CONF" ] && source "$POLICY_CONF" 2>/dev/null || true
        [ ! -f "$POLICY_CONF" ] && [ -f "$ROSTER_CONF" ] && source "$ROSTER_CONF" 2>/dev/null || true
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
    refresh_model_scout force || true
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
  echo "💡 Try: python3 scripts/model-scout-current.py && bash scripts/update-model-roster.sh" >&2
  return 1
}

# ─── Capability-based ranking (cost-first preserved) ──────────────────────────
# Reorders the engine try-sequence by leaderboard capability WITHIN each cost
# class. cost_rank is the PRIMARY sort key → a paid model can never jump ahead of
# a free one; capability only breaks ties inside the same cost class.
CAPABILITY_CACHE="$REPO_ROOT/.tmp/model-capability-cache.json"
CAPABILITY_SCORECARD="$REPO_ROOT/wiki/context/model-capability-scores.json"

_capability_dimension() {
  case "$TASK_TYPE" in
    reason|compare)           echo reasoning ;;
    scan)                     echo terminal_bench ;;
    search|lookup|summarize)  echo speed ;;
    *)                        echo speed ;;
  esac
}

# Args: <dimension> <line...>  where line = "engine|model_id|cost_rank"
# Emits the lines reordered. Degrades to unchanged order if no scorecard/cache.
_rank_by_capability() {
  local dim="$1"; shift
  local card="$CAPABILITY_CACHE"
  [ -f "$card" ] || card="$CAPABILITY_SCORECARD"
  if [ ! -f "$card" ]; then
    printf '%s\n' "$@"   # no data → unchanged cost-first order
    return 0
  fi
  printf '%s\n' "$@" | python3 -c '
import sys, json
dim = sys.argv[1]; card = sys.argv[2]
try:
    fams = json.load(open(card)).get("families", {})
except Exception:
    sys.stdout.write(sys.stdin.read()); sys.exit(0)  # bad json → unchanged
def score(mid):
    m = (mid or "").lower()
    for f in fams.values():
        if any(s in m for s in f.get("match", [])):
            return f.get(dim, 50)
    return 50
rows = []
for i, ln in enumerate(sys.stdin.read().splitlines()):
    if not ln.strip(): continue
    parts = (ln.split("|") + ["", "", "9"])[:3]
    eng, mid, cr = parts
    try: cr = int(cr)
    except ValueError: cr = 9
    rows.append((cr, -score(mid), i, ln))   # i = stable tiebreak
rows.sort()
for r in rows: print(r[3])
' "$dim" "$card"
}

# Dispatch a capability-ranked candidate list (cost-first within each rank).
# Args: <dimension> <line...>  line = "engine|model_id|cost_rank"
_run_ranked() {
  local dim="$1"; shift
  local ranked engine model_id _rest
  ranked=$(_rank_by_capability "$dim" "$@")
  while IFS='|' read -r engine model_id _rest; do
    [ -z "$engine" ] && continue
    case "$engine" in
      gemini)     try_gemini_direct            && return 0 ;;
      deepseek)   try_deepseek_direct  "$model_id" && return 0 ;;
      openrouter) try_openrouter_model "$model_id" && return 0 ;;
      groq)       try_groq_model             && return 0 ;;
      anthropic)  try_anthropic_haiku        && return 0 ;;
      zhipu)      try_zhipu_direct           && return 0 ;;
    esac
  done <<< "$ranked"
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

    2)  # reason / compare — capability-ranked within cost class (free first)
      _run_ranked "$(_capability_dimension)" \
        "gemini|$GEMINI_DIRECT_MODEL|0" \
        "openrouter|$TIER2_PRIMARY|0" \
        "openrouter|$TIER2_FALLBACK1|0" \
        "openrouter|$TIER2_FALLBACK2|0" \
        "deepseek|$TIER2_FALLBACK1|1" \
        "zhipu|$ZHIPU_DIRECT_MODEL|1" \
        "openrouter|$TIER2_FALLBACK3|2" \
        && return 0
      ;;

    3)  # scan / long-context — capability-ranked within cost class (free first)
      _run_ranked "$(_capability_dimension)" \
        "gemini|$GEMINI_DIRECT_MODEL|0" \
        "openrouter|$TIER3_PRIMARY|0" \
        "openrouter|$TIER3_FALLBACK1|0" \
        "zhipu|$ZHIPU_DIRECT_MODEL|1" \
        "openrouter|$TIER3_FALLBACK2|2" \
        "anthropic|$ANTHROPIC_LOW_MODEL|2" \
        && return 0
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
# Fail loudly if the response extractor is missing — otherwise every model call
# fails identically and the auto-heal misdiagnoses the root cause.
if [ ! -f "$EXTRACT_PY" ]; then
  echo "❌ Response extractor not found: $EXTRACT_PY" >&2
  echo "   delegate.sh cannot parse model responses without it." >&2
  echo "   Expected at scripts/_extract_response.py (repo root: $REPO_ROOT)" >&2
  exit 1
fi

run_tier 1
