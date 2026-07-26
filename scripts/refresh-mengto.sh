#!/usr/bin/env bash
# refresh-mengto.sh — Pull latest MengTo/Skills upstream (118 design/game/web skills)
#
# Strategy: remote-only + FILTERED snapshot. Full clone is 127MB / 841 files;
# A-Wiki cherry-picks only 10 skills (~69 files) that fill real gaps
# (GSAP/WebGL/design-first-prompting/perf/codex-workflows). The rest overlap
# ~60% with A-Wiki's existing frontend/design/game skills.
#
# Approach:
#   1. fetch remote (git archive, no clone in repo)
#   2. wipe skills/_upstream/mengto/
#   3. extract ONLY cherry-picked dirs into skills/_upstream/mengto/
#   4. .gitignore the parent (so stray files never get committed)
#
# Docs:     wiki/entities/ai-tools/mengto-skills.md (TBD)
# Upstream: https://github.com/MengTo/Skills (MIT)
# Remote name: mengto
#
# Usage:
#   bash scripts/refresh-mengto.sh            # refresh snapshot
#   bash scripts/refresh-mengto.sh --list     # list currently cherry-picked
#   bash scripts/refresh-mengto.sh --add <cat>/<skill>   # add a new cherry-pick

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SNAPSHOT_DIR="skills/_upstream/mengto"
REMOTE="mengto"
URL="https://github.com/MengTo/Skills.git"
BRANCH="main"

# ── Cherry-pick manifest ────────────────────────────────────────────────────
# Format: "<category>/<skill-name>"
# Add here when extending; .gitignore auto-allows anything under these paths.
CHERRY_PICKS=(
  "web-design/gsap"
  "web-design/cinematic-gsap-lenis-motion-system"
  "web-design/gsap-scrolltrigger-storytelling"
  "web-design/webgl-3d-object"
  "web-design/add-shader-cursor-trail"
  "web-design/shaders-cursor-ripples"
  "web-design/threejs"
  "ui/design-first-ui-prompting"
  "codex/audit-reference-originality"
  "codex/optimize-web-animations"
)

# ── Modes ────────────────────────────────────────────────────────────────────
case "${1:-}" in
  --list)
    echo "Cherry-picked MengTo skills ($SNAPSHOT_DIR):"
    for p in "${CHERRY_PICKS[@]}"; do
      cnt=$(find "$SNAPSHOT_DIR/agent-skills/$p" -type f 2>/dev/null | wc -l)
      printf "  %-50s %3d files\n" "$p" "$cnt"
    done
    exit 0
    ;;
  --add)
    if [ $# -lt 2 ]; then
      echo "Usage: $0 --add <category>/<skill-name>   (e.g. codex/video-to-superprompt)" >&2
      exit 1
    fi
    echo "To add '$2':"
    echo "  1. Edit $0 and append '$2' to CHERRY_PICKS array"
    echo "  2. bash $0   (refresh snapshot)"
    echo "  3. Add entry to skills-registry.json (name, domain, lifecycle_phase, path, source: 'vendor:mengto')"
    echo "  4. python scripts/regen-skill-surfaces.py"
    exit 0
    ;;
esac

# ── 1. Ensure remote ────────────────────────────────────────────────────────
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "→ adding remote $REMOTE → $URL"
  git remote add "$REMOTE" "$URL"
fi

# ── 2. Fetch ─────────────────────────────────────────────────────────────────
echo "→ fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

# ── 3. Wipe snapshot ─────────────────────────────────────────────────────────
mkdir -p "$SNAPSHOT_DIR"
# Remove only tracked contents; keep .gitignore if present
find "$SNAPSHOT_DIR" -mindepth 1 ! -name '.gitignore' -delete 2>/dev/null || true

# ── 4. Extract cherry-picks only ─────────────────────────────────────────────
# Layout note: upstream paths look like `agent-skills/codex/foo/SKILL.md`.
# We want `skills/_upstream/mengto/agent-skills/codex/foo/SKILL.md` (same shape),
# so extract into $SNAPSHOT_DIR with no strip-components.
echo "→ extracting ${#CHERRY_PICKS[@]} cherry-picked skills into $SNAPSHOT_DIR"
for pick in "${CHERRY_PICKS[@]}"; do
  src="agent-skills/$pick"
  if git archive --format=tar "$REMOTE/$BRANCH" "$src" 2>/dev/null | tar -x -C "$SNAPSHOT_DIR" 2>/dev/null; then
    cnt=$(find "$SNAPSHOT_DIR/$src" -type f | wc -l)
    printf "  ✓ %-50s %3d files\n" "$pick" "$cnt"
  else
    echo "  ✗ $pick — not found upstream (typo? renamed?)" >&2
    exit 1
  fi
done

# ── 5. Write .gitignore (parent ignored, cherry-picks allowed) ───────────────
cat > "$SNAPSHOT_DIR/.gitignore" <<'EOF'
# Refreshed by scripts/refresh-mengto.sh — DO NOT hand-edit.
# Parent dir is IGNORED except for cherry-picked skills listed below.
# Pattern: ignore everything in agent-skills/, then un-ignore cherry-picks.

# Block everything by default
agent-skills/

# Allow cherry-picks (must mirror CHERRY_PICKS array in refresh-mengto.sh)
!agent-skills/web-design/
agent-skills/web-design/*
!agent-skills/web-design/gsap/
!agent-skills/web-design/cinematic-gsap-lenis-motion-system/
!agent-skills/web-design/gsap-scrolltrigger-storytelling/
!agent-skills/web-design/webgl-3d-object/
!agent-skills/web-design/add-shader-cursor-trail/
!agent-skills/web-design/shaders-cursor-ripples/
!agent-skills/web-design/threejs/

!agent-skills/ui/
agent-skills/ui/*
!agent-skills/ui/design-first-ui-prompting/

!agent-skills/codex/
agent-skills/codex/*
!agent-skills/codex/audit-reference-originality/
!agent-skills/codex/optimize-web-animations/

# Keep README/LICENSE for provenance
!README.md
!LICENSE
EOF

echo ""
echo "✅ Snapshot refreshed: $SNAPSHOT_DIR"
echo "   Total tracked files: $(git ls-files $SNAPSHOT_DIR | wc -l)  (after first commit)"
echo "   Total on disk: $(find $SNAPSHOT_DIR -type f ! -name '.gitignore' | wc -l)"
echo ""
echo "Next steps (first-time setup):"
echo "  1. Add entries to skills-registry.json for each cherry-pick"
echo "  2. python scripts/regen-skill-surfaces.py"
echo "  3. git add $SNAPSHOT_DIR && git commit -m 'feat(skills): vendor MengTo cherry-picks'"
