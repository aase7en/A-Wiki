---
type: entity
category: tool
tags: [agent-harness, langgraph, rejected, not-integrated]
sources: []
created: 2026-07-05
updated: 2026-07-05
last_verified: 2026-07-05
verify_tool: WebFetch
---

# bytedance/deer-flow

**ประเภท**: Full-stack "SuperAgent" harness — long-horizon research/coding/content orchestration
**สถานะ**: **พิจารณาแล้ว — ไม่ติดตั้ง** (ดูเหตุผลด้านล่าง)
**License**: MIT
**Stars**: 76.1k★ (2026-07-05)

## ภาพรวม

DeerFlow (โดย ByteDance) เป็น agent harness เต็มรูปแบบ — orchestrate sub-agent, decompose task, sandbox execution แยก, persistent memory, รองรับงานที่ใช้เวลานาทีถึงชั่วโมง สร้างบน LangGraph + LangChain (Python 76.8% + TypeScript), มี full-stack deployment (Gateway API + frontend + backend), เวอร์ชัน 2.0 (เขียนใหม่ทั้งหมด กุมภาพันธ์ 2026) [verified 2026-07-05]

## ทำไมไม่ integrate

ผู้ใช้ยืนยันการตัดสินใจนี้เมื่อถามเทียบกับ 3 repo อื่น (Matt Pocock Skills, Graphify, GBrain) ในเซสชันเดียวกัน:

1. **ซ้ำซ้อนกับ Hermes swarm harness ที่มีอยู่แล้ว** — A-Wiki มี Hermes (Telegram-accessible, 24/7, lifecycle-config.json phase routing, sequential persona fan-out) ทำหน้าที่เดียวกัน (orchestrate long-running multi-step งาน) อยู่แล้ว ติดตั้ง DeerFlow ซ้อนจะเป็น agent harness 2 ตัวแข่งกันทำหน้าที่เดียวกัน
2. **Tool/app-shaped หนักที่สุดใน 4 ตัว** — ไม่ใช่ skill drop-in, ต้อง deploy เป็น service แยก (Docker/subprocess, Gateway API + frontend) ขัดกับหลัก "เบาที่สุด" ของ brain-improvement-gate
3. **Blast radius สูง** — full-stack framework ที่มี backend+frontend+containerization ของตัวเอง การผสานเข้ากับ A-Wiki (ซึ่งเป็น wiki repo เบาๆ) จะเพิ่ม maintenance surface มากเกินความจำเป็น เทียบกับ marginal gain ที่ได้ (Hermes ทำหน้าที่คล้ายกันได้แล้ว)

## ถ้าจะพิจารณาใหม่ในอนาคต

เงื่อนไขที่ควรพากลับมาดูใหม่:
- Hermes swarm harness ไม่พอสำหรับ use case เฉพาะ (เช่นต้องการ sandbox execution ที่ Hermes ไม่มี)
- ต้องการ deploy เป็น service แยกอิสระจาก A-Wiki อยู่แล้ว (ไม่ผสานเข้า repo นี้)

## ความสัมพันธ์

- แทนที่ด้วย: [[hermes-agent]] — ทำหน้าที่ agent harness หลักของ A-Wiki อยู่แล้ว
- เกี่ยวข้องกับ: [[gbrain]] — พิจารณาคู่กันในรอบเดียวกัน (GBrain integrate แบบ opt-in, DeerFlow ไม่ integrate)
- เกี่ยวข้องกับ: [[ag2-orchestrator]] — A-Wiki's Planner→Executor→Validator loop เดิม ก็ทำหน้าที่คล้ายกันบางส่วน

## แหล่งข้อมูล

- GitHub: https://github.com/bytedance/deer-flow
- Author: ByteDance
- [verified 2026-07-05] `gh api repos/bytedance/deer-flow` — MIT, 76,102 stars, Python+TypeScript
