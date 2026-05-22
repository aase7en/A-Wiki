---
type: synthesis
tags: [openrouter, agent-routing, ai-tools, workflow, llm-routing]
sources: [openrouter-api-demo, agent-frameworks-local-debug-2026]
created: 2026-05-10
updated: 2026-05-10
---

# OpenRouter + Agent Routing — workflow synthesis

## Scope
หน้านี้วิเคราะห์การใช้ OpenRouter เป็นส่วนหนึ่งของ AI routing architecture และแยกออกจาก Gemini/Claude-only workflow. ถ้าต้องการ policy สำหรับ Gemini CLI + Claude ให้ดู [[wiki/synthesis/dual-ai-workflow]].

## คำถามที่ตอบ
OpenRouter ควรถูกใช้ใน architecture ของ AI agent และ local/model routing อย่างไร เพื่อให้ได้ทั้งความประหยัด, ความต่อเนื่องของ workflow, และ fallback path ที่ robust?

## สรุป
OpenRouter เป็นทางเลือกที่ดีสำหรับงานที่ต้องการโมเดลหลายค่ายโดยไม่ต้องเปลี่ยนโค้ดหลักหรือ lock-in กับ provider เดียว. ใน workflow ของ AI Tools wiki เราใช้ OpenRouter เป็น "fallback gateway" สำหรับ:

- งานค้นหา / fact-check / demo ที่ต้องการประหยัดค่าใช้จ่าย
- งานที่ต้องการ free models หรือ quick proof-of-concept
- แพลตฟอร์ม OpenAI-compatible path เมื่อระบบหลักยังต้องรักษา API integration เดิม

แต่สำหรับงาน reasoning ซับซ้อน, synthesis ข้ามโดเมน, หรือการแก้ไขระบบหลัก ควรให้ Claude Code ของ Anthropic เป็น orchestrator หลัก และใช้ OpenRouter เป็นหนึ่งใน nodes ของ routing chain.

## การวางตำแหน่งใน agent architecture

### 1. Claude Code = orchestrator หลัก
- Claude Code ยังเป็นตัวเลือกแรกสำหรับงานที่ต้องการ reasoning, schema, หรือแก้ไข wiki
- ถ้าคำสั่งเรียกว่า `/lint`, `ingest`, หรือสรุปข้ามหน้า ให้ใช้ Claude จริง

### 2. OpenRouter = fallback / cheap engine
- `openrouter/auto` ใช้เมื่ออยากให้ gateway เลือก model ที่คุ้มค่าที่สุด
- `openrouter/free` ใช้สำหรับงาน quick lookup หรือ demo ที่ไม่ต้องการคุณภาพสูงสุด
- `openrouter/<provider>/<model>` ใช้เมื่อทราบว่าโมเดลใดให้ผลดี (เช่น `openrouter/owl-alpha` หรือ `openrouter/nemotron-3-nano-omni-30b-a3b-reasoning:free`)

### 3. Local model routing / free model layer
- ใช้ `local-llm-routing` เป็นหมวดหลัก: งานง่ายไป local, งานยากไป cloud
- OpenRouter เป็นหนึ่งใน cloud layer ที่อยู่หลัง local fallback เมื่อ local modelไม่ตอบโจทย์
- ใน context ของ Claude Code + Hermes Agent + Telegram AI Router, OpenRouter มีบทบาทเป็น cloud path ที่พร้อม fallback และให้ค่าใช้จ่ายต่ำกว่า provider ตรง

## Workflow ตัวอย่าง

### Scenario A: Quick research / demo
1. User ส่งคำถามแบบทั่วไป
2. ถ้าเป็น query ที่ไม่ต้อง reasoning ลึก → เรียก `openrouter/free` หรือ `openrouter/auto`
3. ถ้า response พอใช้ได้ → แสดงผลทันที
4. ถ้าต้องลึกขึ้น → escalate เป็น Claude Code หรือ Gemini CLI

### Scenario B: Agent orchestration
1. Agent router ตรวจสอบ task complexity
2. ถ้างานง่าย/short answer → route ไป OpenRouter
3. ถ้างานต้อง reasoning, synthesis หรือ schema update → route ไป Claude Code
4. ถ้า OpenRouter / local models fail → fallback ไป Claude หรือ Gemini CLI ตาม policy

## ข้อดี
- ลด lock-in กับผู้ให้บริการเดียว
- สามารถใช้โค้ดโครงสร้างเดียวกัน (OpenAI-compatible) กับทั้ง provider และ OpenRouter
- รองรับ free model fallback สำหรับการ demo และ pilot
- ช่วยให้ `scripts/openrouter-demo.py` เป็น artifact ใช้งานจริง ไม่ใช่แค่ตัวอย่าง

## ข้อจำกัดและข้อควรระวัง
- Free model ของ OpenRouter มี quota / rate limit และบางครั้งอาจ offline
- ผลลัพธ์ไม่สม่ำเสมอเท่า Claude หรือ model paid tier
- ต้องมี billing method เพื่อ unlock free models บางตัว
- ไม่ควรใช้ OpenRouter เป็น authoritative source สำหรับ synthesis ข้ามโดเมนหรืองาน architectural decision

## ความสัมพันธ์
- [[concepts/ai-tools/openrouter-api]] — capability ของ OpenRouter API
- [[concepts/ai-tools/openrouter-claude-code]] — วิธีใช้ OpenRouter กับ Claude Code
- [[concepts/ai-tools/local-llm-routing]] — routing pattern ระหว่าง local, OpenRouter, Claude
- [[entities/ai-tools/telegram-ai-router]] — example of a router that can route queries to cloud or local models

## แหล่งข้อมูลที่ใช้
- [[sources/openrouter-api-demo]]
- [[sources/agent-frameworks-local-debug-2026]]
