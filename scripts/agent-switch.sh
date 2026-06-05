#!/usr/bin/env bash
# scripts/agent-switch.sh — Export session state to handoff.md for multi-agent failover
#
# Usage:
#   bash scripts/agent-switch.sh          # full export (manual trigger / Stop hook)
#   bash scripts/agent-switch.sh stop     # same as above (Stop hook)
#   bash scripts/agent-switch.sh quick    # lightweight: update only uncommitted section
#
# Exit: 0=ok, 1=error writing handoff.md
#
# This script rewrites the section between HANDOFF-AUTO-START and HANDOFF-AUTO-END sentinels.
# Everything outside those sentinels (historical log) is preserved.

set -euo pipefail

MODE="${1:-full}"
HANDOFF="handoff.md"
HANDOFF_TEMPLATE="handoff.md.example"
DATE=$(date "+%Y-%m-%d %H:%M")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/personal_paths.sh
. "$REPO_ROOT/scripts/lib/personal_paths.sh"
LOG_FILE="$(awiki_log_path "$REPO_ROOT" || true)"
SESSION_FILE="$(awiki_session_memory_path "$REPO_ROOT" || true)"

# ---- Gather state ----

UNCOMMITTED=$(git status --short 2>/dev/null || echo "(git unavailable)")
[ -z "$UNCOMMITTED" ] && UNCOMMITTED="(clean — nothing uncommitted)"

LAST_LOG=$(grep "^## \[" "$LOG_FILE" 2>/dev/null | head -1 | sed 's/^## //' || echo "(none)")

