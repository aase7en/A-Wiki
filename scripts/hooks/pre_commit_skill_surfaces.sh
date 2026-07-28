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

# python3 first: macOS ships no bare `python`, so invoking it made this gate
# exit non-zero and report phantom drift on every SKILL.md commit.
# Same resolver shape as scripts/new-skill.sh.
if [ -x "$REPO_ROOT/.venv/bin/python3" ]; then
    PY="$REPO_ROOT/.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "🚫 [pre_commit_skill_surfaces] no python3 on PATH — cannot verify skill surfaces." >&2
    echo "   Override (only if you know the surfaces are clean): PRE_COMMIT_SKIP_SKILL_REGISTRY=1" >&2
    exit 1
fi

# Only run if the staged changes touch skills, the registry, OR the generator/
# taxonomy/consolidation code that determines surface output (CLICK-PATH-004 fix:
# previously the filter was too narrow and missed generator/taxonomy edits that
# would alter surface output, causing local-pass / CI-fail divergence).
STAGED=$(git diff --cached --name-only)
if ! echo "$STAGED" | grep -qE '(^|/)SKILL\.md$|^skills-registry\.json$|^scripts/skills_registry/|^scripts/regen-skill-surfaces\.py$|^scripts/verify-skill-surfaces\.py$'; then
    exit 0
fi

# Check for drift (exit 1 if surfaces are stale).
if ! "$PY" scripts/regen-skill-surfaces.py --check >/dev/null 2>&1; then
    echo "🚫 [pre_commit_skill_surfaces] Generated surfaces have drifted from registry." >&2
    echo "   Fix: python3 scripts/regen-skill-surfaces.py" >&2
    echo "   Then re-stage and commit." >&2
    echo "   Override: PRE_COMMIT_SKIP_SKILL_REGISTRY=1" >&2
    exit 1
fi

exit 0
