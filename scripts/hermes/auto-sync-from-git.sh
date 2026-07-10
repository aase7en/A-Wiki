#!/bin/bash
# =============================================================================
# Hermes Auto-Sync — Pi5 pulls latest brain from GitHub (cron, every 6h)
# =============================================================================
# Cron: 0 */6 * * * cd ~/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh
#
# Flow (rewritten 2026-07-10 — the old tarball flow could never run):
#   1. host clone pull        — keeps THIS script + helpers fresh
#   2. secrets sync           — Drive → local (fail-soft)
#   3. container brain FF     — pi5-brain-sync.py --apply:
#        git fetch + ff-only merge of /opt/data/A-Wiki INSIDE the container,
#        stash/pop with auto-gen conflict resolution, then gateway SIGHUP.
#
# Why the old flow was dead: it imported scripts/hermes/hermes-export-*.tar.gz
# from the repo, but .gitignore excludes *.tar.gz — git pull never delivers a
# package, so the import (and the cwd-clobbering `config set terminal.cwd`
# after it) never ran, and the container brain only updated by hand.
# hermes-export tarballs remain for FIRST-TIME provisioning: see IMPORT-NOTES.md.
#
# One-time Pi5 setup for cron (sudo is passwordful; docker needs root):
#   echo 'umbrel ALL=(root) NOPASSWD: /usr/bin/docker exec *' \
#     | sudo tee /etc/sudoers.d/awiki-hermes-sync
# Without it, step 3 fails fast with a clear sudo error (never hangs).
# =============================================================================
set -e

REPO_DIR="${A_WIKI_DIR:-$HOME/A-Wiki}"
LOCK_FILE="/tmp/hermes-auto-sync.lock"

[ -f "$LOCK_FILE" ] && { echo "Another sync running. Skip."; exit 0; }
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

echo "=== $(date): Hermes Auto-Sync ==="

# ---- Step 1: host clone pull (no sudo needed) ----
cd "$REPO_DIR"
git pull --ff-only 2>&1

# ---- Step 2: secrets from Google Drive (fail-soft) ----
if [ -f "scripts/hermes/sync-secrets-from-drive.sh" ]; then
  bash scripts/hermes/sync-secrets-from-drive.sh 2>&1 \
    || echo "Drive secrets sync skipped (OK if Drive offline)"
fi

# ---- Step 3: container brain FF + gateway rescan ----
# Always run — the container clone has its own UP-TO-DATE guard, and skipping
# on "no new host commits" would strand a container that fell behind earlier.
PY_BIN="$(command -v python3 || command -v python)"
if [ -z "$PY_BIN" ]; then
  echo "ERROR: no python3 on host — cannot run pi5-brain-sync.py"
  exit 1
fi
"$PY_BIN" "$REPO_DIR/scripts/hermes/pi5-brain-sync.py" --apply
RC=$?

echo "=== Done (exit $RC) ==="
exit $RC
