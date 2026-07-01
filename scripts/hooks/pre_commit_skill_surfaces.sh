#!/usr/bin/env bash
# Pre-commit hook: regenerate skill surfaces if SKILL.md or registry changed.
#
# Blocks the commit if generated surfaces have drifted from the registry.
# Install: symlink this into .git/hooks/pre-commit (or run via husky/lefthook).
#
# Override (emergency): PRE_COMMIT_SKIP_SKILL_REGISTRY=1
set -euo pipefail

# Skip if explicitly disabled.
if [ "${PRE_COMMIT_SKIP_SKILL_REGISTRY:-0}" = "1" ]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Only run if the staged changes touch SKILL.md or the registry.
STAGED=$(git diff --cached --name-only)
if ! echo "$STAGED" | grep -qE '(^|/)SKILL\.md$|^skills-registry\.json$'; then
    exit 0
fi

# Check for drift (exit 1 if surfaces are stale).
if ! python scripts/regen-skill-surfaces.py --check >/dev/null 2>&1; then
    echo "🚫 [pre_commit_skill_surfaces] Generated surfaces have drifted from registry." >&2
    echo "   Fix: python scripts/regen-skill-surfaces.py" >&2
    echo "   Then re-stage and commit." >&2
    echo "   Override: PRE_COMMIT_SKIP_SKILL_REGISTRY=1" >&2
    exit 1
fi

exit 0
