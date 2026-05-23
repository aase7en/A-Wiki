#!/usr/bin/env bash
# PostToolUse(Bash): after git push origin main → show remaining open TODOs
# 0 tokens — pure shell, output goes to stderr (visible in Claude UI)
# Does NOT auto-tick (too error-prone) — use scripts/done.sh for that

set -uo pipefail

INPUT="$(cat)"

# Only fire on Bash tool
TOOL=$(printf '%s' "$INPUT" | python3 -c '
import sys,json
try: d=json.load(sys.stdin)
except: sys.exit(0)
print(d.get("tool_name",""))
' 2>/dev/null || true)
[ "$TOOL" != "Bash" ] && exit 0

# Only fire if command was a git push
CMD=$(printf '%s' "$INPUT" | python3 -c '
import sys,json
try: d=json.load(sys.stdin)
except: sys.exit(0)
print(d.get("tool_input",{}).get("command",""))
' 2>/dev/null || true)

echo "$CMD" | grep -qE "git push" || exit 0

# Only fire if push succeeded (exit_code = 0)
EXIT_CODE=$(printf '%s' "$INPUT" | python3 -c '
import sys,json
try: d=json.load(sys.stdin)
except: sys.exit(0)
r = d.get("tool_response", {})
# response may be string or dict
if isinstance(r, dict):
    print(r.get("exit_code", r.get("exitCode", 0)))
else:
    print(0)
' 2>/dev/null || echo "0")
[ "$EXIT_CODE" != "0" ] && exit 0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MEMORY="$REPO_ROOT/wiki/context/session-memory.md"
[ -f "$MEMORY" ] || exit 0

OPEN=$(grep "^- \[ \]" "$MEMORY" 2>/dev/null || true)
COUNT=$(echo "$OPEN" | grep -c "." 2>/dev/null || echo 0)

[ "$COUNT" -eq 0 ] && echo "🎉 [push] ทุก TODO เสร็จหมดแล้ว!" >&2 && exit 0

echo "" >&2
echo "📋 [push] TODO ที่ยังค้าง ($COUNT items) — บอก Claude ว่าเสร็จอะไรแล้วเพื่อติ๊กถูก:" >&2
echo "$OPEN" | grep "\[dream\]" | sed 's/^- \[ \] /  🌟 /' >&2
echo "$OPEN" | grep -v "\[dream\]" | sed 's/^- \[ \] /  • /'  >&2
echo "   💡 ใช้: bash scripts/done.sh \"<ชื่อโปรเจ็ค>\" เพื่อติ๊กถูก+push อัตโนมัติ" >&2

exit 0
