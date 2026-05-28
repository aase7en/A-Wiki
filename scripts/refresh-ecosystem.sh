#!/usr/bin/env bash
# refresh-ecosystem.sh — Pull latest skills from affaan-m/ECC upstream
#
# Strategy: remote-only + targeted snapshot — does NOT touch skills/ecosystem/
# directly. Snapshots upstream to a sibling dir so the user can diff/cherry-pick
# the changes they want without losing A-Wiki-specific customizations.
#
# Docs:     wiki/entities/ai-tools/ecc.md
# Upstream: https://github.com/affaan-m/ECC
# Remote name: ecc (added by this script if missing)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/ecc"
REMOTE="ecc"
URL="https://github.com/affaan-m/ECC.git"
BRANCH="main"

# --- 1. Ensure remote exists ---
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

# --- 2. Fetch ---
echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

# --- 3. Materialize upstream into _upstream/ (does NOT touch skills/ecosystem/) ---
mkdir -p "$SNAPSHOT_DIR"
find "$SNAPSHOT_DIR" -mindepth 1 -delete
echo "→ extracting $REMOTE/$BRANCH into $SNAPSHOT_DIR"
git archive --format=tar "$REMOTE/$BRANCH" | tar -x -C "$SNAPSHOT_DIR"

# --- 4. Diff against current skills/ecosystem/ (high-level) ---
echo ""
echo "📊 Upstream summary:"
find "$SNAPSHOT_DIR" -maxdepth 2 -type d | head -10
echo "  ..."

echo ""
echo "✅ Snapshot ready: $SNAPSHOT_DIR"
echo "   Current A-Wiki: skills/ecosystem/  ($(find skills/ecosystem -maxdepth 1 -type d 2>/dev/null | wc -l) dirs)"
echo ""
echo "To compare a specific skill:"
echo "  diff -ruN skills/ecosystem/code-review/ $SNAPSHOT_DIR/skills/code-review/"
echo ""
echo "To cherry-pick a new upstream skill into A-Wiki:"
echo "  cp -r $SNAPSHOT_DIR/skills/<new-skill> skills/ecosystem/<new-skill>"
