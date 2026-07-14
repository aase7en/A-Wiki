#!/usr/bin/env bash
# scripts/swarm/subagent_fallback.sh — Subagent Rate-Limit Fallback Wrapper
#
# When a subagent call returns "Provider rate limited the model request"
# (HTTP 429), the primary agent re-invokes the failed subagent through this
# script. It walks a fallback chain of providers until one succeeds.
#
# Usage:
#   bash scripts/swarm/subagent_fallback.sh <subagent_type> "<prompt>"
#   bash scripts/swarm/subagent_fallback.sh --dry-run <subagent_type> "<prompt>"
#   bash scripts/swarm/subagent_fallback.sh --chain        # print the chain
#
# Fallback chain (first success wins):
#   1. deepseek-v4-flash      (paid, cheap — separate bucket)
#   2. openrouter/free        (free — OpenRouter quota)
#   3. glm-5.2                (Z.ai — separate bucket)
#   4. gemini-3.5-flash       (free — last resort, single call only)
#
# Design notes:
#   - This is a SHIM, not an executor. ZCode's Agent tool is invoked by the
#     primary agent itself; this script exists to (a) document the chain,
#     (b) let the primary agent call it as a bash command to emit the next
#     model to try, and (c) provide --dry-run for testing.
#   - The primary agent reads the printed "NEXT_MODEL=<...>" line and re-
#     invokes the subagent with that model override.
#
# Exit codes:
#   0 = success (printed a NEXT_MODEL recommendation or ran --dry-run/--chain)
#   1 = bad args
#   2 = exhausted chain
#
# See: docs/protocols/subagent-model-routing.md

set -euo pipefail

CHAIN=(
  "deepseek-v4-flash"
  "openrouter/free"
  "glm-5.2"
  "gemini-3.5-flash"
)

print_chain() {
  echo "FALLBACK_CHAIN:"
  local i=1
  for m in "${CHAIN[@]}"; do
    echo "  $i. $m"
    i=$((i+1))
  done
}

usage() {
  cat <<EOF
Usage: subagent_fallback.sh [--dry-run|--chain] <subagent_type> "<prompt>"

  --dry-run   Print the model each step would try, then exit 0 (no API call).
  --chain     Print the fallback chain and exit 0.
  (no flag)   Walk the chain, printing NEXT_MODEL=<model> for each step until
              the primary agent reports success. State is kept in
              .tmp/subagent_fallback_state.json keyed by subagent_type.

The primary agent should:
  1. Invoke this script with the failed subagent_type + original prompt.
  2. Read the printed NEXT_MODEL line.
  3. Re-invoke the subagent with that model override.
  4. On success, run: bash subagent_fallback.sh --reset <subagent_type>
  5. On another 429, repeat from step 1 (the script advances the cursor).
EOF
}

# ---- arg parsing ----
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="walk"
if [[ "${1:-}" == "--chain" ]]; then
  print_chain
  exit 0
elif [[ "${1:-}" == "--dry-run" ]]; then
  MODE="dry"
  shift
elif [[ "${1:-}" == "--reset" ]]; then
  shift
  SUBAGENT_TYPE="${1:-}"
  [[ -z "$SUBAGENT_TYPE" ]] && { echo "ERR: --reset needs <subagent_type>" >&2; exit 1; }
  STATE_FILE="$REPO_ROOT/.tmp/subagent_fallback_state.json"
  mkdir -p "$REPO_ROOT/.tmp"
  python3 - "$STATE_FILE" "$SUBAGENT_TYPE" <<'PY'
import json, sys, os
path, sa = sys.argv[1], sys.argv[2]
state = {}
if os.path.exists(path):
    try: state = json.load(open(path))
    except: pass
state.pop(sa, None)
open(path,"w").write(json.dumps(state))
print(f"RESET: {sa}")
PY
  exit 0
fi

SUBAGENT_TYPE="${1:-}"
PROMPT="${2:-}"
if [[ -z "$SUBAGENT_TYPE" ]]; then
  usage >&2
  exit 1
fi

STATE_FILE="$REPO_ROOT/.tmp/subagent_fallback_state.json"
mkdir -p "$REPO_ROOT/.tmp"

# ---- state: cursor per subagent_type ----
get_cursor() {
  python3 - "$STATE_FILE" "$SUBAGENT_TYPE" <<'PY'
import json, os, sys
path, sa = sys.argv[1], sys.argv[2]
state = {}
if os.path.exists(path):
    try: state = json.load(open(path))
    except: pass
print(state.get(sa, 0))
PY
}

set_cursor() {
  local val="$1"
  python3 - "$STATE_FILE" "$SUBAGENT_TYPE" "$val" <<'PY'
import json, os, sys
path, sa, val = sys.argv[1], sys.argv[2], int(sys.argv[3])
state = {}
if os.path.exists(path):
    try: state = json.load(open(path))
    except: pass
state[sa] = val
open(path,"w").write(json.dumps(state))
PY
}

# ---- walk the chain ----
if [[ "$MODE" == "dry" ]]; then
  echo "DRY_RUN for subagent_type=$SUBAGENT_TYPE"
  echo "Prompt (truncated): ${PROMPT:0:80}..."
  echo
  di=0
  for m in "${CHAIN[@]}"; do
    di=$((di+1))
    echo "  step $di would try: NEXT_MODEL=$m"
  done
  echo
  echo "EXIT_OK (dry-run, no API call)"
  exit 0
fi

cursor="$(get_cursor)"
if [[ "$cursor" -ge "${#CHAIN[@]}" ]]; then
  echo "EXHAUSTED: fallback chain depleted for $SUBAGENT_TYPE" >&2
  echo "Run: bash $0 --reset $SUBAGENT_TYPE   to restart." >&2
  exit 2
fi

# array index from cursor
MODEL="${CHAIN[$cursor]}"
echo "NEXT_MODEL=$MODEL"
echo "STEP=$((cursor+1))/${#CHAIN[@]}"
echo "SUBAGENT_TYPE=$SUBAGENT_TYPE"
echo "NOTE: primary agent should re-invoke $SUBAGENT_TYPE with model=$MODEL"
echo "      on success: bash $0 --reset $SUBAGENT_TYPE"
echo "      on 429:     re-run this script to advance to step $((cursor+2))"

# advance cursor for next call
set_cursor $((cursor+1))
exit 0
