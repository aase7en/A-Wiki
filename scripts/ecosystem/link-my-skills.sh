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

# 3. ECC ecosystem skills (SELECTIVE — only relevant ones)
ECC_INCLUDE=(
  "agentic-engineering" "api-design" "architecture-decision-records"
  "automated-testing" "bash-scripting" "code-review"
  "commit-message" "continuous-integration" "git-workflow"
  "markdown" "project-planning" "python-development"
  "research-paper" "technical-writing" "terminal-commands"
  "web-development"
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