---
type: source
title: "คู่มือ คำสั่งที่ใช้บ่อย น้องเฮอมีส Hermes Agent"
slug: hermes-agent-guide-th
date_ingested: 2026-04-19
original_file: raw/คู่มือ Hermes Agent.md
tags: [hermes, ai-agent, cli, telegram, discord, skills, cron, mcp]
domain: ai-tools
---

# คู่มือ Hermes Agent (ภาษาไทย)

**ประเภท**: article (คู่มือภาษาไทย)  
**ผู้เผยแพร่**: sanookai.com  
**ผู้พัฒนา**: NousResearch (open-source)

## ประเด็นหลัก

1. **Hermes Agent** คือ open-source AI agent CLI รันบน Mac/Linux/WSL2 รองรับหลาย LLM provider
2. **ติดตั้ง one-line**: `curl -fsSL .../install.sh | bash` — จัดการ Python 3.11, Node.js, ripgrep, ffmpeg ให้อัตโนมัติ
3. **Messaging gateway**: ต่อ Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant ได้
4. **Skills system**: ติดตั้ง/ถอด skill ได้ เรียกใช้ด้วย `/<skill-name>` ทั้งใน CLI และ messaging
5. **Cron + Webhook**: ตั้ง scheduled task และรับ event ภายนอกได้
6. **Memory providers**: รองรับ mem0, honcho, hindsight, holographic, retaindb, byterover, supermemory

## CLI Commands สำคัญ

| กลุ่ม | คำสั่งหลัก |
|-------|-----------|
| เริ่มใช้ | `hermes`, `hermes chat -q "..."`, `hermes -c` (continue), `hermes -r <session>` |
| ตั้งค่า | `hermes model`, `hermes setup`, `hermes tools`, `hermes config show/set` |
| Gateway | `hermes gateway setup`, `hermes gateway run/start/stop` |
| Sessions | `hermes sessions list/browse/export/rename` |
| Diagnostics | `hermes doctor [--fix]`, `hermes status --deep`, `hermes dump` |
| Skills | `hermes skills browse/install/update/audit` |
| Cron | `hermes cron list/create/edit/run` |
| Webhook | `hermes webhook subscribe/list/test` |
| Advanced | `hermes mcp list`, `hermes acp`, `hermes memory setup`, `hermes profile create` |

## Slash Commands สำคัญ (ในแชต)

```
/new        เริ่มบทสนทนาใหม่
/compress   ย่อ context เมื่อคุยนานมาก
/background รันงานแยกเบื้องหลัง
/plan       ให้เขียนแผนก่อนลงมือ
/usage      ดู token/cost/session duration
/retry      ให้ลองตอบรอบล่าสุดใหม่
/undo       ลบ exchange ล่าสุด
/voice on   เปิด voice mode
```

## ข้อสังเกตสำคัญ

- `hermes model` (shell) ≠ `/model` (slash command) — อันแรกเพิ่ม provider/API key, อันหลังสลับ model ระหว่าง session
- `/model` บางเวอร์ชันยังมีบั๊ก → ถ้าไม่ตอบสนองให้ใช้ `hermes model` จาก shell แทน
- `/q` ชนกับ `/quit` → ใช้ `/queue` แบบพิมพ์เต็มเสมอ
- Windows native ยังไม่รองรับ → ใช้ WSL2

## LLM Backend แนะนำ

- มี ChatGPT Plus → ใช้ได้เลย
- ไม่มี → แนะนำ **MiniMax** เริ่มต้น $10/เดือน (รองรับสร้างภาพ + เพลงด้วย)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/ai-tools/hermes-agent]] — สร้างใหม่
