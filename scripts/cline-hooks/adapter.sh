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
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_RUNNER="$REPO_ROOT/scripts/hooks_runner.py"
LOG_FILE="$REPO_ROOT/logs/cline-hooks.log"

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

# ── Log the incoming event ──────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] event=$EVENT tool=$(echo "$INPUT" | jq -r '(.preToolUse.toolName // .postToolUse.toolName // "")' 2>/dev/null)" >> "$LOG_FILE"

# ── Convert Cline hook format → hooks_runner.py format ──────────────────────
# Cline sends:  {"preToolUse":  {"toolName":"...", "parameters":{...}}}
#                {"postToolUse": {"toolName":"...", "parameters":{...}, "result":...}}
#                {"taskStart":   {"task":"...", "apiProvider":"..."}}
#                {"taskComplete":{"task":"...", "apiProvider":"...", ...}}
#
# hooks_runner.py expects: {"tool_name":"...", ...}
#
# Strategy: flatten the inner object, rename toolName→tool_name,
#           add event_type field.
HOOK_DATA="{}"
case "$EVENT" in
  PreToolUse)
    HOOK_DATA=$(echo "$INPUT" | jq -c '
      .preToolUse // {}
      | if .toolName then . + {"tool_name": .toolName} | del(.toolName) else . end
      | . + {"event_type": "PreToolUse"}
    ' 2>/dev/null) || HOOK_DATA="{}"
    ;;
  PostToolUse)
    HOOK_DATA=$(echo "$INPUT" | jq -c '
      .postToolUse // {}
      | if .toolName then . + {"tool_name": .toolName} | del(.toolName) else . end
      | . + {"event_type": "PostToolUse"}
    ' 2>/dev/null) || HOOK_DATA="{}"
    ;;
  TaskStart)
    HOOK_DATA=$(echo "$INPUT" | jq -c '
      .taskStart // {}
      | . + {"event_type": "TaskStart"}
    ' 2>/dev/null) || HOOK_DATA="{}"
    ;;
  TaskComplete)
    HOOK_DATA=$(echo "$INPUT" | jq -c '
      .taskComplete // {}
      | . + {"event_type": "TaskComplete"}
    ' 2>/dev/null) || HOOK_DATA="{}"
    ;;
  *)
    HOOK_DATA=$(echo "$INPUT" | jq -c '. + {"event_type": $event}' --arg event "$EVENT" 2>/dev/null) || HOOK_DATA="{}"
    ;;
esac

# ── Forward to hooks_runner.py ──────────────────────────────────────────────
# hooks_runner.py exit codes:
#   0 → pass (no block)
#   2 → BLOCK (Iron Law violation)
#   other non-zero → pass with warning
STDERR_FILE="$(mktemp)"
EXIT_CODE=0
echo "$HOOK_DATA" | python3 "$HOOKS_RUNNER" 2>"$STDERR_FILE" || EXIT_CODE=$?

STDERR_OUT="$(cat "$STDERR_FILE" 2>/dev/null || true)"
rm -f "$STDERR_FILE"

# ── Convert result → Cline response format ──────────────────────────────────
if [ "$EXIT_CODE" -eq 2 ]; then
  # BLOCK — return cancel:true
  BLOCK_REASON="${STDERR_OUT:-Blocked by A-Wiki hook (Iron Law violation)}"
  # Also log to live-events.jsonl for dashboard
  python3 "$REPO_ROOT/scripts/live-dashboard/event_logger.py" hook_block \
    event="$EVENT" \
    reason="$BLOCK_REASON" \
    "tool=$(echo "$HOOK_DATA" | jq -r '.tool_name // ""' 2>/dev/null)" \
    2>/dev/null || true
  echo "{\"cancel\":true,\"contextModification\":\"\",\"errorMessage\":$(echo "$BLOCK_REASON" | jq -Rs .)}"
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
python3 "$REPO_ROOT/scripts/live-dashboard/event_logger.py" hook_check \
  "hook=cline-adapter" \
  "event=$EVENT" \
  "result=pass" \
  "tool=$(echo "$HOOK_DATA" | jq -r '.tool_name // ""' 2>/dev/null)" \
  2>/dev/null || true

echo '{"cancel":false,"contextModification":"","errorMessage":""}'
exit 0