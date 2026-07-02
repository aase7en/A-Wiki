#!/bin/bash
# =============================================================================
# Hermes Config Export — MacBook → Pi5 Migration
# =============================================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }
step()  { echo -e "${CYAN}[→]${NC} $1"; }

HERMES_BIN="${HERMES_BIN:-$HOME/.hermes/hermes-agent/venv/bin/hermes}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILE="${1:-tech_and_ai_architect}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORKDIR="/tmp/hermes-export-$$"
PACKAGE_NAME="hermes-export-${TIMESTAMP}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  Hermes Config Export — MacBook → Pi5"
echo "  Profile: $PROFILE"
echo "  Time:    $TIMESTAMP"
echo "============================================"

[ ! -x "$HERMES_BIN" ] && { err "Hermes not found at $HERMES_BIN"; exit 1; }
[ ! -d "$HERMES_HOME/profiles/$PROFILE" ] && { err "Profile '$PROFILE' not found"; exit 1; }

mkdir -p "$WORKDIR"

# Step 1: Export profile
step "Step 1/5: Exporting profile '$PROFILE'..."
cd "$WORKDIR"
"$HERMES_BIN" profile export "$PROFILE" 2>&1
EXPORT_FILE="$WORKDIR/${PROFILE}.tar.gz"
[ -f "$EXPORT_FILE" ] || { err "Export failed"; exit 1; }
info "Exported: $(du -h "$EXPORT_FILE" | cut -f1)"

# Step 2: Clean
step "Step 2/5: Cleaning transient files..."
CLEAN_DIR="$WORKDIR/$PROFILE"
mkdir -p "$CLEAN_DIR"
tar -xzf "$EXPORT_FILE" -C "$WORKDIR"

rm -rf "$CLEAN_DIR"/audio_cache "$CLEAN_DIR"/image_cache "$CLEAN_DIR"/sessions 2>/dev/null
rm -rf "$CLEAN_DIR"/logs "$CLEAN_DIR"/home "$CLEAN_DIR"/cache "$CLEAN_DIR"/cron/output 2>/dev/null
rm -f "$CLEAN_DIR"/.update_check "$CLEAN_DIR"/auth.lock "$CLEAN_DIR"/.tick.lock 2>/dev/null
rm -f "$CLEAN_DIR"/models_dev_cache.json "$CLEAN_DIR"/ollama_cloud_models_cache.json 2>/dev/null
rm -f "$CLEAN_DIR"/provider_models_cache.json "$CLEAN_DIR"/processes.json 2>/dev/null
rm -f "$CLEAN_DIR"/cron/.tick.lock "$CLEAN_DIR"/cron/.jobs.lock 2>/dev/null

PACKAGE_FILE="$WORKDIR/${PACKAGE_NAME}.tar.gz"
tar -czf "$PACKAGE_FILE" -C "$WORKDIR" "$PROFILE"
info "Clean package: $(du -h "$PACKAGE_FILE" | cut -f1)"

# Step 3: Copy to scripts/hermes/
step "Step 3/5: Copying package..."
cp "$PACKAGE_FILE" "$SCRIPT_DIR/${PACKAGE_NAME}.tar.gz"
info "Package: $SCRIPT_DIR/${PACKAGE_NAME}.tar.gz"

# Step 4: List contents summary
step "Step 4/5: Contents summary..."
echo ""
echo "  Profile includes:"
tar -tzf "$PACKAGE_FILE" | grep -E "(config.yaml|SOUL.md|MEMORY.md|USER.md|SKILL.md)" | head -20
echo "  ... ($(tar -tzf "$PACKAGE_FILE" | wc -l | tr -d ' ') files total)"

# Step 5: Create import notes
step "Step 5/5: Building import instructions..."
cat > "$SCRIPT_DIR/IMPORT-NOTES.md" << 'NOTESEOF'
# Hermes Config Import — MacBook → Pi5

## What's in the package
- `config.yaml` — All Hermes settings (model, toolsets, terminal, display, etc.)
- `SOUL.md` — Agent persona (Thai: คิดเชิงระบบ เน้นการทำงานอัตโนมัติ)
- `skills/` — 77 skills including A-Wiki skills
- `memories/` — MEMORY.md + USER.md
- `cron/` — Cron job definitions

## What's NOT in the package (needs manual handling)

| File | How to transfer |
|------|-----------------|
| `.env` (API keys) | `scp ~/.hermes/profiles/tech_and_ai_architect/.env pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/` |
| `.env` (global) | `scp ~/.hermes/.env pi@umbrel.local:~/.hermes/` |
| `auth.json` (OAuth) | `scp ~/.hermes/profiles/tech_and_ai_architect/auth.json pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/` |

## How to import on Pi5

```bash
# 1. Copy package to Pi5
scp scripts/hermes/hermes-export-*.tar.gz pi@umbrel.local:~/

# 2. SSH into Pi5 and import
ssh pi@umbrel.local
hermes profile import ~/hermes-export-*.tar.gz

# 3. Copy secrets
#    (do this on MacBook)
scp ~/.hermes/profiles/tech_and_ai_architect/.env pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/
scp ~/.hermes/profiles/tech_and_ai_architect/auth.json pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/

# 4. Adjust paths for Pi5
hermes config set terminal.cwd /home/pi/A-Wiki

# 5. Verify
hermes doctor
hermes profile show tech_and_ai_architect
```

## Path differences to fix
- `terminal.cwd`: `$REPO_ROOT` → `/home/pi/A-Wiki` (or wherever A-Wiki lives on Pi5)
- Any other `/Users/<you>` paths → adjust for Pi5

## Pi5-specific notes
- Terminal backend should be `local` (already set)
- Timezone GMT+7 (already set)
- Model will be auto-detected; run `hermes model` if needed
NOTESEOF

info "Import notes: $SCRIPT_DIR/IMPORT-NOTES.md"

# Cleanup
rm -rf "$WORKDIR"

echo ""
echo "============================================"
echo "  ✅ Export Complete"
echo "============================================"
echo ""
echo "  📦 $SCRIPT_DIR/${PACKAGE_NAME}.tar.gz"
echo "  📋 $SCRIPT_DIR/IMPORT-NOTES.md"
echo ""
echo "  Next: Copy to Pi5 then run 'hermes profile import'"
echo "============================================"
