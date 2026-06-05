---
type: concept
title: Multi-Agent Failover System
tags: [ai-tools, multi-agent, failover, rate-limit, workflow]
sources: []
created: 2026-05-16
updated: 2026-06-05
last_verified: 2026-06-05
verify_tool: wiki
---

# Multi-Agent Failover System

> TL;DR: A-Wiki มีระบบ failover ข้าม agent อยู่แล้วผ่าน `scripts/swarm/agent-switch.sh` และ local `handoff.md`; กฎกลางล่าสุดคือ `docs/protocols/cross-agent-plan-handoff.md` ให้ทุก Plan Mode แตกงานเป็น chunk เล็กพร้อม resume point ก่อนชน limit หรือสลับ IDE/Agent. [wiki]

## นิยาม

ระบบสลับ agent อัตโนมัติเมื่อ Claude Code Sonnet ชน rate limit (5hr rolling หรือ daily limit) โดยไม่สูญเสีย context งาน — ทุก agent อ่าน `handoff.md` เป็นอันดับแรก และใช้ wiki schema เดียวกัน

ตั้งแต่ 2026-06-05 กฎนี้ถูกขยายจาก "failover เมื่อชน limit" เป็น "cross-agent plan handoff" สำหรับทุก agent: Codex, Claude Code, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Antigravity, Ollama/Hermes-style local agents และ agent อื่นในอนาคต. [wiki]

## ทำไมถึงสำคัญ

Claude Code มี limit 2 ชั้น:
- **5-hour rolling limit** — รีเซ็ตทุก 5 ชั่วโมง (Claude Max plan)
- **Daily limit** — รีเซ็ตเที่ยงคืน UTC

เมื่อชน limit งาน wiki หยุดทันที ถ้าไม่มี failover plan = ต้องรอ ซึ่งอาจใช้เวลา 1-5 ชั่วโมง

## Agent Comparison Matrix

| Agent | Hooks | Edit/Write | Bash | Web Search | Rate Limit | ใช้กับงาน | Setup File |
|-------|-------|-----------|------|-----------|-----------|-----------|-----------|
| **Claude Code Desktop** | ✅ ครบ 6 hooks | ✅ Native | ✅ Full | MCP/WebFetch | 5hr + daily | Main: write wiki, schema, reasoning | `CLAUDE.md` |
| **Terminal (claude CLI)** | ✅ same pool | ✅ Native | ✅ Full | MCP/WebFetch | same pool | เหมือน Desktop: scripting | `CLAUDE.md` |
| **OpenRouter engine-swap** ⭐ | ✅ **hooks ครบ!** | ✅ Native | ✅ Full | MCP/WebFetch | ฟรี/ถูกมาก | **Seamless สุด** — Claude Code UI เดิม เปลี่ยนแค่ model | `.env` / shell fn |
| **Codex Desktop** | .codex/hooks.json | ✅ Sandbox | ✅ Limited | WebSearch limited | OpenAI (separate) | Code tasks, fallback | `.codex/AGENTS.md` |
| **VS Code (Cline/Copilot)** | ❌ ไม่มี | ✅ UI only | ❌ | extension-dep | per-extension | File editing only | `.vscode/AGENTS.md` |
| **Gemini CLI** | GEMINI.md | ❌ Text only | ✅ Yes | ✅ Built-in Google | 60rpm free | Web search, lookup, bridge | `GEMINI.md` |
| **Google AI Studio** | ❌ ไม่มี | ❌ Paste only | ❌ | ✅ Google Grounding | Generous free | Long-context synthesis, Q&A | `AISTUDIO.md` |

## วิธีใช้งานแต่ละ Agent

### 1. OpenRouter Engine-Swap (แนะนำ ⭐)

**Seamless ที่สุด** — เปลี่ยนแค่ model ที่ Claude Code ใช้ hooks ยังทำงานครบ

```bash
# วิธีที่ 1: shell function (ตั้งไว้ใน .zshrc)
wiki-qwen          # Qwen Coder ฟรี 200 req/day
claude-router      # Auto-select free model

# วิธีที่ 2: env vars ตรง
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
export ANTHROPIC_MODEL="deepseek/deepseek-chat"
claude             # เปิด Claude Code ปกติ
```

**Free models ที่แนะนำ** (ผ่าน OpenRouter):

| Model | ค่าใช้จ่าย | เหมาะกับ |
|-------|-----------|--------|
| `deepseek/deepseek-chat` | ถูกมาก (~$0.14/M) | reasoning, wiki writing, code |
| `meta-llama/llama-3.3-70b-instruct:free` | ฟรี | lookup, summarize |
| `qwen/qwen-2.5-72b-instruct:free` | ฟรี | multilingual Thai+English |
| `deepseek/deepseek-r1:free` | ฟรี | reasoning เบา |

**ข้อจำกัด**: model อ่อนกว่า Claude Sonnet — งาน schema ซับซ้อนหรือ reasoning ลึกอาจเพี้ยน

---

### 2. Gemini CLI

