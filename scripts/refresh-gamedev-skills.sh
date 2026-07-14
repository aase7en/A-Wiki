#!/usr/bin/env bash
# refresh-gamedev-skills.sh — snapshot latest gamedev-skills/awesome-gamedev-agent-skills upstream
#
# A-Wiki only vendors the 6-skill web-engines subset (see skills/gamedev-skills/NOTICE.md);
# this script snapshots the FULL upstream repo (66 skills) for diffing/future cherry-picks.
#
# Docs:     wiki/entities/ai-tools/gamedev-skills.md
# Upstream: https://github.com/gamedev-skills/awesome-gamedev-agent-skills
# Remote name: gamedev-skills (added by this script if missing)

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/gamedev-skills"
REMOTE="gamedev-skills"
URL="https://github.com/gamedev-skills/awesome-gamedev-agent-skills.git"
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
echo "✅ Snapshot ready: $SNAPSHOT_DIR (full 66-skill upstream catalog)"
echo "   Current A-Wiki vendored subset: skills/gamedev-skills/{phaser-arcade-physics,phaser-core,pixijs-rendering,threejs-gltf-loading,threejs-materials-lighting,threejs-scene-setup}/"
echo ""
echo "To compare a vendored skill:"
echo "  diff -ruN skills/gamedev-skills/<skill>/ $SNAPSHOT_DIR/skills/web-engines/<skill>/"
echo ""
echo "To cherry-pick an additional skill from the other 60 (register FIRST, then write):"
echo "  1. add entry to skills-registry.json (name, domain, lifecycle_phase, category, path)"
echo "  2. python scripts/regen-skill-surfaces.py"
echo "  3. cp -r $SNAPSHOT_DIR/skills/<category>/<skill> skills/gamedev-skills/<skill>"
