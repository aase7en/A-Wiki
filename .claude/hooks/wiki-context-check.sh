#!/bin/bash
# SessionStart hook: ตรวจ wiki-overview.md freshness + auto-rebuild เมื่อ stale (0 token)
# ผล: Claude รู้ state ทันทีโดยไม่ต้องอ่านไฟล์เอง + index ไม่มีวัน stale

# Lean mode (token-save): skip — freshness check resumes on the next full session
if [ "${AWIKI_LEAN_SESSION_START:-0}" = "1" ]; then exit 0; fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OVERVIEW="$REPO_ROOT/wiki/context/wiki-overview.md"

if [ ! -f "$OVERVIEW" ]; then
    echo "⚠️  wiki-overview.md ไม่มี — กำลัง auto-build..."
    if command -v python3 >/dev/null 2>&1; then
        cd "$REPO_ROOT" && python3 scripts/gen-index.py >/dev/null 2>&1 && echo "✅ wiki-overview.md สร้างเสร็จแล้ว"
    else
        echo "    → ไม่มี python3 รัน: python3 scripts/gen-index.py เอง"
    fi
    exit 0
fi

# Cross-platform mod time
if stat -c %Y "$OVERVIEW" &>/dev/null 2>&1; then
    MOD=$(stat -c %Y "$OVERVIEW")   # Linux
else
    MOD=$(stat -f %m "$OVERVIEW")   # macOS
fi
NOW=$(date +%s)
DAYS_OLD=$(( (NOW - MOD) / 86400 ))

ENTRY_COUNT=$(grep -c "^| \`" "$OVERVIEW" 2>/dev/null || echo "?")
BRANCH=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || echo "unknown")
MOD_DATE=$(date -d "@$MOD" "+%Y-%m-%d" 2>/dev/null || date -r "$MOD" "+%Y-%m-%d" 2>/dev/null || echo "unknown")

if [ "$DAYS_OLD" -gt 1 ] && command -v python3 >/dev/null 2>&1; then
    # Auto-rebuild when stale > 1 day
    echo "🔄 wiki-overview.md อายุ ${DAYS_OLD}d — auto-rebuilding index..."
    cd "$REPO_ROOT" && python3 scripts/gen-index.py >/dev/null 2>&1
    ENTRY_COUNT=$(grep -c "^| \`" "$OVERVIEW" 2>/dev/null || echo "?")
    MOD_DATE=$(date "+%Y-%m-%d")
    echo "✅ wiki-overview.md rebuilt (${MOD_DATE}) | ${ENTRY_COUNT} entries | branch: ${BRANCH}"
else
    echo "✅ wiki-overview.md fresh (${DAYS_OLD}d ago, ${MOD_DATE}) | ${ENTRY_COUNT} entries | branch: ${BRANCH}"
fi

# --- Model Roster freshness check ---
ROSTER_CONF="$REPO_ROOT/wiki/context/model-roster.conf"
if [ -f "$ROSTER_CONF" ]; then
    if stat -c %Y "$ROSTER_CONF" &>/dev/null 2>&1; then
        ROSTER_MOD=$(stat -c %Y "$ROSTER_CONF")
    else
        ROSTER_MOD=$(stat -f %m "$ROSTER_CONF")
    fi
    ROSTER_DAYS=$(( (NOW - ROSTER_MOD) / 86400 ))
    if [ "$ROSTER_DAYS" -gt 7 ] && [ -n "${OPENROUTER_API_KEY:-}" ]; then
        echo "🔄 model-roster อายุ ${ROSTER_DAYS}d — auto-scouting new models..."
        cd "$REPO_ROOT" && bash scripts/update-model-roster.sh >/dev/null 2>&1 && \
            echo "✅ model-roster updated" || echo "⚠️  model-roster update failed (network?)"
    elif [ "$ROSTER_DAYS" -gt 7 ]; then
        echo "⚠️  model-roster อายุ ${ROSTER_DAYS}d — set OPENROUTER_API_KEY เพื่อ auto-update"
    fi
fi
