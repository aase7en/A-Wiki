#!/usr/bin/env bash
# ============================================================================
# link-agent-configs.sh — Universal agent-config linker (skills + .env)
# ============================================================================
# One bootstrap per machine: every AI agent harness reads its skills from the
# A-Wiki repo (git = source of truth, already synced across machines) and its
# .env from the Drive data folder (cloud = source of truth for secrets).
#
#   skills:  <agent_dir>/skills/<skill>  ->  <repo>/agent-skills/... (git SSOT)
#   .env:    <agent_dir>/.env            ->  <drive>/.agents/<agent>/.env
#            <repo>/.env                 ->  <drive>/.env  (seeded from .env.example)
#
# Covered agents (auto-detected on this machine):
#   claude codex cline hermes gemini zcode antigravity windsurf openclaw
# Kilo is rendered by scripts/setup-kilo-config.sh — not duplicated here.
#
# Usage:
#   bash scripts/link-agent-configs.sh                # link all detected agents
#   bash scripts/link-agent-configs.sh --agent zcode  # force one agent (creates dir)
#   bash scripts/link-agent-configs.sh --status       # report; exit 1 on broken links
#   bash scripts/link-agent-configs.sh --unlink       # remove managed links only
#   bash scripts/link-agent-configs.sh --list         # show agents + linkable skills
#   Other flags: --all --skills-only --env-only --no-repo-env --dry-run --force
#                --repo-root <path>
#
# Overrides (no hardcoded personal paths — Iron Law #6):
#   A_WIKI_DRIVE_PATH        Drive data root. Fallback order matches
#                            scripts/drive_path.py: repo drive/ link ->
#                            .drive-path file -> ~/.a-wiki-data
#   AWIKI_AGENT_DIR_<AGENT>  per-agent home override (e.g. AWIKI_AGENT_DIR_ZCODE)
#   HERMES_HOME              hermes home (default ~/.hermes)
#
# Notes:
#   - Real (non-symlink) skill dirs and .env files are never deleted; a real
#     .env is migrated to Drive only with --force (backed up beside the target).
#   - Google Drive for Desktop does not sync symlinks: links must point INTO
#     the Drive mount; only real files live on Drive.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

AGENT_NAMES="claude codex cline hermes gemini zcode antigravity windsurf openclaw"
ENV_AGENTS="hermes zcode"

MODE="link"        # link | status | unlink | list
DO_SKILLS=1
DO_ENV=1
SKIP_REPO_ENV=0
DRY_RUN=0
FORCE=0
REQUESTED_AGENTS=""
PROBLEMS=0

usage() {
    sed -n '2,36p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

# ── agent dir resolution ────────────────────────────────────────────────────

agent_default_dir() {
    case "$1" in
        claude)      echo "$HOME/.claude" ;;
        codex)       echo "$HOME/.codex" ;;
        cline)       echo "$HOME/.cline" ;;
        hermes)      echo "${HERMES_HOME:-$HOME/.hermes}" ;;
        gemini)      echo "$HOME/.gemini" ;;
        zcode)       echo "$HOME/.zcode" ;;
        antigravity) echo "$HOME/.antigravity" ;;
        windsurf)    echo "$HOME/.windsurf" ;;
        openclaw)    echo "$HOME/.openclaw" ;;
        *) return 1 ;;
    esac
}

agent_dir() {
    local name="$1" var override
    var="AWIKI_AGENT_DIR_$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')"
    eval "override=\${$var:-}"
    if [ -n "$override" ]; then
        echo "$override"
    else
        agent_default_dir "$name"
    fi
}

is_env_agent() {
    case " $ENV_AGENTS " in
        *" $1 "*) return 0 ;;
        *) return 1 ;;
    esac
}

# ── drive resolution (same order as scripts/drive_path.py) ─────────────────

resolve_drive_root() {
    if [ -n "${A_WIKI_DRIVE_PATH:-}" ]; then
        echo "$A_WIKI_DRIVE_PATH"
        return 0
    fi
    if [ -e "$REPO_ROOT/drive" ]; then
        echo "$REPO_ROOT/drive"
        return 0
    fi
    if [ -f "$REPO_ROOT/.drive-path" ]; then
        local p
        p="$(head -n 1 "$REPO_ROOT/.drive-path" | tr -d '\r')"
        if [ -n "$p" ]; then
            echo "$p"
            return 0
        fi
    fi
    echo "$HOME/.a-wiki-data"
}

