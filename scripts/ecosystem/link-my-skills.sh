#!/bin/bash
# A-Wiki Symlink Connector — เชื่อม skills ecosystem เข้า .claude/skills/
# Usage: bash scripts/ecosystem/link-my-skills.sh [--dry-run]

DRY_RUN=false
[ "$1" = "--dry-run" ] && DRY_RUN=true

SKILLS_DIR=".claude/skills"
mkdir -p "$SKILLS_DIR"

# 1. Claude Code skills (from InW-Wiki)
for skill in skills/claude-code/*/; do
  [ -d "$skill" ] || continue
  name=$(basename "$skill")
  target="$SKILLS_DIR/$name"
  [ -L "$target" ] && continue
  [ -d "$target" ] && continue
  $DRY_RUN && echo "[DRY] ln -s ../../$skill $target" && continue
  ln -s "../../${skill%/}" "$target" 2>/dev/null && echo "Linked: $name"
done

# 2. Thai skills (from 9arm/claude-thai-skills)
for skill in skills/claude-thai/*/; do
  [ -d "$skill" ] || continue
  name=$(basename "$skill")
  target="$SKILLS_DIR/$name"
  [ -L "$target" ] && continue
  [ -d "$target" ] && continue
  $DRY_RUN && echo "[DRY] ln -s ../../$skill $target" && continue
  ln -s "../../${skill%/}" "$target" 2>/dev/null && echo "Linked: $name"
done

# 3. ECC ecosystem skills (SELECTIVE — only relevant, existing ones)
# Every name here MUST exist under skills/ecosystem/ (verified by
# tests/test_kilo_skill_discovery.py). Add/remove as the ecosystem evolves.
ECC_INCLUDE=(
  "agentic-engineering" "api-design" "architecture-decision-records"
  "git-workflow" "project-flow-ops" "python-patterns"
  "python-testing" "tdd-workflow" "research-ops"
  "article-writing" "terminal-ops" "frontend-patterns"
  "security-review" "plankton-code-quality"
)
for name in "${ECC_INCLUDE[@]}"; do
  src="skills/ecosystem/$name"
  target="$SKILLS_DIR/$name"
  [ -d "$src" ] || continue
  [ -L "$target" ] && continue
  $DRY_RUN && echo "[DRY] ln -s ../../$src $target" && continue
  ln -s "../../$src" "$target" 2>/dev/null && echo "Linked ECC: $name"
done

echo "=== Symlink connector done ==="
[ "$DRY_RUN" = true ] && echo "(dry-run — no changes made)"