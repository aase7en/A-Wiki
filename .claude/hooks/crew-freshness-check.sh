#!/usr/bin/env bash
# SessionStart hook: ตรวจ crew.md freshness + API key status (0 token)
# เตือนถ้า model pricing/availability อาจเปลี่ยนไปแล้ว (>30 วัน)

CREW_DOC="docs/protocols/crew.md"
WARN_DAYS=30

if [ ! -f "$CREW_DOC" ]; then
    echo "⚠️  [crew] docs/protocols/crew.md ไม่มี — ระบบ Straw Hat Crew ยังไม่ได้ตั้งค่า"
    exit 0
fi

# Cross-platform mod time
if stat -c %Y "$CREW_DOC" &>/dev/null 2>&1; then
    MOD=$(stat -c %Y "$CREW_DOC")   # Linux
else
    MOD=$(stat -f %m "$CREW_DOC")   # macOS
fi
NOW=$(date +%s)
DAYS_OLD=$(( (NOW - MOD) / 86400 ))
MOD_DATE=$(date -d "@$MOD" "+%Y-%m-%d" 2>/dev/null \
        || date -r "$MOD" "+%Y-%m-%d" 2>/dev/null \
        || echo "unknown")

# ตรวจ API keys ที่มีอยู่
READY=()
MISSING=()
declare -A KEY_MAP=(
    ["Nami🗺️"]="GOOGLE_AI_STUDIO_KEY"
    ["Robin📚"]="DEEPSEEK_API_KEY"
    ["Luffy⚡"]="GROQ_API_KEY"
    ["Franky🔧"]="OPENROUTER_API_KEY"
)
for name in "Nami🗺️" "Robin📚" "Luffy⚡" "Franky🔧"; do
    env_var="${KEY_MAP[$name]}"
    if [ -n "${!env_var:-}" ]; then
        READY+=("$name")
    else
        MISSING+=("$name")
    fi
done

READY_STR=$(IFS=,; echo "${READY[*]:-none}")
MISSING_STR=$(IFS=,; echo "${MISSING[*]:-none}")

# แจ้งผล
if [ "$DAYS_OLD" -gt "$WARN_DAYS" ]; then
    echo "⚠️  [crew] crew.md อายุ ${DAYS_OLD}d (${MOD_DATE}) — model/pricing อาจเปลี่ยนแล้ว"
    echo "    → รัน: python3 scripts/crew-dispatch.py --list-crew"
    echo "    → แนะนำ: web search ราคา/model ล่าสุด แล้วอัปเดต docs/protocols/crew.md"
else
    echo "✅ [crew] crew.md fresh (${DAYS_OLD}d ago, ${MOD_DATE})"
fi

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "   Keys ready: ${READY_STR:-ไม่มีเลย} | Missing: ${MISSING_STR}"
    echo "   No free-model keys found (${MISSING_STR}) — crew tasks will use Claude (costs tokens)"
else
    echo "   All crew keys ready: ${READY_STR}"
fi
