---
type: source
title: "OpenRouter API demo and capabilities"
slug: openrouter-api-demo
date_ingested: 2026-05-10
original_file: scripts/openrouter-demo.py
tags: [openrouter, ai-tools, demo, api]
---

# OpenRouter API demo and capabilities

**ประเภท**: demo script / implementation note
**วันที่**: 2026-05-10
**ผู้เขียน**: Aase7en

## ประเด็นหลัก
1. OpenRouter เป็น unified API gateway ที่รองรับโมเดลหลายค่ายผ่าน endpoint เดียว
2. สามารถใช้ OpenAI-compatible request format กับ `https://openrouter.ai/api/v1`
3. มีทางเลือก `openrouter/auto` สำหรับ auto-routing และ `openrouter/free` สำหรับ free-model fallback
4. สาธิตการเรียก API แบบ command-line ด้วย Python script ที่อ่าน `OPENROUTER_API_KEY` จาก environment
5. มีเมธอด `--discover` เพื่อดึง free models จาก API และเลือกทดสอบอัตโนมัติ

## ข้อมูลที่น่าสนใจ
- สคริปต์ demo ใช้ `openrouter/auto`, `openrouter/free`, `openrouter/owl-alpha`, และ `openrouter/nemotron-3-nano-omni-30b-a3b-reasoning:free`
- วิธีใช้งานหลัก:
  - `OPENROUTER_API_KEY=sk-... python3 scripts/openrouter-demo.py`
  - `OPENROUTER_API_KEY=sk-... python3 scripts/openrouter-demo.py --discover --max-models 4`
- เน้นแนวทาง security: เก็บ API key ใน environment variable เท่านั้น

## ข้อเสนอแนะ
- ถ้าใช้ใน environment จริง ให้เก็บ key ไว้ใน secret manager หรือไฟล์ที่ไม่ commit
- สำหรับการนำไปผลิต ให้เพิ่ม retry/backoff และ validate response schema ก่อนใช้

## หน้า Wiki ที่ได้รับการอัปเดต
- [[concepts/ai-tools/openrouter-api]]
- [[index-ai-tools]]
