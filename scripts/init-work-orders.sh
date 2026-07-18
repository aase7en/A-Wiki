#!/usr/bin/env bash
# init-work-orders.sh — bootstrap the cross-agent work-order standard into a repo.
# Usage: bash scripts/init-work-orders.sh /path/to/repo
# Idempotent: never overwrites existing files; pointer lines added once.
# Protocol: docs/protocols/cross-agent-work-orders.md (binding for all agents).
set -euo pipefail

AWIKI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$AWIKI_ROOT/templates/work-orders"
TARGET="${1:-}"

if [ -z "$TARGET" ] || [ ! -d "$TARGET" ]; then
  echo "usage: bash scripts/init-work-orders.sh /path/to/repo" >&2
  exit 1
fi

copied=0
if [ ! -f "$TARGET/COLLAB.md" ]; then
  cp "$TEMPLATES/COLLAB.md" "$TARGET/COLLAB.md"; copied=$((copied+1))
  echo "+ COLLAB.md"
fi
mkdir -p "$TARGET/docs/work-orders"
for f in README.md WO-TEMPLATE.md; do
  if [ ! -f "$TARGET/docs/work-orders/$f" ]; then
    cp "$TEMPLATES/$f" "$TARGET/docs/work-orders/$f"; copied=$((copied+1))
    echo "+ docs/work-orders/$f"
  fi
done

POINTER='> 🤝 **Multi-agent repo**: read `COLLAB.md` before working — lanes, claims, work orders, pause/resume (A-Wiki cross-agent-work-orders standard).'
for brainfile in AGENTS.md CLAUDE.md; do
  if [ -f "$TARGET/$brainfile" ] && ! grep -q "COLLAB.md" "$TARGET/$brainfile"; then
    printf '\n%s\n' "$POINTER" >> "$TARGET/$brainfile"
    echo "+ pointer in $brainfile"
  fi
done

if [ "$copied" -eq 0 ]; then
  echo "already bootstrapped — nothing to do"
else
  echo "done: fill lanes/hotspots in COLLAB.md, then commit"
fi
