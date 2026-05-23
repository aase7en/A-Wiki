---
type: entity
category: project
tags: [telegram, bot, python, ollama, routing, home-server, mac-mini]
sources: [telegram-ai-router-design]
created: 2026-04-19
updated: 2026-04-19
---

# Telegram AI Router Bot

**ประเภท**: Personal AI Gateway Project  
**สถานะ**: 📐 Design Phase — code skeleton พร้อม

## ภาพรวม
Bot Telegram ส่วนตัวที่รันบน Mac Mini ที่บ้าน ทำหน้าที่เป็น gateway รับข้อความจากผู้ใช้แล้ว route ไปยัง AI model ที่เหมาะสมโดยอัตโนมัติ — local Ollama สำหรับ query ง่าย, Cloud API สำหรับงานซับซ้อน เพื่อประหยัด credit สูงสุด

## Architecture

```
[Telegram] ←→ [Python Bot] ←→ [Router]
                                  ↙        ↘
                          [Ollama]      [Cloud API]
                          local/free    Claude/Gemini
```

## Related patterns
- ใช้แนวคิดจาก [[concepts/ai-tools/local-llm-routing]] สำหรับการตัดสินใจ local ↔ cloud
- ถ้าต้องการเชื่อม Claude Code กับ OpenRouter ให้ดู [[concepts/ai-tools/openrouter-claude-code]]
- ถ้าใช้นโยบาย Gemini-first ให้ดู [[wiki/synthesis/dual-ai-workflow]]

## Code Skeleton

### โครงสร้างไฟล์
```
telegram-ai-router/
├── bot.py          ← จุดเริ่มต้น, รับ message จาก Telegram
├── router.py       ← classifier + model selector
├── llm.py          ← abstraction layer ส่งไป Ollama/API
├── config.py       ← API keys, model names, thresholds
└── requirements.txt
```

### `config.py`
```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CLAUDE_API_KEY = "YOUR_CLAUDE_KEY"
GEMINI_API_KEY = "YOUR_GEMINI_KEY"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"

# Routing thresholds
SHORT_QUERY_MAX_CHARS = 150
LONG_QUERY_MIN_CHARS = 500

WIKI_KEYWORDS = ["ingest", "wiki", "สรุป", "บันทึก", "lint", "อัปเดต wiki"]
COMPLEX_KEYWORDS = ["วิเคราะห์", "เปรียบเทียบ", "ออกแบบระบบ", "synthesis"]
```

### `router.py`
```python
from config import *

def classify(text: str) -> str:
    """Returns: 'local' | 'gemini' | 'claude'"""
    length = len(text)

    # งาน wiki → Gemini
    if any(kw in text.lower() for kw in WIKI_KEYWORDS):
        return "gemini"

    # query ซับซ้อน / ยาว → Claude
    if length > LONG_QUERY_MIN_CHARS:
        return "claude"
    if any(kw in text for kw in COMPLEX_KEYWORDS):
        return "claude"
    if "```" in text:  # มีโค้ด
        return "claude"

    # query สั้น ง่าย → Local
    if length < SHORT_QUERY_MAX_CHARS:
        return "local"

    return "gemini"  # default กลาง
```

### `llm.py`
```python
import httpx
import anthropic
import google.generativeai as genai
from config import *

async def ask_local(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=60)
    return r.json()["response"]

async def ask_gemini(prompt: str) -> str:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

async def ask_claude(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

async def ask(prompt: str, model: str) -> tuple[str, str]:
    """Returns (response_text, model_used)"""
    if model == "local":
        return await ask_local(prompt), f"🏠 Local ({OLLAMA_MODEL})"
    elif model == "gemini":
        return await ask_gemini(prompt), "✨ Gemini"
    else:
        return await ask_claude(prompt), "🧠 Claude"
```

### `bot.py`
```python
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from router import classify
from llm import ask

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("⏳ กำลังคิด...")

    model = classify(text)
    response, model_name = await ask(text, model)

    await update.message.reply_text(f"{response}\n\n_via {model_name}_", parse_mode="Markdown")

if __name__ == "__main__":
    from config import TELEGRAM_TOKEN
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()
```

### `requirements.txt`
```
python-telegram-bot==21.6
anthropic
google-generativeai
httpx
```

## วิธีติดตั้งบน Mac Mini

```bash
# 1. ติดตั้ง Ollama
brew install ollama
ollama pull qwen2.5:7b

# 2. Clone และรัน bot
pip install -r requirements.txt
python bot.py

# 3. รันตอนเปิดเครื่อง (optional)
# ใส่ใน launchd หรือ pm2
```

## Hardware แนะนำ

| รุ่น | RAM | ราคามือสอง | Model ที่รันได้ |
|-----|-----|-----------|--------------|
| Mac Mini M1 (2020) | 8 GB | ~10,000-12,000 ฿ | qwen2.5:7b (25-35 tok/s) |
| Mac Mini M2 (2023) | 8 GB | ~15,000-18,000 ฿ | qwen2.5:7b + เร็วกว่า M1 |
| Mac Mini M2 Pro | 16 GB | ~22,000-28,000 ฿ | qwen2.5:14b (12-18 tok/s) |
| Mac Mini M4 Pro | 48 GB | ~55,000+ ฿ | 32B models ลื่น |

> แนะนำ: **M2 8GB มือสอง** — cost/performance ดีที่สุดสำหรับ use case นี้  
> กฎ 60%: weights ต้องใช้ RAM ไม่เกิน 60% เสมอ (เหลือให้ KV Cache + macOS)

## ความสัมพันธ์
- ใช้แนวคิด: [[concepts/ai-tools/local-llm-routing]]
- เกี่ยวข้องกับ: [[entities/ai-tools/hermes-agent]] — Hermes ทำสิ่งคล้ายกันแต่ซับซ้อนกว่า
- เกี่ยวข้องกับ: [[entities/ai-tools/ollama]]

## แหล่งข้อมูล
- [[sources/telegram-ai-router-design]] — ออกแบบเอง 2026-04-19
