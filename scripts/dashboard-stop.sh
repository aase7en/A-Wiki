#!/usr/bin/env bash
# scripts/dashboard-stop.sh — stop Live Dashboard daemon gracefully
#
# kill -0 (liveness) and kill (termination) can only see/signal MSYS-space
# PIDs on Git Bash. The dashboard daemon's PID (.tmp/live-dashboard.pid) is
# a genuine native Win32 PID on Windows — empirically confirmed neither
# `kill -0 <native_pid>` NOR `kill <native_pid>` (real signal) can see or
# terminate it; only `taskkill //PID <pid> //F` works. See
# scripts/lib/pid_check.py's docstring for the full write-up. POSIX keeps
# the original kill -0 / kill — those PIDs are real POSIX PIDs there
# (server.py's daemonize() double-forks and writes os.getpid()).

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

is_windows=false
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) is_windows=true ;;
esac

# Resolve a Python that actually runs — identical resolution order to
# scripts/dashboard-ensure.sh so both scripts pick the same interpreter.
PYTHON="${AWIKI_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then
      PYTHON="$cand"; break
    fi
  done
fi

if $is_windows && [ -z "$PYTHON" ]; then
  # No usable Python on Windows means we CANNOT reliably tell whether the
  # native PID is alive. Do NOT guess — guessing "dead" is exactly the bug
  # this script exists to fix (silently orphaning a live daemon).
  echo "WARNING: no usable Python found — cannot verify native Windows PID $pid." >&2
  echo "  Stop it manually: taskkill //PID $pid //F   (or Task Manager)" >&2
  echo "  PID file left in place; rerun this script once Python is available." >&2
  exit 1
fi

alive=false
if [ -n "$PYTHON" ]; then
  "$PYTHON" "$REPO_ROOT/scripts/lib/pid_check.py" "$pid" >/dev/null 2>&1 && alive=true
else
  # POSIX with no Python — kill -0 is safe/correct here.
  kill -0 "$pid" 2>/dev/null && alive=true
fi

if $alive; then
  if $is_windows; then
    taskkill //PID "$pid" //F >/dev/null 2>&1
  else
    kill "$pid"
  fi
  echo "Dashboard stopped (PID $pid)"
  rm -f "$PID_FILE"
else
  echo "PID $pid not found — cleaning up stale PID file"
  rm -f "$PID_FILE"
fi
