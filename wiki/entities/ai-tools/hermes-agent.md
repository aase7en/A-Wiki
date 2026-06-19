---
type: entity
category: project
domain: ai-tools
tags: [ai-agent, cli, llm, telegram, discord, skills, cron, mcp, open-source]
sources: [hermes-agent-guide-th, agent-frameworks-local-debug-2026]
created: 2026-04-19
updated: 2026-05-02
---

# Hermes Agent

**ผู้พัฒนา**: NousResearch (open-source)  
**Repository**: github.com/NousResearch/hermes-agent  
**สถานะ**: Active — รองรับ Linux, macOS, WSL2, Android/Termux

## ภาพรวม

Hermes Agent คือ open-source AI agent framework ที่รันผ่าน CLI สามารถต่อกับ LLM หลาย provider พร้อมระบบ messaging gateway (Telegram, Discord, Slack ฯลฯ), skills, cron scheduler และ webhook รองรับ memory provider ภายนอกและ MCP server

## ติดตั้ง (Mac/Linux)

```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.zshrc
hermes
```

จัดการ Python 3.11, Node.js, ripgrep, ffmpeg ให้อัตโนมัติ

## คำสั่งเริ่มต้น

```bash
hermes model      # เพิ่ม provider / API key / เลือก default model
hermes doctor     # ตรวจสุขภาพระบบ
hermes status     # ดูสถานะ auth + platform
hermes            # เปิดแชต
```

## สถาปัตยกรรมหลัก

```
CLI / Messaging Gateway
        ↓
   Hermes Core (LLM)
   ├── Skills (/<name>)
   ├── Cron scheduler
   ├── Webhook listener
   ├── Memory provider (mem0, honcho ฯลฯ)
   └── MCP server / ACP (editor integration)
```

## Messaging Gateway

ต่อได้กับ: Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant

```bash
hermes gateway setup   # ตั้งค่าแบบ interactive
hermes gateway run     # รันแบบ foreground (แนะนำใน WSL/Docker/Termux)
hermes gateway start   # รันแบบ background service
```

## Skills System

```bash
hermes skills browse                    # ดู skills ที่มี
hermes skills install <skill>           # ติดตั้ง
hermes skills update                    # อัปเดตทั้งหมด
# เรียกใช้ใน chat: /<skill-name>
```

## Slash Commands ที่ใช้บ่อย

| Command | ความหมาย |
|---------|---------|
| `/new` | เริ่ม session ใหม่ |
| `/compress` | ย่อ context (ใช้เมื่อคุยนาน) |
| `/background` | รันงานเบื้องหลัง |
| `/plan` | ให้วางแผนก่อนลงมือ |
| `/usage` | ดู token/cost |
| `/retry` | ลองใหม่รอบล่าสุด |
| `/voice on` | เปิด voice mode |

## LLM Providers ที่รองรับ

- ChatGPT Plus, OpenRouter, **MiniMax** ($10/เดือน — แนะนำสำหรับผู้เริ่มต้น), Anthropic และอื่นๆ

## ข้อควรระวัง

- `hermes model` (shell) ≠ `/model` (slash) — อย่าสับสน
- Windows native ยังไม่รองรับ → ต้องใช้ WSL2
- `/q` ชนกับ `/quit` → ใช้ `/queue` พิมพ์เต็ม
- **ctx requirement สูง (จาก dev community 2026-05)**: system prompt + memory preload + skills metadata กิน token เยอะตั้งแต่ token แรก → ถ้ารัน local model ctx <16k อาจ "เปิดไม่ขึ้น" ใช้ Q4 quantized ได้แต่แนะนำ ctx 32k+ ดู [[concepts/ai-tools/agent-framework-tradeoffs]]

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/telegram-bot]] (Hermes ต่อ Telegram gateway → ควบคุม IoT ได้)
- คล้ายกัน: Claude Code (Anthropic — lean style), OpenClaw (orchestrator style)
- จัดอยู่ใน category: [[concepts/ai-tools/agent-framework-tradeoffs]] — Autonomous Specialist



## Raspberry Pi 5 (ARM64)

Hermes รันบน Raspberry Pi 5 ได้เต็มรูปแบบ (ARM64):

| รุ่น | RAM | เหมาะกับ |
|------|-----|---------|
| Pi 5 8GB | 8 GB | Telegram gateway, cron jobs, dashboard client |
| Pi 5 16GB | 16 GB | Full agent + Docker containers + PostgreSQL |

```bash
# ติดตั้งบน Pi 5
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes setup

# เชื่อมกับ A-Wiki
git clone <repo> ~/A-Wiki
hermes gateway setup  # เลือก Telegram
hermes gateway start  # รัน background
```

**ข้อแนะนำ**: ไม่ควร run local LLM บน Pi 5 — ใช้ API-based models (DeepSeek, Gemini Flash) ผ่าน OpenRouter แทน

**Docker compose**: ดู `docs/runbooks/hermes-raspberry-pi5.md`

**Performance**: Telegram gateway ~30MB RAM, Dashboard server ~50MB RAM, Cron jobs ~100MB peak

## แหล่งข้อมูล

- [[sources/hermes-agent-guide-th]] — คู่มือภาษาไทย, คำสั่งครบชุด
