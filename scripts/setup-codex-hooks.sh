#!/usr/bin/env bash
# scripts/setup-codex-hooks.sh — enable Codex Desktop hooks with full guardrail coverage.
#
# This script cannot DOWNGRADE hooks — if .codex/hooks.json already exists and has
# required guardrails, it is kept. Only missing guardrails are added.
#
# Preferred alternative: python3 scripts/setup-codex-config.py (also writes config.toml)
# This script kept for backwards compatibility and quick hook-only resets.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p .codex

if [ ! -e ".codex/hooks" ] && [ -d ".claude/hooks" ]; then
  ln -s ../.claude/hooks .codex/hooks 2>/dev/null || cp -R .claude/hooks .codex/hooks
fi

# Delegate full-coverage write to setup-codex-config.py if available
if [ -f "scripts/setup-codex-config.py" ]; then
  echo "🔧 Delegating to setup-codex-config.py for full guardrail coverage..."
  python3 scripts/setup-codex-config.py
  exit $?
fi

# P6-RR07: NO embedded fallback hooks.json. The python generator is the
# single source of truth; regenerating a stale copy here could produce a
# false-green parity config. If the generator is missing, FAIL LOUDLY.
if [ ! -f "scripts/setup-codex-config.py" ]; then
  echo "❌ scripts/setup-codex-config.py missing — refusing to write a stale .codex/hooks.json (P6-RR07)" >&2
  echo "   Fix: restore the generator, or run setup-local.sh to re-link scripts." >&2
  exit 1
fi
echo "❌ unexpected state: generator present but delegation did not exit" >&2
exit 1
