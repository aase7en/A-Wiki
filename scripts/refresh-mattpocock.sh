#!/usr/bin/env bash
# refresh-mattpocock.sh — Pull latest skills from mattpocock/skills upstream
#
# Strategy: remote-only + targeted snapshot — does NOT touch skills/mattpocock/
# directly. Snapshots upstream to a sibling dir so the user can diff/cherry-pick
# the changes they want without losing A-Wiki-specific customizations.
#
# Docs:     wiki/entities/ai-tools/mattpocock-skills.md
# Upstream: https://github.com/mattpocock/skills
# Remote name: mattpocock (added by this script if missing)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/mattpocock"
REMOTE="mattpocock"
URL="https://github.com/mattpocock/skills.git"
BRANCH="main"

# --- 1. Ensure remote exists ---
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

# --- 2. Fetch ---
echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

# --- 3. Materialize upstream into _upstream/ (does NOT touch skills/mattpocock/) ---
mkdir -p "$SNAPSHOT_DIR"
find "$SNAPSHOT_DIR" -mindepth 1 -delete
echo "→ extracting $REMOTE/$BRANCH into $SNAPSHOT_DIR"
git archive --format=tar "$REMOTE/$BRANCH" | tar -x -C "$SNAPSHOT_DIR"

# --- 4. Diff against current skills/mattpocock/ (high-level) ---
echo ""
echo "📊 Upstream summary:"
find "$SNAPSHOT_DIR" -maxdepth 2 -type d | head -20

echo ""
echo "✅ Snapshot ready: $SNAPSHOT_DIR"
echo "   Current A-Wiki: skills/mattpocock/  ($(find skills/mattpocock -maxdepth 1 -type d 2>/dev/null | wc -l) dirs)"
echo ""
echo "To compare a specific skill:"
echo "  diff -ruN skills/mattpocock/<skill>/ $SNAPSHOT_DIR/<skill>/"
echo ""
echo "To cherry-pick a new upstream skill into A-Wiki (register FIRST, then write):"
echo "  1. add entry to skills-registry.json (name, domain, lifecycle_phase, path)"
echo "  2. python scripts/regen-skill-surfaces.py"
echo "  3. cp -r $SNAPSHOT_DIR/<new-skill> skills/mattpocock/<new-skill>"
