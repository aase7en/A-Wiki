#!/usr/bin/env bash
# A-Wiki local setup — run once per machine after cloning
# Works on: macOS (symlink) and Windows/Git Bash (junction via PowerShell)
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== A-Wiki Local Setup ==="
echo "Repo: $REPO_ROOT"
echo "OS:   $(uname -s)"
echo ""

# ── 1. raw → Google Drive junction/symlink ──────────────────────────────────

setup_raw() {
  echo "[1/7] Setting up drive/ + raw/ links via setup-cloud-link.sh..."
  # Delegate to multi-provider script. Uses --auto for non-interactive setup.
  # If drive/ not yet linked, this will also handle that (multi-provider auto-pick).
  if bash "$(dirname "$0")/setup-cloud-link.sh" --auto; then
    echo "  OK — cloud links configured"
  else
    echo "  WARN: cloud link setup failed — run 'bash scripts/setup-cloud-link.sh' manually" >&2
    return 0  # non-fatal, continue with other setup steps
  fi
}

# ── 2. .mcp.json — generate from example ───────────────────────────────────

setup_mcp() {
  echo "[2/7] Setting up .mcp.json..."

  if [[ -f ".mcp.json" ]]; then
    echo "  .mcp.json already exists — skipping"
    return
  fi

  case "$(uname -s)" in
    Darwin*)
      PYTHON_CMD="python3"
      FS_PATH="$REPO_ROOT"
      ;;
    MINGW*|CYGWIN*|MSYS*)
      PYTHON_CMD="python"
      # Convert to forward-slash Windows path
      FS_PATH=$(cygpath -m "$REPO_ROOT")
      ;;
    *)
      PYTHON_CMD="python3"
      FS_PATH="$REPO_ROOT"
      ;;
  esac

  sed \
    -e "s|/REPLACE/WITH/YOUR/REPO/PATH|$FS_PATH|g" \
    -e "s|REPLACE_python3_or_python|$PYTHON_CMD|g" \
    .mcp.json.example > .mcp.json

  echo "  OK — .mcp.json created (filesystem: $FS_PATH, python: $PYTHON_CMD)"
}

# ── 3. Sync API keys from Google Drive → settings.local.json ───────────────

setup_secrets() {
  echo "[3/7] Syncing API keys from Google Drive .secrets..."

  SYNC_SCRIPT="scripts/import-keys.py"
  if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo "  scripts/import-keys.py not found — skipping"
    return
  fi

  python3 "$SYNC_SCRIPT" 2>/dev/null || python "$SYNC_SCRIPT"
}

# ── 4. Private journal files — local only, never committed ─────────────────

setup_private_journal() {
  echo "[4/8] Setting up private journal files..."
  mkdir -p wiki/context

  mkdir -p drive/personal/journal 2>/dev/null || true

  ensure_private_file() {
    local local_path="$1"
    local drive_path="$2"
    local example_path="$3"

    if [[ -e "$local_path" ]]; then
      echo "  $local_path already exists — skipping"
      return 0
    fi

    if [[ -f "$drive_path" ]]; then
      case "$(uname -s)" in
        Darwin*|Linux*)
          ln -s "$drive_path" "$local_path"
          echo "  OK — linked $local_path -> $drive_path"
          ;;
        *)
          cp "$drive_path" "$local_path"
          echo "  OK — copied $drive_path -> $local_path"
          ;;
      esac
      return 0
    fi

    if [[ -f "$example_path" ]]; then
      cp "$example_path" "$local_path"
      echo "  OK — created $local_path from $example_path"
    else
      echo "  WARN: missing template $example_path" >&2
    fi
  }

  ensure_private_file "log.md" "drive/personal/journal/log.md" "log.md.example"
  ensure_private_file "wiki/context/session-memory.md" \
    "drive/personal/journal/wiki-context-session-memory.md" \
    "wiki/context/session-memory.md.example"
}

# ── 5. Build SQLite wiki index ──────────────────────────────────────────────

setup_index() {
  echo "[5/8] Building SQLite wiki index (FTS5 search)..."

  if [[ ! -f "scripts/gen-index.py" ]]; then
    echo "  scripts/gen-index.py not found — skipping"
    return
  fi

  python3 scripts/gen-index.py 2>/dev/null || python scripts/gen-index.py
  echo "  OK — wiki index built"
}

# ── 6. .codex/ hooks — link to .claude/hooks/ ──────────────────────────────

setup_codex() {
  echo "[6/8] Setting up .codex/ hooks link..."

  if [[ -f "scripts/setup-codex-hooks.sh" ]]; then
    bash scripts/setup-codex-hooks.sh
    echo "  OK — Codex Desktop hooks configured"
    return
  fi

  mkdir -p .codex

  case "$(uname -s)" in
    Darwin*)
      ln -sfn "$(pwd)/.claude/hooks" .codex/hooks
      echo "  OK — symlink: .codex/hooks -> .claude/hooks"
      ;;
    MINGW*|CYGWIN*|MSYS*)
      powershell.exe -Command "New-Item -ItemType Junction -Path '$(pwd)/.codex/hooks' -Target '$(cygpath -w "$(pwd)/.claude/hooks")'" > /dev/null
      echo "  OK — junction: .codex/hooks -> .claude/hooks"
      ;;
    *)
      echo "  Unknown OS — please link .codex/hooks -> .claude/hooks manually"
      ;;
  esac
}

