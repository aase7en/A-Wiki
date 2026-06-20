#!/bin/bash
# A-Wiki → Hermes on Raspberry Pi 5 — One-shot Brain Sync
# 2026-06-20 | source: A-Wiki AGENTS.md + lifecycle skills
#
# What this does:
#   1. Clones/pulls A-Wiki repo
#   2. Links all lifecycle skills into Hermes skill dir
#   3. Registers agent personas
#   4. Installs lifecycle router as session hook
#   5. Configures Hermes to load A-Wiki brain at startup
#
# Run once after Hermes is installed on Pi 5:
#   bash scripts/hermes/awiki-init-pi5.sh

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }

# ---- Config ----
A_WIKI_REPO="${A_WIKI_REPO:-https://github.com/aase7en/A-Wiki.git}"
A_WIKI_DIR="${A_WIKI_DIR:-$HOME/A-Wiki}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_SKILLS="${HERMES_SKILLS:-$HERMES_HOME/skills}"
HERMES_HOOKS="${HERMES_HOOKS:-$HERMES_HOME/hooks}"
HERMES_CONFIG="${HERMES_CONFIG:-$HERMES_HOME/config.yaml}"

echo "============================================"
echo "  A-Wiki → Hermes Brain Sync (Pi 5)"
echo "============================================"

# ---- Step 1: Clone / pull A-Wiki ----
if [ -d "$A_WIKI_DIR/.git" ]; then
  info "A-Wiki already cloned at $A_WIKI_DIR — pulling latest"
  git -C "$A_WIKI_DIR" pull --ff-only
else
  info "Cloning A-Wiki to $A_WIKI_DIR"
  git clone "$A_WIKI_REPO" "$A_WIKI_DIR"
fi

# ---- Step 2: Verify Hermes is installed ----
if ! command -v hermes &>/dev/null; then
  warn "Hermes CLI not found. Install first:"
  warn "  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
  warn "Then re-run this script."
  exit 1
fi
info "Hermes $(hermes version 2>/dev/null | head -1 || echo 'installed')"

# ---- Step 3: Link lifecycle skills ----
mkdir -p "$HERMES_SKILLS/lifecycle"
LIFECYCLE_DIR="$A_WIKI_DIR/skills/engineering-lifecycle"

if [ -d "$LIFECYCLE_DIR" ]; then
  info "Linking lifecycle skills → $HERMES_SKILLS/lifecycle/"
  for phase_dir in "$LIFECYCLE_DIR"/*/; do
    phase=$(basename "$phase_dir")
    for skill_dir in "$phase_dir"*/; do
      skill=$(basename "$skill_dir")
      skill_name="${skill//-/ }"
      if [ -f "$skill_dir/SKILL.md" ]; then
        ln -sf "$skill_dir" "$HERMES_SKILLS/lifecycle/$skill"
      fi
    done
  done
  # Link meta-skill
  if [ -f "$LIFECYCLE_DIR/awiki-lifecycle-router/SKILL.md" ]; then
    mkdir -p "$HERMES_SKILLS/awiki"
    ln -sf "$LIFECYCLE_DIR/awiki-lifecycle-router" "$HERMES_SKILLS/awiki/lifecycle-router"
    info "Meta-skill linked"
  fi
  info "Linked $(ls -d "$HERMES_SKILLS/lifecycle"/*/ 2>/dev/null | wc -l) lifecycle skills"
else
  warn "Lifecycle skills dir not found at $LIFECYCLE_DIR — skipping"
fi

