#!/usr/bin/env bash
# scripts/dashboard-ensure.sh — idempotent: start Live Dashboard if not already running
# Safe to call from session_start.py or delegate.sh (fire-and-forget).
# Guard: AWIKI_DISABLE_DASHBOARD_AUTOSTART=1 → skip.

[ "${AWIKI_DISABLE_DASHBOARD_AUTOSTART:-0}" = "1" ] && exit 0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.tmp/live-dashboard.pid"

# Check if already running via PID file
if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    exit 0  # Already running
  fi
  rm -f "$PID_FILE"
fi

# Start in daemon mode (double-fork, opens browser on first start)
python3 "$REPO_ROOT/scripts/live-dashboard/server.py" --daemonize "$@" &>/dev/null &
