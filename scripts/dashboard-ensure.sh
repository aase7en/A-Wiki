#!/usr/bin/env bash
# scripts/dashboard-ensure.sh — idempotent: start Live Dashboard if not already running
# Safe to call from session_start.py or delegate.sh (fire-and-forget).
# Guard: AWIKI_DISABLE_DASHBOARD_AUTOSTART=1 → skip.

[ "${AWIKI_DISABLE_DASHBOARD_AUTOSTART:-0}" = "1" ] && exit 0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.tmp/live-dashboard.pid"
PORT="${AWIKI_DASHBOARD_PORT:-7790}"

# Guard 1 — PID file (works on POSIX; kill -0 can't see native PIDs on Win)
if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    exit 0  # Already running
  fi
  rm -f "$PID_FILE"
fi

# Resolve a Python that actually runs. On Windows Git Bash, `python3` is often
# a Microsoft Store alias stub that prints an install message and exits without
# executing — so verify the interpreter can import before using it.
PYTHON="${AWIKI_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then
      PYTHON="$cand"; break
    fi
  done
fi
[ -z "$PYTHON" ] && exit 0  # no usable Python — skip silently (non-fatal)

# Guard 2 — port probe (robust on Windows where kill -0 misses native PIDs):
# if something already answers on the dashboard port, it's running → no-op.
if "$PYTHON" -c "import socket,sys; s=socket.socket(); s.settimeout(0.3); sys.exit(0 if s.connect_ex(('127.0.0.1',$PORT))==0 else 1)" 2>/dev/null; then
  exit 0
fi

# Start in daemon mode. server.py --daemonize detaches itself (POSIX double-fork
# / Windows detached subprocess) and returns fast, so we must NOT background it
# with `&` — doing so lets the launching shell SIGHUP the parent before it
# finishes spawning the detached daemon (race seen on Windows/Git Bash).
"$PYTHON" "$REPO_ROOT/scripts/live-dashboard/server.py" --daemonize "$@" >/dev/null 2>&1
