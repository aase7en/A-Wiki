---
name: a-wiki-telegram
description: "A-Wiki Telegram integration — wiki search, lifecycle commands, backup via Telegram bot"
version: 1.0.0
author: A-Wiki + Hermes
tags: [awiki, telegram, bot, wiki-search]
---

# A-Wiki Telegram — Bot Integration

ทำให้ Hermes บน Pi5 ตอบคำถามผ่าน Telegram ด้วย A-Wiki brain

## Auto-Load Rule

โหลดอัตโนมัติเมื่อ source=telegram — Hermes อ่าน skill นี้ทุกครั้งที่มีข้อความเข้าจาก Telegram

## Commands Available via Telegram

| Command | Action |
|---------|--------|
| `/wiki <query>` | ค้น A-Wiki FTS5 → สรุป + sources |
| `/search <query>` | Web search + wiki cross-ref |
| `/backup` | Backup sessions now |
| `/status` | System health check |
| `/spec` | Write specification |
| `/plan` | Break down into tasks |

## Setup

1. สร้าง bot กับ @BotFather → ได้ `TELEGRAM_BOT_TOKEN`
2. เพิ่ม token ใน `.env` ของ Pi5 container
3. `hermes gateway setup` → enable Telegram
4. `hermes gateway status` → verify connected

## Pi5 Docker Commands

```bash
# Add token
echo "TELEGRAM_BOT_TOKEN=YOUR_TOKEN" | sudo -S -p '' docker exec -i hermes-agent_web_1 tee -a /opt/data/profiles/tech_and_ai_architect/.env

# Setup gateway
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes -p tech_and_ai_architect gateway setup

# Verify
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes -p tech_and_ai_architect gateway status
```
