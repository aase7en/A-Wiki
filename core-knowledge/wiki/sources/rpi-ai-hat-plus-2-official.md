---
type: source
title: "Raspberry Pi AI HAT+ 2 — Official Announcement"
slug: rpi-ai-hat-plus-2-official
date_ingested: 2026-04-20
original_file: raw/Introducing the Raspberry Pi AI HAT+ 2 Generative AI on Raspberry Pi 5.md
source_type: web
url: https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/
tags: [raspberry-pi, ai-hat, hailo, local-llm, edge-ai, npu]
---

# Raspberry Pi AI HAT+ 2 — Official Announcement

**ประเภท**: Official announcement (raspberrypi.com)
**วันที่เผยแพร่**: 2026-01-15
**ผู้เขียน**: Naush Patuck (Raspberry Pi)

## ประเด็นหลัก

1. **Hailo-10H NPU** — 40 TOPS (INT4), ออกแบบมาสำหรับ Generative AI โดยเฉพาะ
2. **8GB on-board RAM** แยกออกจาก Pi — model weights อยู่บน HAT ไม่กิน RAM ของ Pi
3. **ราคา $130** — วางขายแล้ว
4. **LLM ที่รองรับ ณ วันเปิดตัว**: Qwen2, Qwen2.5-Instruct, Qwen2.5-Coder, Llama3.2, DeepSeek-R1-Distill — ทั้งหมดขนาด **1.5B พารามิเตอร์**
5. รองรับ **LoRA fine-tuning** สำหรับปรับโมเดลเฉพาะงาน
6. ใช้ **hailo-ollama** เป็น backend + **Open WebUI** เป็น frontend

## ข้อจำกัดสำคัญ (Claude verified)

> Cloud LLMs จาก OpenAI/Meta/Anthropic มี 500B-2T พารามิเตอร์  
> AI HAT+ 2 รันได้จริงแค่ **1-7B** เท่านั้น (ตัวเลข 7B เป็น roadmap ยังไม่พร้อม ณ วันเปิดตัว)

สำหรับ **Wiki AI bot use case**: โมเดล 1.5B ตอบคำถามง่ายๆ ได้ แต่ synthesis หรือ reasoning ซับซ้อนต้องพึ่ง Claude API อยู่ดี

## หน้า Wiki ที่ได้รับการอัปเดต
- [[entities/iot/raspberry-pi]] — เพิ่ม AI HAT+ 2 compatibility
