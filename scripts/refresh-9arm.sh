#!/usr/bin/env bash
# refresh-9arm.sh — Pull latest skills from thananon/9arm-skills upstream
#
# Strategy: remote-only (not git-subtree) — fetch then targeted checkout into
# agent-skills/_upstream/9arm-skills/. Safer than `git subtree add` because it
# does NOT require a clean working tree and creates only one commit (or none
# if nothing changed).
#
# Docs:     wiki/entities/ai-tools/9arm-skills.md
# Upstream: https://github.com/thananon/9arm-skills
# Remote name: 9arm (added by this script if missing)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

UPSTREAM_DIR="agent-skills/_upstream/9arm-skills"
REMOTE="9arm"
URL="https://github.com/thananon/9arm-skills.git"
BRANCH="main"

# --- 1. Ensure remote exists ---
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

# --- 2. Fetch ---
echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

# --- 3. Materialize upstream into _upstream/ via git archive (no merge commit) ---
mkdir -p "$UPSTREAM_DIR"
# Remove old contents (but keep the dir itself) so deleted upstream files vanish locally
find "$UPSTREAM_DIR" -mindepth 1 -delete
echo "→ extracting $REMOTE/$BRANCH into $UPSTREAM_DIR"
git archive --format=tar "$REMOTE/$BRANCH" | tar -x -C "$UPSTREAM_DIR"

# --- 4. Show summary ---
echo ""
echo "✅ Refreshed: $UPSTREAM_DIR"
ls "$UPSTREAM_DIR" | head -10
echo ""
echo "Symlinks in agent-skills/engineering/ and productivity/ point here."
echo "Verify: ls -la agent-skills/engineering/debug-mantra"
echo ""
echo "Commit when ready:"
echo "  git add $UPSTREAM_DIR"
echo "  git commit -m \"refresh: 9arm-skills from upstream\""
