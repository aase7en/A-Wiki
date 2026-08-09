#!/usr/bin/env bash
# session-start-a-router.sh — inject the A-Suite pointer at session start.
#
# STATIC AND TINY ON PURPOSE (~200 tokens). The full routing table lives in
# wiki/A-ROUTER.md and is read on demand. a-plan and a-debug were deliberately
# moved from invocation:both to manual to save ~1.2k tokens per session each —
# injecting the whole table here would hand that saving straight back.
#
# stdout is appended to the session context by Claude Code, same mechanism as
# .claude/hooks/session-start-initial-context.sh.
#
# Disable with AWIKI_A_ROUTER_STUB=0.
set -u

[ "${AWIKI_A_ROUTER_STUB:-1}" = "0" ] && exit 0
[ "${AWIKI_LEAN_SESSION_START:-0}" = "1" ] && exit 0

cat <<'EOF'
🎯 A-Suite: ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST
   /A-Think (fallback) · /A-Plan ออกแบบ · /A-Doc เอกสาร · /A-Council รีวิว
   /A-Debug แก้บั๊ก · /A-Flow pipeline · /A-Loop งานยาว · /A-Escalate ส่งโมเดลเก่งกว่า
   ไม่รู้ใช้ตัวไหน → MCP `skill_route` หรืออ่าน wiki/A-ROUTER.md
   เริ่มงานหลาย step → MCP `focus_set` (กันหลุด phase)
EOF
exit 0
