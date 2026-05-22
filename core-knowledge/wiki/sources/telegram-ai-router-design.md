---
type: source
title: "Telegram AI Router — Home Server Design"
slug: telegram-ai-router-design
date_ingested: 2026-04-19
original_file: null
tags: [telegram, ollama, routing, home-server, mac-mini, python]
---

# Telegram AI Router — Home Server Design

**ประเภท**: Original Design (ออกแบบเอง)  
**วันที่**: 2026-04-19  
**ผู้เขียน**: User + Claude (wiki session)

## ประเด็นหลัก

1. **ปัญหาที่แก้**: ลดการพึ่งพา Claude API เพียงอย่างเดียว โดยใช้ local LLM (Ollama) สำหรับ query ง่ายๆ ~70% ของการใช้งาน
2. **Auto routing**: classifier ง่ายๆ ใน Python ตัดสินใจว่าจะส่ง query ไปที่ local/Gemini/Claude โดยไม่ต้องให้ผู้ใช้เลือกเอง
3. **Interface**: Telegram Bot — ใช้งานได้ทุกที่ ไม่ต้องเปิด terminal
4. **Hardware**: Mac Mini M1/M2 มือสอง เปิดไว้ที่บ้านเป็น home AI server

## Stack ที่เลือก
- **python-telegram-bot** — library ที่ง่ายที่สุดสำหรับ Telegram bot
- **Ollama** — รัน local model บน Mac โดยไม่ต้องตั้งค่าซับซ้อน
- **httpx** — async HTTP client สำหรับเรียก Ollama API
- **anthropic + google-generativeai** — official SDK ทั้งคู่

## Routing Logic
- Short + ไม่มีโค้ด → Ollama local (ฟรี)
- มี keyword งาน wiki → Gemini (ถูก)
- ยาว / มีโค้ด / synthesis → Claude (คุณภาพสูงสุด)

## หน้า Wiki ที่ได้รับการอัปเดต
- [[entities/ai-tools/telegram-ai-router]] — entity page พร้อม full code skeleton
- [[concepts/ai-tools/local-llm-routing]] — concept อธิบาย routing pattern
