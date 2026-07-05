#!/usr/bin/env bash
# ============================================================================
# link-my-skills.sh — Symlink agent-skills/ into global agent environments
# ============================================================================
# Links all skills in agent-skills/ into:
#   ~/.claude/skills/   (Claude Code)
#   ~/.codex/skills/    (Codex / OpenAI)
#   ~/.cline/skills/    (Cline / Roo)
#
# Usage:
#   bash scripts/link-my-skills.sh            # Link to all environments
#   bash scripts/link-my-skills.sh --claude   # Link only to Claude
#   bash scripts/link-my-skills.sh --codex    # Link only to Codex
#   bash scripts/link-my-skills.sh --cline    # Link only to Cline
#   bash scripts/link-my-skills.sh --list     # Show what would be linked
# ============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SOURCE="$REPO_ROOT/agent-skills"
ANTHROPIC_SKILL_SOURCE="$REPO_ROOT/skills/anthropic-skills"
MATTPOCOCK_SKILL_SOURCE="$REPO_ROOT/skills/mattpocock"

LINK_TARGETS=()

if [ $# -eq 0 ]; then
    # Default: link to all environments
    LINK_TARGETS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.cline/skills")
else
    case "$1" in
        --claude) LINK_TARGETS=("$HOME/.claude/skills") ;;
        --codex)  LINK_TARGETS=("$HOME/.codex/skills") ;;
        --cline)  LINK_TARGETS=("$HOME/.cline/skills") ;;
        --list)
            echo "Skills that will be linked (from $SKILL_SOURCE):"
            for dir in "$SKILL_SOURCE"/*/*/; do
                skill_name=$(basename "$dir")
                skill_cat=$(basename "$(dirname "$dir")")
                echo "  • $skill_cat/$skill_name"
            done
            if [ -d "$ANTHROPIC_SKILL_SOURCE" ]; then
                echo ""
                echo "Anthropic skills (from $ANTHROPIC_SKILL_SOURCE):"
                for dir in "$ANTHROPIC_SKILL_SOURCE"/*/; do
                    echo "  • anthropic-skills/$(basename "$dir")"
                done
            fi
            if [ -d "$MATTPOCOCK_SKILL_SOURCE" ]; then
                echo ""
                echo "Matt Pocock skills (from $MATTPOCOCK_SKILL_SOURCE):"
                for dir in "$MATTPOCOCK_SKILL_SOURCE"/*/; do
                    echo "  • mattpocock/$(basename "$dir")"
                done
            fi
            echo ""
            agent_count=$(find "$SKILL_SOURCE" -mindepth 2 -maxdepth 2 -type d | wc -l | tr -d ' ')
            anthropic_count=$([ -d "$ANTHROPIC_SKILL_SOURCE" ] && find "$ANTHROPIC_SKILL_SOURCE" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ' || echo 0)
            mattpocock_count=$([ -d "$MATTPOCOCK_SKILL_SOURCE" ] && find "$MATTPOCOCK_SKILL_SOURCE" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ' || echo 0)
            echo "Total: $agent_count agent-skills + $anthropic_count anthropic-skills + $mattpocock_count mattpocock skills"
            exit 0
            ;;
        *)
            echo "Usage: $0 [--claude|--codex|--cline|--list]"
            exit 1
            ;;
    esac
fi

# Check that source directory exists
if [ ! -d "$SKILL_SOURCE" ]; then
    echo "error: Skill source directory not found: $SKILL_SOURCE"
    exit 1
fi

link_skills_to() {
    local dest="$1"
    local agent_name="${dest##*/skills}"
    agent_name="${agent_name%/}"

    echo "🔗 Linking skills to $dest ..."

    mkdir -p "$dest"

    # Find all skill directories (two levels deep in agent-skills/, one level in anthropic-skills/ and mattpocock/)
    {
        find "$SKILL_SOURCE" -mindepth 2 -maxdepth 2 -type d -print0
        [ -d "$ANTHROPIC_SKILL_SOURCE" ] && find "$ANTHROPIC_SKILL_SOURCE" -mindepth 1 -maxdepth 1 -type d -print0
        [ -d "$MATTPOCOCK_SKILL_SOURCE" ] && find "$MATTPOCOCK_SKILL_SOURCE" -mindepth 1 -maxdepth 1 -type d -print0
    } |
    while IFS= read -r -d '' skill_dir; do
        skill_name="$(basename "$skill_dir")"
        target="$dest/$skill_name"

        # Remove existing files/symlinks. Keep real directories to avoid
        # deleting locally installed skills that are not managed by A-Wiki.
        if [ -L "$target" ] || [ -f "$target" ]; then
            rm -f "$target"
        elif [ -d "$target" ]; then
            echo "  ⚠️  Skipping existing directory: $target"
            continue
        elif [ -e "$target" ]; then
            rm -f "$target"
        fi

        # Create symlink
        if ln -s "$skill_dir" "$target" 2>/dev/null; then
            echo "  ✅ $skill_name → $skill_dir"
        else
            echo "  ⚠️  Failed to link $skill_name (symlinks may need admin rights on Windows)"
        fi
    done

    echo "✅ Done linking to $dest"
}

# Link to each target
for target in "${LINK_TARGETS[@]}"; do
    link_skills_to "$target"
done

echo ""
echo "🎯 All skills linked. Skills are now available to your agents."
echo "   Run '$0 --list' to see all linked skills."
