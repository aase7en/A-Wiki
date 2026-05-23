#!/usr/bin/env bash
# Stop hook: commit ALL changes → merge feature branch to main → push
# Zero Claude tokens — runs as shell script on every session end
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 0

git rev-parse --git-dir >/dev/null 2>&1 || exit 0

DATE=$(date +%Y-%m-%d)
BRANCH=$(git branch --show-current 2>/dev/null)

# ── 1. Commit everything that's changed ───────────────────────────────────────
# Exclude known-sensitive patterns (.env files, lock.txt)
DIRTY=$(git status --porcelain 2>/dev/null | grep -vE "\.env$|lock\.txt$" | wc -l | tr -d ' ')

if [ "$DIRTY" -gt 0 ]; then
  git add -A -- ':!*.env' ':!.claude/lock.txt' 2>/dev/null
  git commit -m "auto: session end $DATE" 2>/dev/null \
    && echo "[stop] ✅ committed $DIRTY file(s)" >&2 \
    || echo "[stop] ⚠️  commit failed (secret-leak hook? check staged files)" >&2
else
  echo "[stop] ℹ️  no changes to commit" >&2
fi

# ── 2. If on feature branch → merge to main ──────────────────────────────────
if [ -n "$BRANCH" ] && [ "$BRANCH" != "main" ]; then
  echo "[stop] 🔀 merging $BRANCH → main..." >&2
  git checkout main 2>/dev/null \
    && git pull --rebase origin main 2>/dev/null \
    && git merge "$BRANCH" --no-edit 2>/dev/null \
    && echo "[stop] ✅ merged to main" >&2 \
    || { echo "[stop] ⚠️  merge conflict — resolve manually then push" >&2; exit 0; }
fi

# ── 3. Push to origin/main ───────────────────────────────────────────────────
git push origin main 2>/dev/null \
  && echo "[stop] ✅ pushed to origin/main" >&2 \
  || echo "[stop] ⚠️  push failed — check network / try: git push origin main" >&2
