#!/usr/bin/env bash
# install-git-hooks.sh — install tracked git hooks + aliases into .git/ (not tracked).
#
# Currently installs:
#   - pre-commit: runs scripts/hooks/pre-commit-awiki.sh (USA-1 §5 Layer 2) which
#     combines skill-registry drift check + secret scan + machine-path scan on
#     the staged diff.
#   - post-merge: runs scripts/hooks/post_merge_relink.sh to re-link agent skills
#     after every `git pull` / `git merge` (skips Pi5 Docker — cron handles it).
#
# Also registers the git alias:
#   - `git awiki-sync` → scripts/awiki-sync.sh (pull + link + status, platform-aware)
#
# Idempotent: safe to re-run. Overwrites existing hooks only if they differ.
# Override: skip entirely with INSTALL_GIT_HOOKS=0
set -euo pipefail

if [ "${INSTALL_GIT_HOOKS:-1}" = "0" ]; then
  echo "[install-git-hooks] skipped (INSTALL_GIT_HOOKS=0)"
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
HOOKS_DIR=".git/hooks"
mkdir -p "$HOOKS_DIR"

# --- pre-commit (USA-1 §5 Layer 2: registry drift + secret + machine-path) ---
TARGET="$HOOKS_DIR/pre-commit"
SOURCE="scripts/hooks/pre-commit-awiki.sh"

if [ ! -f "$SOURCE" ]; then
  echo "[install-git-hooks] source $SOURCE missing — skipping pre-commit"
else
  # Write a small wrapper that delegates to the tracked gate (keeps the
  # tracked script as the source of truth, editable across machines).
  cat > "$TARGET" <<'EOF'
#!/usr/bin/env bash
# Auto-installed by scripts/install-git-hooks.sh — delegates to tracked gate.
# To customize, edit scripts/hooks/pre-commit-awiki.sh (NOT this file).
exec bash "$(git rev-parse --show-toplevel)/scripts/hooks/pre-commit-awiki.sh"
EOF
  chmod +x "$TARGET"
  echo "[install-git-hooks] installed pre-commit → delegates to $SOURCE"
fi

# --- post-merge (re-link agent skills after pull/merge) ---
TARGET="$HOOKS_DIR/post-merge"
SOURCE="scripts/hooks/post_merge_relink.sh"

if [ ! -f "$SOURCE" ]; then
  echo "[install-git-hooks] source $SOURCE missing — skipping post-merge"
else
  cat > "$TARGET" <<'EOF'
#!/usr/bin/env bash
# Auto-installed by scripts/install-git-hooks.sh — delegates to tracked script.
# To customize, edit scripts/hooks/post_merge_relink.sh (NOT this file).
exec bash "$(git rev-parse --show-toplevel)/scripts/hooks/post_merge_relink.sh"
EOF
  chmod +x "$TARGET"
  echo "[install-git-hooks] installed post-merge → delegates to $SOURCE"
fi

# --- git alias: git awiki-sync (pull + re-link skills, platform-aware) ---
AWIKI_SYNC_SCRIPT="$REPO_ROOT/scripts/awiki-sync.sh"
if [ -f "$AWIKI_SYNC_SCRIPT" ]; then
  # `!` prefix = shell command alias (not a git subcommand). Quotes the path
  # so spaces/special chars in the repo path don't break it.
  git config alias.awiki-sync "!bash \"$AWIKI_SYNC_SCRIPT\""
  echo "[install-git-hooks] registered git alias: git awiki-sync"
else
  echo "[install-git-hooks] scripts/awiki-sync.sh missing — skipping alias"
fi

echo "[install-git-hooks] done. Hooks are not git-tracked; re-run on new machines."
