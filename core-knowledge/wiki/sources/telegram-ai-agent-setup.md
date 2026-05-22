---
type: source
title: "Telegram AI Agent — Claude API / OpenRouter / Ollama"
slug: telegram-ai-agent-setup
date_ingested: 2026-04-20
original_file: web-search
tags: [telegram, claude-api, openrouter, ollama, ai-agent, python]
quality: ⚠️ web-search
---

# Telegram AI Agent Setup

**ประเภท**: tutorial / framework comparison  
**แหล่ง**: openrouter.ai, github.com, openclawapi.org  
**เกี่ยวข้องกับ**: Pi 5, Claude API, Hermes Agent

## ประเด็นหลัก

1. มีหลาย framework ที่ใช้ได้: Nanobot, NClaw, Hermes Agent, custom Python
2. OpenRouter รองรับ Claude API format ตรงๆ — เปลี่ยน base URL แค่บรรทัดเดียว
3. `claude-code-telegram` — ให้ access Claude Code จาก Telegram ได้เลย
4. Pi 5 รัน Telegram bot ด้วย RAM แค่ ~100MB — เบามาก

## ตัวเลือก Framework

| Framework | RAM | ความยืดหยุ่น | เหมาะกับ |
|-----------|-----|------------|---------|
| **Hermes Agent** | ~150MB | สูง (skills, cron) | ✅ แนะนำ — มีใน wiki แล้ว |
| **Nanobot** | ~100MB | ปานกลาง | ✅ เริ่มต้นง่าย |
| **NClaw** | ~200MB | สูง (580+ models) | ✅ หลาย provider |
| **custom Python** | ~80MB | สูงสุด | ⚠️ เขียนเองทุกอย่าง |

## OpenRouter — เปลี่ยน 1 บรรทัด ใช้ Claude API ได้

```python
import anthropic

client = anthropic.Anthropic(
    api_key="sk-or-...",           # OpenRouter key
    base_url="https://openrouter.ai/api/v1"  # ← แค่นี้
)
# ใช้ได้เหมือน Claude API ทุกอย่าง รองรับ thinking, tool use
```

## Model Routing (ประหยัด cost)

```
Telegram message → classify complexity
  ├── Simple (FAQ, status) → Ollama local (ฟรี, 3-5 tok/s)
  ├── Medium (analysis)    → Gemini Flash (ถูก)
  └── Complex (coding)     → Claude Sonnet (แม่นยำ)
```

> ตรงกับ `local-llm-routing` concept ที่มีใน wiki แล้ว

## Hermes Agent บน Pi 5

```bash
# ติดตั้งผ่าน Docker
docker run -d hermes-agent \
  --telegram-token YOUR_TOKEN \
  --provider openrouter \
  --model claude-sonnet-4-6
```

## แหล่งอ้างอิง

- [OpenRouter Docs](https://openrouter.ai/docs)
- [claude-code-telegram GitHub](https://github.com/RichardAtCT/claude-code-telegram)
- [Hermes Agent — Openclaw](https://openclawapi.org/en/blog/2026-04-01-hermes-agent-full-platform-deploy)
- [Nanobot GitHub](https://github.com/HKUDS/nanobot)

## หน้า Wiki ที่เกี่ยวข้อง

- [[entities/ai-tools/hermes-agent]]
- [[concepts/ai-tools/local-llm-routing]]
- [[entities/iot/raspberry-pi]]
