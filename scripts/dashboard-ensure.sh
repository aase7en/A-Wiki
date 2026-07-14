#!/usr/bin/env bash
# scripts/dashboard-ensure.sh — idempotent: start Live Dashboard if not already running
# Safe to call from session_start.py or delegate.sh (fire-and-forget).
# Guards:
#   AWIKI_DISABLE_DASHBOARD_AUTOSTART=1 → skip.
#   AWIKI_DISABLE_DASHBOARD_OPEN_BROWSER=1 → start server only, don't open browser.
#
# Optional arg 1: agent name (claude, codex, zcode, gemini, cursor, windsurf,
# cline, antigravity, hermes, kilo, copilot) — opens browser with ?agent=<name>
# so the Skills tab auto-filters to what THAT agent can invoke.

[ "${AWIKI_DISABLE_DASHBOARD_AUTOSTART:-0}" = "1" ] && exit 0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.tmp/live-dashboard.pid"
LOCK_DIR="$REPO_ROOT/.tmp/.dashboard.lock"
PORT="${AWIKI_DASHBOARD_PORT:-7790}"
AGENT="${1:-${AWIKI_DASHBOARD_AGENT:-}}"

# --- helpers ---------------------------------------------------------------

# Cross-platform "is this PID alive?". Git Bash's `kill -0` cannot see native
# Win32 PIDs (documented in scripts/lib/pid_check.py), so on MINGW/MSYS we ask
# tasklist instead. Without this, the PID-file guard always fails on Windows
# and every caller races into spawning a second daemon.
_pid_alive() {
  local pid="$1"
  [ -z "$pid" ] && return 1
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      tasklist //FI "PID eq $pid" 2>/dev/null | grep -q "$pid"
      ;;
    *)
      kill -0 "$pid" 2>/dev/null
      ;;
  esac
}

# Port-probe: returns 0 (true) if something is already bound on $PORT.
_port_in_use() {
  "$PYTHON" -c "import socket,sys; s=socket.socket(); s.settimeout(0.3); sys.exit(0 if s.connect_ex(('127.0.0.1',$PORT))==0 else 1)" 2>/dev/null
}

# --- resolve a working Python ---------------------------------------------
# On Windows Git Bash, `python3` is often a Microsoft Store alias stub that
# prints an install message and exits without executing — verify the
# interpreter can import before using it.
PYTHON="${AWIKI_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then
      PYTHON="$cand"; break
    fi
  done
fi
[ -z "$PYTHON" ] && exit 0  # no usable Python — skip silently (non-fatal)

# --- Guard 1 — PID file ----------------------------------------------------
if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$pid" ] && _pid_alive "$pid"; then
    exit 0  # Already running
  fi
  rm -f "$PID_FILE"
fi

# --- Guard 2 — port probe (robust even when PID file is stale) -------------
if _port_in_use; then
  exit 0
fi

# --- Guard 3 — file lock to prevent the race between concurrent callers ----
# VS Code folderOpen + Claude/ZCode SessionStart + delegate.sh can all fire
# within the same ~500ms; the port probe above is still "free" for all of
# them, so without a lock each caller spawns its own daemon → 2-4 browser
# tabs. mkdir is atomic on every platform (no flock needed).
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  # Another caller holds the lock. Wait briefly for it to either bind the
  # port (dashboard started) or release the lock (it failed/crashed).
  for _ in 1 2 3 4 5; do
    _port_in_use && exit 0
    sleep 0.5
  done
  # Lock still held and port still free after ~2.5s — the other caller may
  # have died mid-spawn. Force a re-check and proceed if we can re-acquire.
  rmdir "$LOCK_DIR" 2>/dev/null
  mkdir "$LOCK_DIR" 2>/dev/null || exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

# Re-check the port after acquiring the lock — the previous lock-holder may
# have just finished starting the daemon.
if _port_in_use; then
  exit 0
fi

# --- Start the daemon ------------------------------------------------------
# server.py --daemonize detaches itself (POSIX double-fork / Windows detached
# subprocess) and returns fast, so we must NOT background it with `&` — doing
# so lets the launching shell SIGHUP the parent before it finishes spawning
# the detached daemon (race seen on Windows/Git Bash).
#
# --no-browser is passed unconditionally: server.py would otherwise call
# webbrowser.open() itself (server.py:1203), and THIS script also opens the
# browser below — that double-open is the second source of duplicate tabs.
# Letting only this script decide (honoring AWIKI_DISABLE_DASHBOARD_OPEN_BROWSER)
# keeps a single point of control.
"$PYTHON" "$REPO_ROOT/scripts/live-dashboard/server.py" --daemonize --no-browser >/dev/null 2>&1

# Give the daemon a moment to bind the port before we try to open the browser.
sleep 1

# Open the dashboard in the user's default browser with ?agent=<name> if given.
# Disabled via AWIKI_DISABLE_DASHBOARD_OPEN_BROWSER=1. Fire-and-forget — never
# blocks the calling shell.
if [ "${AWIKI_DISABLE_DASHBOARD_OPEN_BROWSER:-0}" != "1" ]; then
  URL="http://localhost:${PORT}/"
  [ -n "$AGENT" ] && URL="${URL}?agent=${AGENT}"
  (
    case "$(uname -s)" in
      MINGW*|MSYS*|CYGWIN*) start "" "$URL" >/dev/null 2>&1 ;;
      Darwin)               open "$URL" >/dev/null 2>&1 ;;
      *)                    xdg-open "$URL" >/dev/null 2>&1 ;;
    esac
  ) &
fi
