#!/usr/bin/env bash
# scripts/setup-kilo-config.sh — render a machine-specific global Kilo config
# from the portable, Drive-synced template.
#
# Keeps ~/.config/kilo/kilo.jsonc consistent across machines (home Mac +
# work Windows/WSL) by auto-detecting each machine's Google Drive path and
# injecting provider keys from Drive .secrets — without changing any AI
# model/agent/permission settings.
#
# Safe to re-run; idempotent. Re-runs after editing the Drive template or
# adding keys to .secrets propagate on the next invocation.
#
# Usage:
#   bash scripts/setup-kilo-config.sh           # render (idempotent)
#   bash scripts/setup-kilo-config.sh --check   # report only, no write
#   bash scripts/setup-kilo-config.sh --force   # overwrite even if unchanged
#
# Guard: AWIKI_DISABLE_KILO_CONFIG_SYNC=1 → skip (for CI / headless setups).

set -eu

[ "${AWIKI_DISABLE_KILO_CONFIG_SYNC:-0}" = "1" ] && { echo "skipped (AWIKI_DISABLE_KILO_CONFIG_SYNC=1)"; exit 0; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RENDER="$REPO_ROOT/scripts/lib/render_kilo_config.py"

if [ ! -f "$RENDER" ]; then
  echo "❌ $RENDER not found" >&2
  exit 1
fi

# Prefer the repo venv python if present, else python3, else python.
if [ -x "$REPO_ROOT/.venv/bin/python3" ]; then
  PY="$REPO_ROOT/.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

exec "$PY" "$RENDER" "$@"
