---
type: source
title: "Ollama Local LLM on Raspberry Pi 5"
slug: ollama-pi5
date_ingested: 2026-04-20
original_file: web-search
tags: [ollama, local-llm, raspberry-pi, arm64, ai]
quality: ⚠️ web-search
---

# Ollama Local LLM บน Raspberry Pi 5

**ประเภท**: tutorial / benchmark  
**แหล่ง**: stratosphereips.org, raspberry.tips, picocluster.com  
**เกี่ยวข้องกับ**: Pi 5, local AI, Telegram agent

## ประเด็นหลัก

1. Ollama รองรับ ARM64 ติดตั้งอัตโนมัติผ่าน install script
2. Pi 5 8GB **จำเป็นสำหรับ 7B models** — 4GB จะ swap หนักจนใช้ไม่ได้
3. NVMe SSD โหลด model เร็วกว่า microSD **3-5 เท่า**
4. Pi 5 เร็วกว่า Pi 4 ในการ inference **2-3 เท่า**
5. ต้องตั้ง `OLLAMA_CONTEXT_LENGTH` เอง (default 4096 กิน RAM มากเกิน)

## Performance บน Pi 5 (8GB)

| Model | RAM ใช้ | Token/s | ใช้งานได้? |
|-------|--------|---------|-----------|
| `gemma3:1b` | ~0.8GB | ~10 t/s | ✅ เร็วที่สุด |
| `llama3.2:1b` | ~1GB | ~8 t/s | ✅ ดี |
| `llama3.2:3b` | ~2GB | ~5 t/s | ✅ สมดุล |
| `phi3:mini (3.8B)` | ~2.5GB | ~4 t/s | ✅ ดี |
| `mistral:7b` | ~4.5GB | ~2 t/s | ⚠️ ช้า แต่รันได้ |
| `llama3.1:8b` | ~6GB | ~1 t/s | ❌ ช้าเกินใช้ |

> Pi 5 8GB: รัน mistral:7b ได้ แต่ 2 tok/s = ช้าสำหรับ real-time chat  
> แนะนำ `llama3.2:3b` หรือ `gemma3:1b` สำหรับ Telegram bot

## การติดตั้ง

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

## การตั้งค่า Context Length (ประหยัด RAM)

```bash
# ใน Modelfile หรือ environment
OLLAMA_CONTEXT_LENGTH=2048  # ลดจาก 4096 ประหยัด RAM ~30%
```

## NVMe Load Time เทียบ

| Storage | โหลด llama3.2:3b |
|---------|----------------|
| microSD | ~15 วินาที |
| NVMe SSD | ~4 วินาที ✅ |

> Pi 5 ของเจ้านายใช้ M.2 NVMe 2TB → โหลดเร็วที่สุด

## แหล่งอ้างอิง

- [Ollama on Pi 5 — Stratosphere Lab](https://www.stratosphereips.org/blog/2025/6/5/how-well-do-llms-perform-on-a-raspberry-pi-5)
- [Ollama Pi 5 Tutorial — PicoCluster](https://www.picocluster.com/blogs/picocluster-software-engineering/run-ollama-local-ai-chat-raspberry-pi-5)
- [Ollama Pi 5 — raspberry.tips](https://raspberry.tips/en/raspberrypi-tutorials/ollama-raspberry-pi-5)

## หน้า Wiki ที่เกี่ยวข้อง

- [[entities/iot/raspberry-pi]]
- [[concepts/ai-tools/local-llm-routing]]
