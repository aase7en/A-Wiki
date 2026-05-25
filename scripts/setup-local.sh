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
  echo "[1/3] Setting up raw/ link to Google Drive..."

  if [[ -L "raw" || -d "raw" ]]; then
    echo "  raw already exists ($(file raw 2>/dev/null || echo 'directory'))"
    return
  fi
  if [[ -f "raw" ]]; then
    echo "  Removing stale raw file..."
    rm -f raw
  fi

  case "$(uname -s)" in
    Darwin*)
      # macOS — Google Drive via CloudStorage
      GDRIVE_PATH="/Users/$(whoami)/Library/CloudStorage"
      RAW_TARGET=$(find "$GDRIVE_PATH" -maxdepth 3 -name "A-Wiki-Data" -type d 2>/dev/null | head -1)
      if [[ -z "$RAW_TARGET" ]]; then
        echo "  ERROR: Cannot find A-Wiki-Data in Google Drive ($GDRIVE_PATH)"
        echo "  Please create symlink manually: ln -s /path/to/A-Wiki-Data/raw raw"
        return 1
      fi
      ln -sfn "$RAW_TARGET/raw" raw
      echo "  OK — symlink: raw -> $RAW_TARGET/raw"
      ;;
    MINGW*|CYGWIN*|MSYS*)
      # Windows/Git Bash — Google Drive at L:\My Drive\A-Wiki-Data
      GDRIVE_WIN="L:/My Drive/A-Wiki-Data/raw"
      if [[ ! -d "$GDRIVE_WIN" ]]; then
        echo "  ERROR: Cannot find Google Drive at $GDRIVE_WIN"
        echo "  Ensure Google Drive is mounted at L: and A-Wiki-Data folder exists"
        return 1
      fi
      powershell.exe -Command "New-Item -ItemType Junction -Path '$(pwd)/raw' -Target '$(cygpath -w "$GDRIVE_WIN")'" > /dev/null
      echo "  OK — junction: raw -> $GDRIVE_WIN"
      ;;
    *)
      echo "  Unknown OS — please create raw link manually"
      ;;
  esac
}

# ── 2. .mcp.json — generate from example ───────────────────────────────────

setup_mcp() {
  echo "[2/3] Setting up .mcp.json..."

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
  echo "[3/4] Syncing API keys from Google Drive .secrets..."

  SYNC_SCRIPT="scripts/import-keys.py"
  if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo "  scripts/import-keys.py not found — skipping"
    return
  fi

  python3 "$SYNC_SCRIPT" 2>/dev/null || python "$SYNC_SCRIPT"
}

# ── 4. Build SQLite wiki index ──────────────────────────────────────────────

setup_index() {
  echo "[4/5] Building SQLite wiki index (FTS5 search)..."

  if [[ ! -f "scripts/gen-index.py" ]]; then
    echo "  scripts/gen-index.py not found — skipping"
    return
  fi

  python3 scripts/gen-index.py 2>/dev/null || python scripts/gen-index.py
  echo "  OK — wiki index built"
}

# ── 5. .codex/ hooks — link to .claude/hooks/ ──────────────────────────────

setup_codex() {
  echo "[5/5] Setting up .codex/ hooks link..."

  mkdir -p .codex

  if [[ -L ".codex/hooks" || -d ".codex/hooks" ]]; then
    echo "  .codex/hooks already exists — skipping"
    return
  fi

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

setup_raw
setup_mcp
setup_secrets
setup_index
setup_codex

echo ""
echo "=== Setup complete ==="
echo "To re-sync keys after adding new ones to Google Drive .secrets:"
echo "  python scripts/import-keys.py"
echo "To refresh free model roster:"
echo "  bash scripts/update-model-roster.sh"
