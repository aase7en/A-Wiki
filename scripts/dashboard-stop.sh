#!/usr/bin/env bash
# scripts/dashboard-stop.sh — stop Live Dashboard daemon gracefully

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.tmp/live-dashboard.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Dashboard not running (no PID file at .tmp/live-dashboard.pid)"
  exit 0
fi

pid=$(cat "$PID_FILE" 2>/dev/null)
if [ -z "$pid" ]; then
  rm -f "$PID_FILE"
  echo "PID file was empty — cleaned up"
  exit 0
fi

if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  echo "Dashboard stopped (PID $pid)"
  rm -f "$PID_FILE"
else
  echo "PID $pid not found — cleaning up stale PID file"
  rm -f "$PID_FILE"
fi