# ── link creation (symlink -> PowerShell junction -> mklink /J) ─────────────

create_link() {
    local target="$1" link="$2"
    [ -L "$link" ] && rm -f "$link"

    if ln -s "$target" "$link" 2>/dev/null; then
        return 0
    fi

    # Windows/Git Bash fallback — junctions work for directories only
    if [ -d "$target" ] && command -v powershell.exe >/dev/null 2>&1; then
        local win_link win_target
        win_link="$(cygpath -w "$link" 2>/dev/null || echo "$link")"
        win_target="$(cygpath -w "$target" 2>/dev/null || echo "$target")"
        if powershell.exe -NoProfile -Command \
            "New-Item -ItemType Junction -Path '$win_link' -Target '$win_target' -ErrorAction Stop" \
            >/dev/null 2>&1; then
            return 0
        fi
        if cmd.exe /c "mklink /J \"$win_link\" \"$win_target\"" >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

run_rm() {
    if [ "$DRY_RUN" = "1" ]; then
        echo "  [dry-run] rm $1"
    else
        rm -f "$1"
    fi
}

# ── skill sources (same set as the legacy link-my-skills.sh) ────────────────

list_skill_sources() {
    if [ -d "$REPO_ROOT/agent-skills" ]; then
        find "$REPO_ROOT/agent-skills" -mindepth 2 -maxdepth 2 -type d -print0
    fi
    if [ -d "$REPO_ROOT/skills/anthropic-skills" ]; then
        find "$REPO_ROOT/skills/anthropic-skills" -mindepth 1 -maxdepth 1 -type d -print0
    fi
    if [ -d "$REPO_ROOT/skills/mattpocock" ]; then
        find "$REPO_ROOT/skills/mattpocock" -mindepth 1 -maxdepth 1 -type d -print0
    fi
}

link_skills_into() {
    local dest="$1"
    local skill_dir skill_name target linked=0 failed=0

    if [ "$DRY_RUN" = "1" ]; then
        echo "  [dry-run] would link skills into $dest"
        return 0
    fi
    mkdir -p "$dest"

    while IFS= read -r -d '' skill_dir; do
        skill_name="$(basename "$skill_dir")"
        target="$dest/$skill_name"

        # Replace stale links/files; keep real directories so locally
        # installed skills that A-Wiki does not manage are never deleted.
        if [ -L "$target" ] || [ -f "$target" ]; then
            rm -f "$target"
        elif [ -d "$target" ]; then
            echo "  ⚠️  Skipping existing directory: $target"
            continue
        fi

        if create_link "$skill_dir" "$target"; then
            linked=$((linked + 1))
        else
            failed=$((failed + 1))
        fi
    done < <(list_skill_sources)

    echo "  ✅ $linked skills linked into $dest"
    if [ "$failed" -gt 0 ]; then
        echo "  ⚠️  $failed skills failed to link (Windows: enable Developer Mode or run as admin)"
    fi
}

# ── .env linking (local symlink -> real file on Drive) ─────────────────────

ensure_env_link() {
    local local_path="$1" drive_target="$2" seed="$3" label="$4"

    if [ "$DRY_RUN" = "1" ]; then
        echo "  [dry-run] env link $local_path -> $drive_target"
        return 0
    fi

    # Healthy symlink — nothing to do; broken symlink — re-create below
    if [ -L "$local_path" ]; then
        if [ -e "$local_path" ]; then
            echo "  OK (already linked) — $label"
            return 0
        fi
        echo "  ⚠️  $label symlink broken — re-linking"
        rm -f "$local_path"
    fi

    # Real file — never clobber silently; --force migrates content to Drive
    if [ -e "$local_path" ]; then
        if [ "$FORCE" != "1" ]; then
            echo "  ⚠️  $label is a real local file — kept as-is (re-run with --force to migrate it to Drive)"
            return 0
        fi
        mkdir -p "$(dirname "$drive_target")"
        if [ ! -f "$drive_target" ]; then
            cp "$local_path" "$drive_target"
            echo "  OK — migrated $label content to $drive_target"
        else
            cp "$local_path" "${drive_target}.backup-$(date +%Y%m%d%H%M%S)"
            echo "  OK — Drive copy kept; local $label backed up beside it"
        fi
        rm -f "$local_path"
    fi

    # Ensure the real file exists on Drive (seed from template when available)
    mkdir -p "$(dirname "$drive_target")"
    if [ ! -f "$drive_target" ]; then
        if [ -n "$seed" ] && [ -f "$seed" ]; then
            cp "$seed" "$drive_target"
        else
            : > "$drive_target"
        fi
        chmod 600 "$drive_target" 2>/dev/null || true
    fi

    if create_link "$drive_target" "$local_path"; then
        echo "  OK — linked $label -> $drive_target"
    else
        # Symlinks unavailable (Windows without Developer Mode): junctions
        # cannot point at single files, so fall back to a copy.
        cp "$drive_target" "$local_path"
        echo "  ⚠️  no symlink support — copied Drive .env to $label (re-run after editing the Drive copy)"
    fi
}

env_state() {
    local p="$1"
    if [ -L "$p" ]; then
        if [ -e "$p" ]; then
            echo "linked"
        else
            echo "broken (target missing — Drive offline or moved)"
        fi
    elif [ -f "$p" ]; then
        echo "local file (not Drive-backed; --force to migrate)"
    else
        echo "not linked"
    fi
}

# ── agent selection ─────────────────────────────────────────────────────────

active_agents() {
    local a dir
    if [ -n "$REQUESTED_AGENTS" ]; then
        for a in $REQUESTED_AGENTS; do
            echo "$a"
        done
        return 0
    fi
    for a in $AGENT_NAMES; do
        dir="$(agent_dir "$a")"
        if [ -d "$dir" ]; then
            echo "$a"
        fi
    done
    return 0
}

# ── modes ───────────────────────────────────────────────────────────────────

do_link() {
    echo "🔗 A-Wiki universal agent linker"
    echo "   repo:  $REPO_ROOT"
    echo "   drive: $DRIVE_ROOT"

    local a dir found=0
    for a in $(active_agents); do
        found=1
        dir="$(agent_dir "$a")"
        if [ ! -d "$dir" ]; then
            if [ "$DRY_RUN" = "1" ]; then
                echo "  [dry-run] mkdir -p $dir"
            else
                mkdir -p "$dir"
            fi
        fi
        echo ""
        echo "▶ $a ($dir)"
        if [ "$DO_SKILLS" = "1" ]; then
            link_skills_into "$dir/skills"
        fi
        if [ "$DO_ENV" = "1" ] && is_env_agent "$a"; then
            ensure_env_link "$dir/.env" "$DRIVE_ROOT/.agents/$a/.env" "" "$a/.env"
        fi
    done

    if [ "$found" = "0" ]; then
        echo "  (no agent dirs detected — nothing to link; use --agent <name> to force one)"
    fi

    if [ "$DO_ENV" = "1" ] && [ "$SKIP_REPO_ENV" != "1" ]; then
        echo ""
        echo "▶ repo .env"
        ensure_env_link "$REPO_ROOT/.env" "$DRIVE_ROOT/.env" "$REPO_ROOT/.env.example" "repo .env"
    fi

    if [ -d "${AWIKI_AGENT_DIR_KILO:-$HOME/.config/kilo}" ] && [ -f "$REPO_ROOT/scripts/setup-kilo-config.sh" ]; then
        echo ""
        echo "ℹ️  kilo: rendered by scripts/setup-kilo-config.sh (runs inside setup-local.sh)"
    fi

    echo ""
    echo "✅ Done. Verify anytime: bash scripts/link-agent-configs.sh --status"
}

do_status() {
    echo "A-Wiki agent link status"
    echo "  repo:  $REPO_ROOT"
    echo "  drive: $DRIVE_ROOT"

    local a dir entry target managed broken envstate
    for a in $AGENT_NAMES; do
        dir="$(agent_dir "$a")"
        if [ ! -d "$dir" ]; then
            echo "  [ -- ] $a: not installed ($dir)"
            continue
        fi

        managed=0
        broken=0
        if [ -d "$dir/skills" ]; then
            for entry in "$dir/skills"/*; do
                [ -L "$entry" ] || continue
                target="$(readlink "$entry")"
                case "$target" in
                    "$REPO_ROOT"/*)
                        managed=$((managed + 1))
                        [ -e "$entry" ] || broken=$((broken + 1))
                        ;;
                esac
            done
        fi

        envstate="-"
        if is_env_agent "$a"; then
            envstate="$(env_state "$dir/.env")"
            case "$envstate" in
                broken*) PROBLEMS=1 ;;
            esac
        fi

        if [ "$broken" -gt 0 ]; then
            PROBLEMS=1
            echo "  [FAIL] $a: $managed skills linked ($broken BROKEN); .env: $envstate"
        else
            echo "  [ OK ] $a: $managed skills linked; .env: $envstate"
        fi
    done

    if [ "$SKIP_REPO_ENV" != "1" ]; then
        local rstate
        rstate="$(env_state "$REPO_ROOT/.env")"
        case "$rstate" in
            broken*) PROBLEMS=1 ;;
        esac
        echo "  repo .env: $rstate"
    fi

    if [ "$PROBLEMS" = "1" ]; then
        echo "  ✗ problems found — fix with: bash scripts/link-agent-configs.sh"
        return 1
    fi
    echo "  ✓ all good"
    return 0
}

do_unlink() {
    local a dir entry target
    for a in $(active_agents); do
        dir="$(agent_dir "$a")"
        [ -d "$dir" ] || continue

        if [ -d "$dir/skills" ]; then
            for entry in "$dir/skills"/*; do
                [ -L "$entry" ] || continue
                target="$(readlink "$entry")"
                case "$target" in
                    "$REPO_ROOT"/*) run_rm "$entry" ;;
                esac
            done
        fi
        if [ -L "$dir/.env" ]; then
            target="$(readlink "$dir/.env")"
            case "$target" in
                "$DRIVE_ROOT"/*) run_rm "$dir/.env" ;;
            esac
        fi
        echo "  unlinked: $a"
    done

    if [ "$SKIP_REPO_ENV" != "1" ] && [ -L "$REPO_ROOT/.env" ]; then
        target="$(readlink "$REPO_ROOT/.env")"
        case "$target" in
            "$DRIVE_ROOT"/*) run_rm "$REPO_ROOT/.env" ;;
        esac
    fi
    echo "✅ managed links removed (Drive-side data untouched)"
}

do_list() {
    local a dir st n=0 d
    echo "Agents:"
    for a in $AGENT_NAMES; do
        dir="$(agent_dir "$a")"
        if [ -d "$dir" ]; then st="installed"; else st="not installed"; fi
        printf '  %-12s %s (%s)\n' "$a" "$dir" "$st"
    done
    echo ""
    echo "Skills that will be linked:"
    while IFS= read -r -d '' d; do
        n=$((n + 1))
        printf '  • %s/%s\n' "$(basename "$(dirname "$d")")" "$(basename "$d")"
    done < <(list_skill_sources)
    echo ""
    echo "Total: $n skills"
}

# ── args ────────────────────────────────────────────────────────────────────

while [ $# -gt 0 ]; do
    case "$1" in
        --all) MODE="link" ;;
        --agent)
            shift
            if [ $# -eq 0 ]; then
                echo "error: --agent needs a name (known: $AGENT_NAMES)" >&2
                exit 1
            fi
            case " $AGENT_NAMES " in
                *" $1 "*) REQUESTED_AGENTS="$REQUESTED_AGENTS $1" ;;
                *)
                    echo "error: unknown agent '$1' (known: $AGENT_NAMES)" >&2
                    echo "hint: set AWIKI_AGENT_DIR_<NAME> to add a custom harness dir" >&2
                    exit 1
                    ;;
            esac
            ;;
        --status) MODE="status" ;;
        --unlink) MODE="unlink" ;;
        --list) MODE="list" ;;
        --skills-only) DO_ENV=0 ;;
        --env-only) DO_SKILLS=0 ;;
        --no-repo-env) SKIP_REPO_ENV=1 ;;
        --dry-run) DRY_RUN=1 ;;
        --force) FORCE=1 ;;
        --repo-root)
            shift
            if [ $# -eq 0 ] || [ ! -d "$1" ]; then
                echo "error: --repo-root needs an existing directory" >&2
                exit 1
            fi
            REPO_ROOT="$(cd "$1" && pwd)"
            ;;
        --help|-h) usage; exit 0 ;;
        *)
            echo "unknown flag: $1" >&2
            usage
            exit 1
            ;;
    esac
    shift
done

DRIVE_ROOT="$(resolve_drive_root)"

case "$MODE" in
    link)   do_link ;;
    status) do_status ;;
    unlink) do_unlink ;;
    list)   do_list ;;
esac
