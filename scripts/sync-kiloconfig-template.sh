#!/usr/bin/env bash
# scripts/sync-kiloconfig-template.sh — Sync the Drive-synced template to the
# bundled fallback template so new machines get the latest defaults.
#
# Why:  The bundled template (scripts/lib/kilo.jsonc.template) is the fallback
#       for machines without Drive access or before first `setup-cloud-link.sh`.
#       After updating the Drive template at:
#         <Drive>/A-Wiki-Data/.config/kilo/kilo.jsonc.template
#       run this script to keep the bundled fallback in sync.
#
# Safety: The script copies the template as-is. It does NOT expand secrets or
#         path tokens — those are resolved at render time by render_kilo_config.py.
#         If the Drive template contains any expanded secrets (indicating a
#         mistake), the script warns and aborts.
#
# Usage:
#   bash scripts/sync-kiloconfig-template.sh          # sync (idempotent)
#   bash scripts/sync-kiloconfig-template.sh --check  # report only, no write
#
# Guard: AWIKI_DISABLE_KILO_CONFIG_SYNC=1 → skip (for CI / headless setups).

set -eu

[ "${AWIKI_DISABLE_KILO_CONFIG_SYNC:-0}" = "1" ] && { echo "skipped (AWIKI_DISABLE_KILO_CONFIG_SYNC=1)"; exit 0; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRIVE_TPL="$REPO_ROOT/drive/.config/kilo/kilo.jsonc.template"
BUNDLED_TPL="$REPO_ROOT/scripts/lib/kilo.jsonc.template"

if [ ! -f "$DRIVE_TPL" ]; then
  if [ "${1:-}" = "--check" ]; then
    echo "WARN: Drive template not found at $DRIVE_TPL — run setup-cloud-link.sh first"
    exit 0
  fi
  echo "ERROR: Drive template not found at $DRIVE_TPL" >&2
  echo "Run 'bash scripts/setup-cloud-link.sh --auto' first, or check that" >&2
  echo "drive/.config/kilo/kilo.jsonc.template exists." >&2
  exit 1
fi

# Sanity check: ensure the Drive template doesn't contain expanded secrets
if grep -qE '(sk-or-v1-|AIzaSy[A-Za-z0-9_\-]{20,})' "$DRIVE_TPL" 2>/dev/null; then
  echo "ERROR: Drive template appears to contain expanded secrets! Aborting." >&2
  echo "  Check $DRIVE_TPL for leaked API keys and fix before syncing." >&2
  exit 2
fi

if [ "${1:-}" = "--check" ]; then
  echo "Drive  template : $DRIVE_TPL"
  echo "Bundled fallback : $BUNDLED_TPL"
  if diff -q "$DRIVE_TPL" "$BUNDLED_TPL" >/dev/null 2>&1; then
    echo "Status: in sync"
  else
    echo "Status: out of sync — run without --check to update"
  fi
  exit 0
fi

cp "$DRIVE_TPL" "$BUNDLED_TPL"
echo "OK — synced $DRIVE_TPL → $BUNDLED_TPL"

# Also make sure the bundled template is valid JSON
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import json; json.loads(open('$BUNDLED_TPL', encoding='utf-8').read())" && \
    echo "OK — bundled template is valid JSON"
elif command -v python >/dev/null 2>&1; then
  python -c "import json; json.loads(open('$BUNDLED_TPL', encoding='utf-8').read())" && \
    echo "OK — bundled template is valid JSON"
fi
