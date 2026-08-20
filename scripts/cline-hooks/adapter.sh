#!/usr/bin/env bash
# -*- mode: shell-script; -*-
# ============================================================================
# Cline → A-Wiki Hook Adapter
# ============================================================================
# Receives Cline native hook JSON on stdin, forwards to hooks_runner.py,
# and returns Cline-compatible JSON response on stdout.
#
# Hook event name is inferred from the symlink name that invoked this script.
#
# Usage (via .clinerules/hooks/* symlinks):
#   echo '{"preToolUse":{"toolName":"write_to_file","parameters":{...}}}' \
#     | bash scripts/cline-hooks/adapter.sh
#
# Cline response format:
#   {"cancel": false, "contextModification": "", "errorMessage": ""}
#   {"cancel": true,  "contextModification": "", "errorMessage": "reason"}
#
# Exit codes:
#   0 — hook passed (no block)
#   1 — hook blocked the operation (rare, prefer cancel:true in JSON)
#
# Environment:
#   HOOK_SKIP       — comma-separated hooks to skip (forwarded to runner)
#   HOOK_TIMEOUT    — seconds per hook (forwarded to runner, default 5)
#   AWIKI_PYTHON    — explicit Python interpreter (default: python3)
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_RUNNER="$REPO_ROOT/scripts/hooks_runner.py"
LOG_FILE="${CLINE_HOOK_LOG_FILE:-$REPO_ROOT/logs/cline-hooks.log}"
PYTHON_BIN="${AWIKI_PYTHON:-python3}"

# ── Infer event name from the symlink name that invoked us ──────────────────
# $0 could be: .clinerules/hooks/PreToolUse  → event = PreToolUse
#              .clinerules/hooks/PostToolUse → event = PostToolUse
#              etc.
EVENT="${CLINE_HOOK_EVENT:-}"
if [ -z "$EVENT" ]; then
  # Derive from script name (last component of $0)
  EVENT="$(basename "$0")"
  # Fallback: if called directly as adapter.sh, default to PreToolUse
  [ "$EVENT" = "adapter.sh" ] && EVENT="PreToolUse"
fi

# ── Read Cline JSON from stdin ──────────────────────────────────────────────
INPUT="$(cat)"

# ── Parse only optional log metadata; never transform the provider payload ──
# Malformed JSON is allowed to flow unchanged to the canonical runner.
TOOL_NAME="$(printf '%s' "$INPUT" | "$PYTHON_BIN" -c '
import json, sys
try:
    data = json.load(sys.stdin)
    inner = data.get("preToolUse") or data.get("postToolUse") or {}
    value = inner.get("toolName", "") if isinstance(inner, dict) else ""
    sys.stdout.write(str(value))
except Exception:
    pass
' 2>/dev/null || true)"

# ── Log the incoming event ──────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] event=$EVENT tool=$TOOL_NAME" >> "$LOG_FILE"

# ── Preserve provider-native payload for canonical normalization ─────────────
# Do not fabricate `{}` on malformed input. The canonical provider boundary
# in hooks_runner.py owns malformed-vs-empty semantics.

# ── Forward to hooks_runner.py ──────────────────────────────────────────────
# hooks_runner.py exit codes:
#   0 → pass (no block)
#   2 → BLOCK (Iron Law violation)
#   other non-zero → pass with warning
STDERR_FILE="$(mktemp)"
EXIT_CODE=0
printf '%s' "$INPUT" | "$PYTHON_BIN" "$HOOKS_RUNNER" --provider cline --event "$EVENT" 2>"$STDERR_FILE" || EXIT_CODE=$?

STDERR_OUT="$(cat "$STDERR_FILE" 2>/dev/null || true)"
rm -f "$STDERR_FILE"

# ── Convert result → Cline response format ──────────────────────────────────
if [ "$EXIT_CODE" -eq 2 ]; then
  # BLOCK — return cancel:true
  BLOCK_REASON="${STDERR_OUT:-Blocked by A-Wiki hook (Iron Law violation)}"
  # Also log to live-events.jsonl for dashboard
  "$PYTHON_BIN" "$REPO_ROOT/scripts/live-dashboard/event_logger.py" hook_block \
    event="$EVENT" \
    reason="$BLOCK_REASON" \
    "tool=$TOOL_NAME" \
    2>/dev/null || true
  if ! ENCODED_REASON="$(printf '%s' "$BLOCK_REASON" | "$PYTHON_BIN" -c 'import json, sys; sys.stdout.write(json.dumps(sys.stdin.read()))' 2>/dev/null)"; then
    ENCODED_REASON='"Blocked by A-Wiki hook"'
  fi
  [ -n "$ENCODED_REASON" ] || ENCODED_REASON='"Blocked by A-Wiki hook"'
  printf '{"cancel":true,"contextModification":"","errorMessage":%s}\n' "$ENCODED_REASON"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] event=$EVENT result=BLOCK reason=$BLOCK_REASON" >> "$LOG_FILE"
  exit 0
fi

# PASS — return cancel:false
if [ -n "$STDERR_OUT" ]; then
  # Warning but not blocking
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] event=$EVENT result=PASS_WARNING stderr=$STDERR_OUT" >> "$LOG_FILE"
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] event=$EVENT result=PASS" >> "$LOG_FILE"

# Emit pass event to live dashboard
"$PYTHON_BIN" "$REPO_ROOT/scripts/live-dashboard/event_logger.py" hook_check \
  "hook=cline-adapter" \
  "event=$EVENT" \
  "result=pass" \
  "tool=$TOOL_NAME" \
  2>/dev/null || true

echo '{"cancel":false,"contextModification":"","errorMessage":""}'
exit 0