---
type: concept
tags: [vibe-coding, ai-assisted, development-methodology, rapid-prototyping, llm]
sources: [vibe-pocketbase-gemini-plan]
created: 2026-05-11
updated: 2026-05-11
last_verified: 2026-05-11
verify_tool: training
---

# Vibe Coding

## นิยาม

Vibe Coding คือ methodology การพัฒนา software ที่ใช้ AI (LLM) เป็น co-pilot หลัก — ผู้พัฒนา "vibe" ด้วยการอธิบายสิ่งที่ต้องการเป็นภาษาธรรมชาติ แล้วให้ AI เขียนโค้ดให้ ผู้พัฒนาทำหน้าที่ review, test, และกำหนดทิศทาง

แนวคิดหลัก: **ลด friction ระหว่าง idea กับ working product ให้สั้นที่สุด** — วัดเป็นชั่วโมง ไม่ใช่สัปดาห์

## ทำไมถึงสำคัญ

- AI models ปัจจุบัน (Claude, Gemini, Qwen Code, DeepSeek) เขียนโค้ดได้ดีพอที่จะ ship ใช้งานจริงได้
- Stack เรียบง่าย + AI ที่ดี = สร้าง MVP ได้ใน 1-2 ชั่วโมง
- ลด barrier สำหรับคนที่ไม่ใช่ full-time developer แต่ต้องการเครื่องมือ custom

## หลักการสำคัญ

### 1. Keep it Simple
- ห้ามใช้ abstraction ที่ไม่จำเป็น (ไม่ต้องมี Redux, ไม่ต้อง ORM ซับซ้อน)
- เป้าหมายคือ working product — ไม่ใช่ perfect architecture
- ถ้า AI เสนอ pattern ซับซ้อน → บอก "simpler please"

### 2. เตรียม Context ให้ AI ก่อน
สร้างไฟล์ `CLAUDE.md` / `.ai/rules.md` ที่ root โปรเจ็คระบุ:
- Tech stack ที่ใช้
- กฎที่ห้ามทำ (เช่น "ห้ามใช้ Redux")
- Pattern มาตรฐาน (เช่น "ใช้ PocketBase SDK เสมอ")

### 3. เลือก Tech Stack ที่ AI รู้จักดี
- React + Vite + TailwindCSS — popular มาก AI เขียนได้แม่น
- PocketBase — single binary ง่าย AI ไม่งง
- หลีกเลี่ยง framework niche ที่ AI training data น้อย

### 4. ให้ AI ทำเป็น Step เล็กๆ
แทนที่จะสั่ง "สร้างทั้ง app" → แบ่งเป็น:
- Step 1: Setup project structure
- Step 2: ทำ login form
- Step 3: ทำ CRUD table

## วิธีการทำงาน (Workflow)

```
1. กำหนด .ai/rules.md (context + กฎ)
   ↓
2. สั่ง AI สร้าง boilerplate (Vite + React + Tailwind)
   ↓
3. ออกแบบ DB schema ผ่าน PocketBase Admin UI
   ↓
4. สั่ง AI เขียน frontend CRUD ต่อ API
   ↓
5. Test → feedback → iterate
   ↓
6. Deploy + Setup backup
```

## ตัวอย่าง Prompt ที่ดี

```
# Good — ชัดเจน มี context
"เขียนหน้า Login ด้วย OTP โดยใช้ PocketBase SDK
- UI ใช้ TailwindCSS, minimal design
- เมื่อ OTP ถูก ให้ redirect ไป /dashboard
- ห้ามใช้ Redux หรือ state management ซับซ้อน"

# Bad — กว้างเกินไป
"ทำระบบ login ให้หน่อย"
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| เร็วมาก — MVP ใน 1-2 ชั่วโมง | โค้ดอาจไม่ optimized |
| ไม่ต้องรู้ทุก detail ของ library | ต้องเข้าใจโค้ดที่ AI เขียนพอจะ debug ได้ |
| ดีสำหรับ internal tools / personal projects | ไม่เหมาะกับ large-scale production ที่ต้อง maintain นาน |
| ลด learning curve ของ tech stack ใหม่ | AI อาจเขียน pattern เก่าถ้าไม่ระบุ version |

## Tech Stack แนะนำสำหรับ Vibe Coding

| Layer | เลือก | เหตุผล |
|-------|-------|-------|
| Frontend | React + Vite + Tailwind | AI รู้จักดีมาก, starter เร็ว |
| Backend | PocketBase | Single binary, Admin UI, API อัตโนมัติ |
| Auth | PocketBase built-in | ไม่ต้องเขียนเอง |
| Infra | Nginx + simple VPS | Simple, AI เขียน config ได้ |
| Backup | bash + Cloudflare R2 | Shell script เรียบง่าย |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/pocketbase]]
- โปรเจ็คตัวอย่าง: [[synthesis/vibe-pocketbase-project]]
- AI tools ที่ใช้ได้: [[entities/ai-tools/hermes-agent]], [[concepts/ai-tools/openrouter-claude-code]]

## แหล่งข้อมูล

- [[sources/vibe-pocketbase-gemini-plan]] — คำแนะนำ project structure จาก Gemini Pro [training]
