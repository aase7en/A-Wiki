---
type: entity
category: software
tags: [llm, local-ai, inference-server, ollama, mac-mini, raspberry-pi, gguf]
sources: [local-llm-mac-mini-guide, ollama-pi5]
created: 2026-05-21
updated: 2026-05-21
---

# Ollama

## ภาพรวม

Ollama เป็น runtime สำหรับรัน LLM แบบ local บนเครื่องตัวเอง — แพ็ค model weights + quantization (GGUF) + inference engine + HTTP API (`/api/generate`, `/api/chat`) ไว้ใน binary เดียว ติดตั้งง่ายข้าม OS (macOS, Linux, Windows) เป็นทางเลือก default-friendly สำหรับใครที่ไม่อยาก setup llama.cpp / vLLM เอง

## คุณสมบัติหลัก

- **One-line install**: `brew install ollama` (macOS) หรือ `curl -fsSL https://ollama.com/install.sh | sh` (Linux)
- **Model pull จาก registry**: `ollama pull qwen2.5:7b`, `ollama pull llama3.2`, ฯลฯ
- **HTTP API บน :11434**: เข้ากันได้กับ OpenAI-compatible client ผ่าน proxy
- **Auto-quantization tier**: เลือก Q4/Q5/Q8 ตาม VRAM/RAM ที่มี
- **GPU acceleration**: รองรับ Apple MPS (Metal), CUDA, ROCm
- **Modelfile**: customize system prompt + parameters คล้าย Dockerfile

## การใช้งานใน wiki นี้

- **Mac mini M4 local stack** — รัน 7B/13B models พร้อมกับ Telegram bot (ดู [[entities/ai-tools/telegram-ai-router]])
- **Raspberry Pi 5** — รัน 1.5B–3B models สำหรับ edge inference (ดู source [[sources/ollama-pi5]])
- **Routing target** — เป็น "Level 0 free local" ใน cost-first pyramid สำหรับงานที่ไม่ต้อง cloud (ดู [[concepts/ai-tools/local-llm-routing]])

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ติดตั้ง 1 บรรทัด ใช้ได้เลย | เร็วช้ากว่า vLLM/llama.cpp tuned เอง |
| HTTP API stable | ไม่รองรับ batching ระดับ production |
| Registry pull ง่าย | model ใหญ่ (70B+) ต้อง RAM/VRAM มาก |
| Cross-platform | ไม่มี fine-tuning ในตัว |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/telegram-ai-router]] — Telegram bot ใช้ Ollama เป็น backend
- ใช้ร่วมกับ: [[concepts/ai-tools/local-llm-routing]] — routing logic เลือก model
- เกี่ยวข้องกับ: [[entities/ai-tools/hermes-agent]] — agent framework ทางเลือก
- เปรียบเทียบกับ: cloud LLM (OpenRouter, Anthropic API) — trade-off cost vs latency vs privacy

## แหล่งข้อมูล

- [[sources/local-llm-mac-mini-guide]] — Mac mini M4 + Ollama + MLX setup
- [[sources/ollama-pi5]] — Pi 5 benchmark + tutorial links
