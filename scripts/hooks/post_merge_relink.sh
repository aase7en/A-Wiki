#!/usr/bin/env bash
# =============================================================================
# post_merge_relink.sh — git post-merge hook (tracked source of truth)
# =============================================================================
# Installed by scripts/install-git-hooks.sh into .git/hooks/post-merge.
# Runs after every `git pull` / `git merge` to keep agent skill symlinks in
# sync with the freshly-updated repo content.
#
# Behavior:
#   - On Pi5 (Umbrel Docker): SKIP entirely — Hermes lives in a container and
#     host symlinks are useless. The cron job (auto-sync-from-git.sh) handles
#     Pi5 via docker cp + profile import. Print a one-line reminder only.
#   - On Windows/Mac/Linux: run link-agent-configs.sh --skills-only. Output is
#     suppressed unless something changes or fails, to keep `git pull` quiet.
#   - ALWAYS exit 0: this hook must never block a merge/pull, even if the
#     linker fails (the user can re-run manually with `git awiki-sync`).
# =============================================================================
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || exit 0)"
[ -z "$REPO_ROOT" ] && exit 0

LINKER="$REPO_ROOT/scripts/link-agent-configs.sh"
[ ! -f "$LINKER" ] && exit 0

# ---- Pi5 guard ----
detect_pi5() {
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}
if detect_pi5; then
  # Pi5 uses Docker — host symlinks are irrelevant. The cron job handles it.
  echo "[post-merge] Pi5 detected — skipping native relink (cron handles Docker sync)"
  exit 0
fi

# ---- Re-link skills quietly ----
# Capture output; only print if the linker reports a change or a warning.
# This keeps `git pull` quiet when there's nothing to do.
OUTPUT="$("$LINKER" --skills-only 2>&1)" || true
if echo "$OUTPUT" | grep -qiE "linked|FAIL|WARN|⚠|❌|Skipping|backed up"; then
  echo "[post-merge] re-linked agent skills:"
  echo "$OUTPUT" | sed 's/^/  /'
fi

exit 0
