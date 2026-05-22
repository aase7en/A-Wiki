---
type: source
title: "Local LLM on Mac Mini — In-depth Guide (2025-2026)"
slug: local-llm-mac-mini-guide
date_ingested: 2026-04-20
original_file: raw/web-local-llm-mac-mini-2026-04-19.md
source_type: gemini-knowledge
url: null
tags: [local-llm, mac-mini, ollama, mlx, apple-silicon, quantization]
---

# Local LLM on Mac Mini — In-depth Guide

**ประเภท**: Gemini knowledge synthesis (ไม่มี URL — verify ตัวเลขก่อนใช้จริง)  
**วันที่**: 2026-04-19  
**ผู้เขียน**: Gemini CLI

## ประเด็นหลัก

1. **60% Rule** — weights ของ model ควรใช้ RAM ไม่เกิน 60% เพื่อเหลือให้ KV Cache + macOS
2. **M4 Pro เป็นจุดคุ้มค่าใหม่** — 273 GB/s bandwidth รัน 14B-32B ได้ลื่น 12-18 tokens/sec
3. **Ollama + MLX backend** — ให้ประสิทธิภาพสูงสุดบน Apple Silicon ในปี 2026
4. **Exo Clustering** — รวม RAM จาก Mac หลายเครื่องรัน model 70B+ ได้
5. **oMLX SSD Caching** — ข้ามขีดจำกัด RAM โดย offload KV Cache ลง SSD (ระวังอายุ SSD)

## Performance Tiers (Q4 Quantization)

| Model Size | RAM ที่ต้องการ | ความเร็ว (tokens/sec) |
|-----------|--------------|----------------------|
| 7B-8B | 16GB+ (M4) | 25-35 |
| 14B-32B | 48GB+ (M4 Pro) | 12-18 |
| 70B+ | 64GB+ หรือ Exo cluster | <10 |

## Software Stack

| เครื่องมือ | ใช้ทำอะไร |
|----------|---------|
| Ollama (MLX backend) | รัน model ง่ายสุด, API compatible |
| oMLX | SSD caching สำหรับ context ยาว |
| Exo | Cluster Mac หลายเครื่องรัน model ใหญ่ |

## Optimization สำคัญ
- ใช้ **Q4_K_M หรือ Q5_K_M** (GGUF) — จุดสมดุล speed vs quality
- เปิด **Flash Attention** ลด memory ใช้กับ context ยาว
- ตั้ง `keepAlive: 3600` ใน Ollama ป้องกัน model unload

## หน้า Wiki ที่ได้รับการอัปเดต
- [[entities/ai-tools/ollama]]
- [[entities/ai-tools/telegram-ai-router]] — เพิ่ม model tier table