# Extract open TODOs from "## 🔥 Active TODOs" block (mirror show-active-todos.sh)
PENDING=$(awk '
  /^## 🔥 Active TODOs/ { flag=1; next }
  /^## / { if (flag) exit }
  { if (flag) print }
' "$SESSION_FILE" 2>/dev/null \
  | grep -E '^[[:space:]]*-[[:space:]]*\[[[:space:]]\]' \
  | sed -E 's/^[[:space:]]*-[[:space:]]*\[[[:space:]]\][[:space:]]*/  • /' || echo "")
[ -z "$PENDING" ] && PENDING="  • (ไม่มี TODO ค้าง)"

# Extract latest session narrative from "## 🗓️ Recent" (first ### [date] block)
LAST_BRIEF=$(awk '
  /^## 🗓️ Recent/ { recent=1; next }
  recent && /^### \[/ { if (in_block) exit; in_block=1; print; next }
  in_block && /^### \[/ { exit }
  in_block && /^## / { exit }
  in_block { print }
' "$SESSION_FILE" 2>/dev/null || true)
[ -z "$LAST_BRIEF" ] && LAST_BRIEF="(ไม่มี narrative — session-memory.md ยังไม่มี ## 🗓️ Recent block)"

# ---- Determine task type & agent recommendation ----

CONTEXT="$LAST_LOG $PENDING"
if echo "$CONTEXT" | grep -qiE "search|web|ราคา|version|ล่าสุด|lookup|ค้น"; then
  TASK_TYPE="web-search"
  RECOMMEND="**Gemini CLI** — \`gemini\` (built-in Google search, ดีที่สุดสำหรับงานนี้)"
  RECOMMEND2="Google AI Studio — paste 'Context for AI Studio' section ด้านล่าง"
elif echo "$CONTEXT" | grep -qiE "code|script|bash|python|debug|fix"; then
  TASK_TYPE="code"
  RECOMMEND="**claude-qwen** — \`wiki-qwen\` (hooks ครบ, Qwen Coder แทน Sonnet) ⭐"
  RECOMMEND2="Codex Desktop — OpenAI limits ต่างกัน"
elif echo "$CONTEXT" | grep -qiE "wiki|ingest|synthesis|เขียน|entity|concept"; then
  TASK_TYPE="wiki-write"
  RECOMMEND="**claude-qwen** — \`wiki-qwen\` หรือ \`claude-router\` (OpenRouter, hooks ครบ) ⭐"
  RECOMMEND2="Gemini CLI — \`gemini\` ถ้าต้องการ web research ก่อน"
else
  TASK_TYPE="general"
  RECOMMEND="**claude-qwen** — \`wiki-qwen\` (OpenRouter DeepSeek, default fallback) ⭐"
  RECOMMEND2="Gemini CLI — \`gemini\` สำหรับงาน lookup/search"
fi

# ---- Build auto-export section ----

AUTO_SECTION="<!-- HANDOFF-AUTO-START — managed by scripts/agent-switch.sh, DO NOT EDIT MANUALLY -->

## 🔄 Current Handoff State

**Exported**: ${DATE} | **Branch**: ${BRANCH} | **Triggered by**: ${MODE}

### Task Context
**Type**: ${TASK_TYPE}
**Last log entry**: ${LAST_LOG}

### Uncommitted Changes
\`\`\`
${UNCOMMITTED}
\`\`\`

### Pending TODO (from session-memory.md)
${PENDING}

### 📨 Last Session Brief
*(narrative ล่าสุดจาก session-memory.md — context สำหรับ agent ตัวต่อไป)*

${LAST_BRIEF}

### Agent Recommendation
**Primary**: ${RECOMMEND}
**Alternative**: ${RECOMMEND2}

**Failover order (เมื่อ Claude Sonnet ชน limit):**
| Priority | Agent | วิธีเปิด | Hooks | ใช้กับ |
|----------|-------|---------|-------|-------|
| 1 ⭐ | OpenRouter engine-swap | \`wiki-qwen\` หรือ \`claude-router\` | ✅ ครบ | งาน wiki ทั่วไป |
| 2 | Gemini CLI | \`gemini\` | GEMINI.md | web search, lookup |
| 3 | Codex Desktop | เปิดแอป | .codex/AGENTS.md | code tasks |
| 4 | Google AI Studio | paste ด้านล่าง | ❌ | synthesis ยาว |
| 5 | VS Code + Cline | extension | ❌ | file editing only |

### Context for AI Studio
*(Paste ทั้งก้อนนี้เข้า aistudio.google.com เพื่อเริ่ม session)*

\`\`\`
You are a wiki agent for A-Wiki.
Domains: IoT, Environmental Health, AI Tools, Pharmacy.
Rules: wiki/ files only (kebab-case .md), Thai to user, no raw/ edits.
Current task type: ${TASK_TYPE}
Last action: ${LAST_LOG}

Pending TODOs:
${PENDING}

Last session narrative (what was done / open / decisions):
${LAST_BRIEF}

Uncommitted files:
${UNCOMMITTED}

Constraint: you cannot write files — provide markdown content for user to apply via Claude or terminal.
When done: summarize what you suggested so Claude can pick up seamlessly.
\`\`\`

<!-- HANDOFF-AUTO-END -->"

# ---- Rewrite handoff.md (preserve everything outside sentinels) ----

if [ ! -f "$HANDOFF" ]; then
  if [ -f "$HANDOFF_TEMPLATE" ]; then
    cp "$HANDOFF_TEMPLATE" "$HANDOFF"
  else
    echo "[agent-switch] ERROR: $HANDOFF not found and $HANDOFF_TEMPLATE is missing" >&2
    exit 1
  fi
fi

# Use python3 for reliable sentinel replacement (awk can choke on special chars)
python3 - "$HANDOFF" "$AUTO_SECTION" <<'PY'
import sys, re

path = sys.argv[1]
new_section = sys.argv[2]

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"<!-- HANDOFF-AUTO-START.*?<!-- HANDOFF-AUTO-END -->"
replacement = new_section
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    # Sentinels not found — prepend the section
    new_content = new_section + "\n\n" + content

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)
PY

echo "[agent-switch] handoff.md updated (mode: ${MODE}, task: ${TASK_TYPE})" >&2
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Agent Handoff Ready — ${DATE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Task type : ${TASK_TYPE}"
echo "  Recommend : $(echo "$RECOMMEND" | sed 's/\*\*//g')"
echo "  Branch    : ${BRANCH}"
echo ""
echo "  Uncommitted: $(echo "$UNCOMMITTED" | wc -l | tr -d ' ') file(s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  handoff.md updated — open next agent and read it"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
