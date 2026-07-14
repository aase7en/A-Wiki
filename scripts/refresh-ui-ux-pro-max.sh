#!/usr/bin/env bash
# refresh-ui-ux-pro-max.sh — snapshot latest nextlevelbuilder/ui-ux-pro-max-skill upstream
#
# Docs:     wiki/entities/ai-tools/ui-ux-pro-max.md
# Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
# Remote name: ui-ux-pro-max (added by this script if missing)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/ui-ux-pro-max"
REMOTE="ui-ux-pro-max"
URL="https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git"
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
echo "   Current A-Wiki vendored copy: skills/ui-ux-pro-max/ (from upstream .claude/skills/ui-ux-pro-max/)"
echo ""
echo "To compare:"
echo "  diff -ruN skills/ui-ux-pro-max/ $SNAPSHOT_DIR/.claude/skills/ui-ux-pro-max/"