# ---- Step 4: Link A-Wiki native skills (debug-mantra, scrutinize, etc.) ----
NATIVE_SKILLS_DIR="$A_WIKI_DIR/skills/engineering"
if [ -d "$NATIVE_SKILLS_DIR" ]; then
  mkdir -p "$HERMES_SKILLS/awiki/native"
  info "Linking A-Wiki native skills"
  for skill_dir in "$NATIVE_SKILLS_DIR"/*/; do
    skill=$(basename "$skill_dir")
    if [ -f "$skill_dir/SKILL.md" ]; then
      ln -sf "$skill_dir" "$HERMES_SKILLS/awiki/native/$skill"
    fi
  done
fi

# ---- Step 5: Link agent personas ----
AGENTS_DIR="$A_WIKI_DIR/agents"
if [ -d "$AGENTS_DIR" ]; then
  mkdir -p "$HERMES_HOME/agents"
  info "Linking agent personas (code-reviewer, test-engineer, security-auditor, web-performance-auditor)"
  for persona in "$AGENTS_DIR"/*.md; do
    pname=$(basename "$persona" .md)
    ln -sf "$persona" "$HERMES_HOME/agents/$pname.md"
  done
  info "Linked $(ls "$AGENTS_DIR"/*.md 2>/dev/null | wc -l) personas"
fi

# ---- Step 6: Register lifecycle config with Hermes ----
LIFECYCLE_CONFIG="$A_WIKI_DIR/scripts/hermes/lifecycle-config.json"
if [ -f "$LIFECYCLE_CONFIG" ]; then
  info "Registering lifecycle config with Hermes"
  mkdir -p "$HERMES_HOME/config.d"
  cp "$LIFECYCLE_CONFIG" "$HERMES_HOME/config.d/awiki-lifecycle.json"
  info "Config copied to $HERMES_HOME/config.d/awiki-lifecycle.json"
fi

# ---- Step 7: Install session hook ----
HOOKS_SRC="$A_WIKI_DIR/hooks/lifecycle-session-start.sh"
if [ -f "$HOOKS_SRC" ]; then
  mkdir -p "$HERMES_HOOKS"
  info "Installing A-Wiki session start hook"
  cp "$HOOKS_SRC" "$HERMES_HOOKS/awiki-session-start.sh"
  chmod +x "$HERMES_HOOKS/awiki-session-start.sh"

  # Register hook in Hermes hooks.json if it exists
  HOOKS_JSON="$HERMES_HOME/hooks.json"
  if [ ! -f "$HOOKS_JSON" ]; then
    echo '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"bash ~/.hermes/hooks/awiki-session-start.sh"}]}]}}' > "$HOOKS_JSON"
    info "Created hooks.json with A-Wiki session hook"
  else
    warn "hooks.json already exists — you may need to manually add:"
    warn "  bash ~/.hermes/hooks/awiki-session-start.sh"
    warn "  to the SessionStart hook array in $HOOKS_JSON"
  fi
fi

# ---- Step 8: Set A-Wiki as default context in config ----
if [ -f "$HERMES_CONFIG" ]; then
  info "A-Wiki config: adding A_WIKI_DIR and skills path to Hermes config"
  # Append A-Wiki env vars to Hermes .env if not already there
  HERMES_ENV="$HERMES_HOME/.env"
  if ! grep -q "A_WIKI_DIR" "$HERMES_ENV" 2>/dev/null; then
    echo "# A-Wiki brain integration (added by awiki-init-pi5.sh)" >> "$HERMES_ENV"
    echo "export A_WIKI_DIR=$A_WIKI_DIR" >> "$HERMES_ENV"
    echo "export A_WIKI_LIFECYCLE_SKILLS=$HERMES_SKILLS/lifecycle" >> "$HERMES_ENV"
    echo "export A_WIKI_NATIVE_SKILLS=$HERMES_SKILLS/awiki/native" >> "$HERMES_ENV"
    echo "export HERMES_AGENTS_DIR=$HERMES_HOME/agents" >> "$HERMES_ENV"
    echo "export HERMES_HOOKS_DIR=$HERMES_HOOKS" >> "$HERMES_ENV"
    info "Environment variables set in $HERMES_ENV"
  else
    warn "A_WIKI_DIR already in .env — skipping env addition"
  fi
fi

# ---- Step 9: Verify ----
echo ""
echo "============================================"
echo "  Verification"
echo "============================================"
echo ""
echo "  A-Wiki:    $A_WIKI_DIR $(git -C "$A_WIKI_DIR" rev-parse --short HEAD 2>/dev/null)"
echo "  Hermes:    $(hermes version 2>/dev/null | head -1 || echo 'N/A')"
echo "  Skills:    $(ls -d "$HERMES_SKILLS"/lifecycle/*/ 2>/dev/null | wc -l) lifecycle"
echo "  Personas:  $(ls "$HERMES_HOME"/agents/*.md 2>/dev/null | wc -l)"
echo "  Config:    $(ls "$HERMES_HOME"/config.d/awiki-lifecycle.json 2>/dev/null && echo '✅' || echo '❌')"
echo "  Hook:      $(ls "$HERMES_HOOKS"/awiki-session-start.sh 2>/dev/null && echo '✅' || echo '❌')"
echo ""

# ---- Optional: Telegram + Dashboard ----
if [ "$1" == "--full" ]; then
  echo ""
  echo "============================================"
  echo "  Full Setup: Telegram + Dashboard"
  echo "============================================"
  echo ""
  hermes gateway setup 2>/dev/null || warn "Skipping gateway setup (run manually: hermes gateway setup)"
  cd "$A_WIKI_DIR" && nohup python3 scripts/live-dashboard/server.py > /dev/null 2>&1 &
  info "Live Dashboard started on port 7790"
fi

echo ""
info "A-Wiki brain sync complete. Start Hermes with:"
echo "  hermes"
echo "  hermes chat -q \"ทำอะไรได้บ้าง\"  # ใช้ A-Wiki brain"
echo ""
echo "For full A-Wiki integration, load the lifecycle router:"
echo "  hermes skills config"
echo ""