**เหมาะสุดสำหรับ**: web research, ราคา hardware, version ล่าสุด

```bash
gemini             # เปิด interactive session
gemini -p "สรุปหน้า wiki นี้: [paste content]"
```

อ่าน `GEMINI.md` สำหรับ full instructions + trigger phrases

---

### 3. Codex Desktop (OpenAI)

**เหมาะสุดสำหรับ**: code tasks, script generation — limit แยกจาก Claude

```
เปิดแอป Codex Desktop
อ่าน AGENTS.md → CLAUDE.md → .codex/AGENTS.md
อ่าน handoff.md → ดูว่างานค้างอยู่ตรงไหน
```

---

### 4. Google AI Studio

**เหมาะสุดสำหรับ**: synthesis ยาว, cross-domain analysis ที่ไม่ต้อง write file

```
1. เปิด aistudio.google.com
2. เลือก Gemini 2.5 Pro
3. Paste section "Context for AI Studio" จาก handoff.md
4. เริ่มงานได้เลย
```

Output → copy กลับมาให้ Claude apply ผ่าน terminal/Claude Code

---

### 5. VS Code + Cline

**เหมาะสุดสำหรับ**: file editing เมื่อไม่มี agent อื่น เช่นงาน format, เพิ่ม frontmatter

```
install Cline extension → ใส่ Claude API key (แยกจาก Claude Code limit)
อ่าน .vscode/AGENTS.md
ไม่มี hooks → ระวัง raw/ และ CLAUDE.md ด้วยตัวเอง
```

---

## Failover Protocol (ขั้นตอน)

กฎละเอียดปัจจุบันอยู่ที่ `docs/protocols/cross-agent-plan-handoff.md`: ทุก Plan Mode / multi-step plan ต้องแตกเป็น chunk มี ID, status, files, verify command, และ handoff note แล้ว checkpoint ลง local `handoff.md`. [wiki]

### เมื่อ Claude ชน limit

```
Claude แสดง "Usage limit reached" หรือหยุดตอบ
  ↓
รัน: bash scripts/agent-switch.sh
  ↓
handoff.md อัปเดต → ดู "Agent Recommendation"
  ↓
เปิด agent ที่แนะนำ → อ่าน handoff.md เป็นอันดับแรก
  ↓
ทำงานต่อ → เพิ่ม entry ใน handoff.md Historical Log เมื่อเสร็จ
  ↓
เมื่อ Claude กลับมา → เปิด Claude Code → อ่าน handoff.md → ต่องาน
```

### ลำดับสลับ (Failover Order)

```
Claude Code Sonnet (หลัก)
  → wiki-qwen / claude-router  (OpenRouter ⭐ — seamless, hooks ครบ)
  → gemini                     (Gemini CLI — web search ดีสุด)
  → Codex Desktop              (OpenAI limit ต่างกัน)
  → Google AI Studio           (synthesis ยาว, paste context)
  → VS Code + Cline            (file editing only)
  → [รอ Claude กลับมา]        (reset ทุก 5hr หรือ midnight UTC)
```

---

## Auto-Export System

### 3 ชั้นของ State Sync

**ชั้น 1: PostToolUse Hook** (อัตโนมัติ, debounced 60s)
- ทุกครั้งที่ Claude แก้ไขไฟล์ → `handoff.md` อัปเดต uncommitted changes
- ถ้า Claude หยุดกะทันหัน state ล่าสุดยังอยู่ใน handoff.md

**ชั้น 2: Stop Hook** (อัตโนมัติเมื่อ session จบ)
- Claude Code exit → รัน `scripts/agent-switch.sh stop`
- Full export: task type + recommendation + pending TODOs + uncommitted

**ชั้น 3: Manual Trigger**
```bash
bash scripts/agent-switch.sh        # full export, interactive output
bash scripts/agent-switch.sh stop   # same (Stop hook ใช้ command นี้)
bash scripts/agent-switch.sh quick  # lightweight (PostToolUse ใช้ command นี้)
```

---

## Cost Impact

| Action | Cost |
|--------|------|
| PostToolUse hook (handoff-auto-export.sh) | 0 tokens — pure bash |
| Stop hook (agent-switch.sh) | 0 tokens — pure bash + python3 |
| handoff.md update | ~2KB disk write |
| OpenRouter engine-swap (free model) | ฟรี (quota เป็นแต่ละ model) |
| OpenRouter engine-swap (DeepSeek) | ~$0.14/M tokens ≈ 100x ถูกกว่า Claude Sonnet |

---

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[openrouter-claude-code]] — shell functions สำหรับ engine-swap
- เกี่ยวข้องกับ: [[agent-framework-tradeoffs]] — เปรียบเทียบ agent styles
- เกี่ยวข้องกับ: [[context-management]] — /compact ก่อน handoff ลด context ที่ส่งต่อ
- เกี่ยวข้องกับ: [[local-llm-routing]] — routing pattern ที่คล้ายกัน

## แหล่งข้อมูล

- [design session 2026-05-16] — วางระบบ multi-agent failover สำหรับ InW-Wiki
