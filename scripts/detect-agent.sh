#!/usr/bin/env bash
# scripts/detect-agent.sh — print detected agent name (claude/codex/zcode/...)
# or empty string if no fingerprint matches.
#
# Uses scripts/lib/agent_detect.py — the SAME logic as
# scripts/hooks/session_start.py:_detect_agent(). Single source of truth.
#
# Consumers:
#   - .vscode/tasks.json (folderOpen → passes to dashboard-ensure.sh as $1)
#   - any shell caller that wants the agent name
#
# Exit codes: 0 always (empty output is a valid "no agent detected").
#
# Env:
#   AWIKI_PYTHON — override the Python interpreter (default: auto-detect).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Resolve a Python that actually runs. On Windows Git Bash, `python3` is
# often a Microsoft Store alias stub — verify the interpreter can import.
PYTHON="${AWIKI_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then
      PYTHON="$cand"; break
    fi
  done
fi
[ -z "$PYTHON" ] && exit 0  # no usable Python → empty output

# Run the shared detector. Print agent name (may be empty).
# Let Python resolve its own __file__ so we get a native path the interpreter
# understands on every platform (MSYS `pwd` returns /a/... which Windows
# Python can't import from).
"$PYTHON" "$REPO_ROOT/scripts/lib/agent_detect_cli.py" 2>/dev/null
