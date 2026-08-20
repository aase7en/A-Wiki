#!/usr/bin/env bash
# Stop hook: commit changes on main, then push origin/main — GATED.
# Main-only policy: never merge a feature branch automatically.
#
# Continuity-gate rule 3 (2026-08-20 incident: auto-commit pushed
# generated noise + leftover conflict markers straight to main and main's
# security scan went red; every PR merging main inherited the failure):
#   GATE 1 — pure GENERATED_NOISE changes are never pushed to main
#            (they belong on a work branch that passes CI)
#   GATE 2 — no push unless the repo security scan passes
#            (--ci --baseline, strict pattern source = fail-closed)
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

# Generated surfaces owned by the regenerators — a session-end snapshot of
# ONLY these must not land on main.
GENERATED_NOISE=(
  ".wiki-graph.json"
  "brain-map.canvas"
  "wiki/context/overview-*.md"
  "wiki/context/knowledge-graph.md"
  "wiki/context/graph-hygiene.md"
  "wiki/context/wiki-capability-map.md"
  "wiki/context/wiki-overview.md"
  "wiki/context/review-report.md"
  "wiki/concepts/*/CLAUDE.md"
  "wiki/entities/*/CLAUDE.md"
  "wiki/sources/CLAUDE.md"
)

_is_noise() {
  local f="$1" pat
  for pat in "${GENERATED_NOISE[@]}"; do
    # shellcheck disable=SC2254
    case "$f" in
      $pat) return 0 ;;
    esac
  done
  return 1
}

# Exclude known-sensitive patterns (.env files, lock.txt).
DIRTY=$(git status --porcelain 2>/dev/null | grep -vE "\.env$|lock\.txt$" | wc -l | tr -d ' ')

if [ "$DIRTY" -gt 0 ]; then
  git add -A -- ':!*.env' ':!.claude/lock.txt' 2>/dev/null

  # ── GATE 1: pure generated-noise never pushes to main ────────────────
  NON_NOISE_COUNT=0
  while IFS= read -r staged_file; do
    [ -z "$staged_file" ] && continue
    if ! _is_noise "$staged_file"; then
      NON_NOISE_COUNT=$((NON_NOISE_COUNT + 1))
    fi
  done < <(git diff --cached --name-only 2>/dev/null)

  if [ "$NON_NOISE_COUNT" -eq 0 ]; then
    echo "[stop] staged changes are PURE generated noise — NOT pushing to main." >&2
    echo "[stop] Landing generated updates belongs on a work branch that passes CI." >&2
    git commit -m "auto: session end $DATE (generated-only, not pushed)" >/dev/null 2>&1
    exit 0
  fi

  # ── GATE 2: security scan must pass before any push to main ──────────
  SCAN_OK=0
  if python3 scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt \
        || python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt; then
    SCAN_OK=1
  fi

  if [ "$SCAN_OK" -ne 1 ]; then
    echo "[stop] SECURITY SCAN FAILED (or scanner unavailable — fail-closed): NOT pushing to main." >&2
    echo "[stop] Fix findings or land via a work branch; push manually once green." >&2
    git commit -m "auto: session end $DATE (scan-gated, not pushed)" >/dev/null 2>&1
    exit 0
  fi

  git commit -m "auto: session end $DATE" 2>/dev/null \
    && echo "[stop] committed $DIRTY file(s) (gates passed)" >&2 \
    || echo "[stop] commit failed (secret-leak hook? check staged files)" >&2
else
  echo "[stop] no changes to commit" >&2
fi

git push origin main 2>/dev/null \
  && echo "[stop] pushed to origin/main (gates passed)" >&2 \
  || echo "[stop] push failed; check network or try: git push origin main" >&2
