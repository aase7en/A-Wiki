#!/usr/bin/env bash
# refresh-transitions-dev.sh — snapshot latest Jakubantalik/transitions.dev upstream
#
# Docs:     wiki/entities/ai-tools/transitions-dev.md
# Upstream: https://github.com/Jakubantalik/transitions.dev
# Remote name: transitions-dev (added by this script if missing)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/transitions-dev"
REMOTE="transitions-dev"
URL="https://github.com/Jakubantalik/transitions.dev.git"
BRANCH="main"

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

mkdir -p "$SNAPSHOT_DIR"
find "$SNAPSHOT_DIR" -mindepth 1 -delete
echo "→ extracting $REMOTE/$BRANCH into $SNAPSHOT_DIR"
git archive --format=tar "$REMOTE/$BRANCH" | tar -x -C "$SNAPSHOT_DIR"

echo ""
echo "✅ Snapshot ready: $SNAPSHOT_DIR"
echo "   Current A-Wiki vendored copy: skills/transitions-dev/"
echo ""
echo "To compare:"
echo "  diff -ruN skills/transitions-dev/ $SNAPSHOT_DIR/skills/transitions-dev/"
