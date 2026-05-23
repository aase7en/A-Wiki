---
type: concept
tags: [openrouter, ai-tools, llm-routing, api-demo, free-models, openai-compatibility]
sources: [openrouter-api-demo]
created: 2026-05-10
updated: 2026-05-10
last_verified: 2026-05-10
verify_tool: training
---

# OpenRouter API

## Scope
หน้านี้เป็น overview ของ OpenRouter ในฐานะ unified API gateway สำหรับโมเดลหลายค่าย โดยโฟกัสที่ capability และ use case ของ OpenRouter เอง ไม่ได้ลงลึกเฉพาะ Claude Code integration หรือ implementation ของ agent project ใดๆ.

ถ้าต้องการใช้งาน OpenRouter ร่วมกับ Claude Code ให้ดู [[concepts/ai-tools/openrouter-claude-code]].

## นิยาม
OpenRouter เป็น **unified API gateway** สำหรับ LLM models หลายค่าย โดยรวมโมเดลจาก OpenAI, Google, Anthropic, Meta, NVIDIA และผู้ให้บริการอื่นไว้ใน API เดียว.

## ทำไมถึงสำคัญใน AI Tools
- ช่วยให้ทีมใช้งานโมเดลหลายค่ายโดยไม่ต้องเปลี่ยนโค้ดหลักของระบบมากนัก
- ลดความซับซ้อนเมื่อเปลี่ยนแพลตฟอร์มหรือสลับระหว่างโมเดลฟรีกับโมเดลจ่ายเงิน
- เหมาะสำหรับ workflow ที่ต้องการ fallback / auto-routing เช่น agent orchestration, web research, และเดโม internal

## วิธีการทำงาน
1. ใช้ API key เดียวกับ `OPENROUTER_API_KEY`
2. เรียก endpoint เดียว: `https://openrouter.ai/api/v1`
3. ส่ง request ในรูปแบบ OpenAI-compatible หรือ Anthropic-compatible ขึ้นกับ SDK/เครื่องมือที่ใช้
4. เลือกโมเดลโดยตรง เช่น `openrouter/auto`, `openrouter/free`, หรือโมเดลเฉพาะเจาะจงที่ provider รองรับ

## ความสามารถหลัก
- **Unified Interface**: เชื่อมต่อโมเดลหลายค่ายด้วย endpoint เดียว
- **OpenAI compatibility**: ใช้ OpenAI SDK เป็น drop-in replacement ได้ง่าย
- **Model routing**: `openrouter/auto` ช่วยเลือกโมเดลที่คุ้มค่าหรือพร้อมใช้งานโดยอัตโนมัติ
- **Free models**: มีโมเดลฟรีให้เลือกใช้งาน รวมถึงโมเดลที่มี tag `:free`
- **Transparent pricing**: รายงานค่าใช้จ่ายแยกตามโมเดล และมี billing dashboard ใน OpenRouter
- **Metadata / rankings**: สามารถส่งหัวข้อ app / referer เพื่อช่วย ranking และ analytics

## ตัวอย่าง use case ที่เหมาะสม
- งานค้นหรือ fact-check ที่อยากลดค่าใช้จ่าย
- สาธิตความสามารถโมเดลหลายตัวให้เจ้านายดู
- สลับ fallback จาก free → paid เมื่อ free model overloaded
- ทดลอง OpenAI-compatible code path โดยไม่ต้องเปลี่ยนคอนฟิกระบบหลัก

## Demo script
- ไฟล์สาธิต: `scripts/openrouter-demo.py`
- ใช้ environment variable `OPENROUTER_API_KEY`
- สามารถเรียก `openrouter/auto` และ `openrouter/free`
- มีตัวเลือก `--discover` เพื่อดึงรายชื่อโมเดลจาก API และแสดง free model ที่พร้อมใช้งาน
- ตัวอย่างคำสั่ง:
  - `OPENROUTER_API_KEY=sk-... python3 scripts/openrouter-demo.py`
  - `OPENROUTER_API_KEY=sk-... python3 scripts/openrouter-demo.py --discover --max-models 4`
  - `OPENROUTER_API_KEY=sk-... python3 scripts/openrouter-demo.py --models openrouter/auto,openrouter/free`

## คำแนะนำการใช้งาน
- เก็บ `OPENROUTER_API_KEY` ไว้ใน environment variable เท่านั้น
- ถ้าต้องการประหยัด ให้เริ่มที่ `openrouter/auto` หรือ `openrouter/free`
- ถ้าต้องการผลแม่นยำสูงกว่า ให้เลือกโมเดลเฉพาะเจาะจงจากการ discover
- ตรวจดูข้อจำกัด request rate และ quota ก่อนรัน benchmark

## ความสัมพันธ์
- [[concepts/ai-tools/openrouter-claude-code]] — ใช้ OpenRouter เป็น backend สำหรับ Claude Code
- [[concepts/ai-tools/local-llm-routing]] — OpenRouter เป็นทางเลือก fallback ที่ช่วย route งานง่าย-ยาก

## แหล่งข้อมูล
- `scripts/openrouter-demo.py` — สคริปต์ demo และตัวอย่างการเรียก API
- `scripts/test-free-subagent.sh` — benchmark free models และ OpenRouter fallback
