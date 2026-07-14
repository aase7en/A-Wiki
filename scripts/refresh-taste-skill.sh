#!/usr/bin/env bash
# refresh-taste-skill.sh — snapshot latest Leonxlnx/taste-skill upstream
#
# Does NOT touch skills/taste-skill/ directly. Snapshots upstream to a sibling
# dir so the user can diff before deciding whether to re-vendor.
#
# Docs:     wiki/entities/ai-tools/taste-skill.md
# Upstream: https://github.com/Leonxlnx/taste-skill
# Remote name: taste-skill (added by this script if missing)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/taste-skill"
REMOTE="taste-skill"
URL="https://github.com/Leonxlnx/taste-skill.git"
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
echo "   Current A-Wiki vendored copy: skills/taste-skill/ (design-taste-frontend only)"
echo ""
echo "To compare:"
echo "  diff -ruN skills/taste-skill/ $SNAPSHOT_DIR/skills/taste-skill/"
