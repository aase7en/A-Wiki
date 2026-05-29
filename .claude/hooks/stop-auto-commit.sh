#!/usr/bin/env bash
# Stop hook: commit ALL changes on main, then push origin/main.
# Main-only policy: never merge a feature branch automatically.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 0

git rev-parse --git-dir >/dev/null 2>&1 || exit 0

DATE=$(date +%Y-%m-%d)
BRANCH=$(git branch --show-current 2>/dev/null)

if [ -n "$BRANCH" ] && [ "$BRANCH" != "main" ]; then
  echo "[stop] ERROR: current branch is '$BRANCH'; refusing auto-commit/push because A-Wiki is main-only" >&2
  echo "[stop] Switch to main and reconcile manually before ending the session." >&2
  exit 0
fi

# Exclude known-sensitive patterns (.env files, lock.txt).
DIRTY=$(git status --porcelain 2>/dev/null | grep -vE "\.env$|lock\.txt$" | wc -l | tr -d ' ')

if [ "$DIRTY" -gt 0 ]; then
  git add -A -- ':!*.env' ':!.claude/lock.txt' 2>/dev/null
  git commit -m "auto: session end $DATE" 2>/dev/null \
    && echo "[stop] committed $DIRTY file(s)" >&2 \
    || echo "[stop] commit failed (secret-leak hook? check staged files)" >&2
else
  echo "[stop] no changes to commit" >&2
fi

git push origin main 2>/dev/null \
  && echo "[stop] pushed to origin/main" >&2 \
  || echo "[stop] push failed; check network or try: git push origin main" >&2
