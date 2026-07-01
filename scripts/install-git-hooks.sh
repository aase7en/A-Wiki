#!/usr/bin/env bash
# install-git-hooks.sh — install tracked git hooks into .git/hooks/ (which is not tracked).
#
# Currently installs:
#   - pre-commit: runs scripts/hooks/pre_commit_skill_surfaces.sh to catch skill-registry
#     drift before it reaches CI.
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

# --- pre-commit ---
TARGET="$HOOKS_DIR/pre-commit"
SOURCE="scripts/hooks/pre_commit_skill_surfaces.sh"

if [ ! -f "$SOURCE" ]; then
  echo "[install-git-hooks] source $SOURCE missing — skipping pre-commit"
else
  # Write a small wrapper that delegates to the tracked script (keeps the
  # tracked script as the source of truth, editable across machines).
  cat > "$TARGET" <<'EOF'
#!/usr/bin/env bash
# Auto-installed by scripts/install-git-hooks.sh — delegates to tracked script.
# To customize, edit scripts/hooks/pre_commit_skill_surfaces.sh (NOT this file).
exec bash "$(git rev-parse --show-toplevel)/scripts/hooks/pre_commit_skill_surfaces.sh"
EOF
  chmod +x "$TARGET"
  echo "[install-git-hooks] installed pre-commit → delegates to $SOURCE"
fi

echo "[install-git-hooks] done. Hooks are not git-tracked; re-run on new machines."
