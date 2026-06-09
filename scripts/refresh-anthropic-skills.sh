#!/usr/bin/env bash
# refresh-anthropic-skills.sh — Pull latest skills from anthropics/skills upstream
#
# Strategy: remote fetch + git archive extraction directly into skills/anthropic-skills/.
# Unlike refresh-ecosystem.sh (which snapshots into _upstream/ for manual review),
# anthropics/skills are Anthropic-curated and safe to apply directly.
#
# Docs:     wiki/entities/ai-tools/anthropic-skills.md
# Upstream: https://github.com/anthropics/skills
# Remote name: anthropic-skills (added by this script if missing)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DEST_DIR="skills/anthropic-skills"
REMOTE="anthropic-skills"
URL="https://github.com/anthropics/skills.git"
BRANCH="main"

# --- 1. Ensure remote exists ---
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

# --- 2. Fetch ---
echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

# --- 3. Extract skills/ into skills/anthropic-skills/ (strip the skills/ prefix) ---
mkdir -p "$DEST_DIR"
# Clear existing to avoid stale skills after upstream renames/removes
find "$DEST_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true

echo "→ extracting $REMOTE/$BRANCH:skills/ into $DEST_DIR"
git archive --format=tar "$REMOTE/$BRANCH" skills/ | tar -x -C "$DEST_DIR" --strip-components=1

# --- 4. Summary ---
SKILL_COUNT=$(find "$DEST_DIR" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
echo ""
echo "✅ Updated: $DEST_DIR ($SKILL_COUNT skills)"
echo ""
echo "Skills available:"
for d in "$DEST_DIR"/*/; do
  echo "  • $(basename "$d")"
done
echo ""
echo "Run 'bash scripts/link-skills.sh' to link updated skills to ~/.claude/skills/"
echo "Run 'bash scripts/link-my-skills.sh' to distribute to all agent environments"