# ── 7. Model intel cache — optional Gemini grounded refresh ────────────────
# Off by default during setup to avoid network/API surprises. SessionStart will
# refresh it later when GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY is available.
# Enable now with: AWIKI_REFRESH_MODEL_INTEL=1 bash scripts/setup-local.sh

setup_model_intel() {
  echo "[7/8] Preparing AI model intel cache..."
  mkdir -p .tmp/model-intel
  if [[ "${AWIKI_REFRESH_MODEL_INTEL:-0}" != "1" ]]; then
    echo "  skipped live refresh — set AWIKI_REFRESH_MODEL_INTEL=1 to run now"
    return 0
  fi
  if [[ ! -f "scripts/update-ai-model-intel.sh" ]]; then
    echo "  scripts/update-ai-model-intel.sh not found — skipping"
    return 0
  fi
  bash scripts/update-ai-model-intel.sh --offline-ok || {
    echo "  WARN: model intel refresh failed — session can still use cached/static roster" >&2
    return 0
  }
}

setup_model_router_policy() {
  echo "  Refreshing local model router policy..."
  if [[ -f "scripts/model-router-policy.py" ]]; then
    python3 scripts/model-router-policy.py --quiet || {
      echo "  WARN: model router policy refresh failed — delegate.sh will fallback to roster" >&2
      return 0
    }
  fi
}

# ── 6. (optional) react-doctor — Claude Code skill for React audits ────────
# Off by default. Enable with: INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh
# A-Wiki itself has no React; this benefits dream projects (Sunday Estate, etc.).
# See: wiki/entities/ai-tools/react-doctor.md

setup_react_doctor() {
  if [[ "${INSTALL_REACT_DOCTOR:-0}" != "1" ]]; then
    return 0
  fi
  echo "[optional] Installing react-doctor as Claude Code skill (INSTALL_REACT_DOCTOR=1)..."
  if ! command -v npx >/dev/null 2>&1; then
    echo "  WARN: npx not found — install Node.js 18+ first" >&2
    return 0
  fi
  npx -y react-doctor@latest install || {
    echo "  WARN: react-doctor install failed — re-run manually if needed" >&2
    return 0
  }
  echo "  OK — react-doctor skill registered (~/.claude/skills/)"
}

# ── 8. (optional) SkillOpt — local install only, not committed ─────────────
# Enable with: INSTALL_SKILLOPT=1 bash scripts/setup-local.sh

setup_skillopt() {
  echo "[8/8] SkillOpt optional integration..."
  if [[ "${INSTALL_SKILLOPT:-0}" != "1" ]]; then
    echo "  skipped install — set INSTALL_SKILLOPT=1 to install into .venv-skillopt"
    return 0
  fi
  if [[ ! -f "scripts/install-skillopt-local.sh" ]]; then
    echo "  scripts/install-skillopt-local.sh not found — skipping"
    return 0
  fi
  bash scripts/install-skillopt-local.sh || {
    echo "  WARN: SkillOpt install failed — inspect network/Python dependencies and retry" >&2
    return 0
  }
}

setup_raw
setup_mcp
setup_secrets
setup_private_journal
setup_index
setup_codex
setup_model_intel
setup_model_router_policy
setup_skillopt
setup_react_doctor

echo ""
echo "=== Setup complete ==="
echo "To re-sync keys after adding new ones to Google Drive .secrets:"
echo "  python scripts/import-keys.py"
echo "To refresh free model roster:"
echo "  bash scripts/update-model-roster.sh"
echo "To refresh current model/agent intel cache:"
echo "  bash scripts/update-ai-model-intel.sh --force --print"
echo "To snapshot Microsoft SkillOpt upstream metadata/core prompts:"
echo "  bash scripts/refresh-skillopt.sh"
echo "To install runnable SkillOpt locally:"
echo "  INSTALL_SKILLOPT=1 bash scripts/setup-local.sh"
echo "To install react-doctor skill (for dream projects with React):"
echo "  INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh"
echo "To verify this clone is ready for real A-Wiki work:"
echo "  python3 scripts/verify-awiki-ready.py"
echo "To verify OS-specific dependencies and sqlite-vec on this machine:"
echo "  python3 scripts/verify-cross-platform.py --build-vec"
echo "To inspect A-Wiki-owned skill quality:"
echo "  python3 scripts/skill-quality-report.py"
echo "To inspect SessionStart TODO hygiene:"
echo "  python3 scripts/todo-health.py"
