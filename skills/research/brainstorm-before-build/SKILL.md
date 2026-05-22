---
name: brainstorm-before-build
description: Use BEFORE designing/building anything new — features, systems, wiki domains, scripts, hooks, skills. Triggers: "ออกแบบ", "วางระบบ", "สร้างฟีเจอร์", "สร้าง skill", "ทำ feature", "/brainstorm". Forces clarify-then-propose flow. SKIP for trivial edits (เพิ่ม 1 บรรทัด, แก้ typo, ingest source ตรงๆ).
---

# brainstorm-before-build

> Adapted from Superpowers `brainstorming` — เบากว่า ปรับให้พอดี wiki+coding hybrid

## เมื่อไหร่ใช้

✅ ก่อนสร้าง: skill ใหม่, hook ใหม่, script ใหม่, wiki domain ใหม่, web app feature
✅ ก่อน refactor ที่กระทบ >3 ไฟล์
❌ ข้าม: เพิ่ม 1 หน้า wiki, แก้ typo, ingest source ปกติ, /lint

## Iron Law

> **NO BUILD WITHOUT CLARIFY + APPROACH-PICK FIRST**

ห้าม jump เข้า Edit/Write ทันทีถ้ายังไม่ทำ 3 step ข้างล่าง

## ขั้นตอน (บังคับเรียง)

### 1. Clarify (≤3 คำถาม)
ถาม user ทีละข้อ ไม่ใช่ยิงพร้อมกัน — สิ่งที่ยังไม่ชัด:
- ขอบเขต: ครอบคลุมแค่ไหน? domain ไหน?
- ข้อจำกัด: token budget? time? mobile compatible?
- success criteria: ทำเสร็จแล้วดูยังไงว่าใช้ได้

### 2. เสนอ 2-3 approach
รูปแบบ:
```
Approach A: [ชื่อสั้น] — [trade-off 1 บรรทัด]
Approach B: [ชื่อสั้น] — [trade-off 1 บรรทัด]
แนะนำ: [A/B/C] เพราะ [เหตุผล 1 บรรทัด]
```

### 3. รอ user เลือก
ห้ามเริ่ม implement ก่อน user confirm — ถ้า user เงียบ → ถาม "เอา approach ไหน?"

### 4. เขียน plan (ถ้างานใหญ่ >5 ไฟล์)
ใช้ Plan Mode หรือเขียน plan สั้นใน chat — ระบุไฟล์ที่จะแก้ + step

## Red flags (STOP signals)

ถ้าคิดประโยคพวกนี้ในใจ → หยุด กลับมาที่ขั้นตอน 1:
- "งานนี้ง่ายอยู่แล้ว ไม่ต้องถาม"
- "user คงต้องการแบบนี้แหละ"
- "เริ่มเขียนไปก่อน เดี๋ยวค่อยถาม"

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "user เคยทำแบบนี้แล้ว" | wiki/context/session-memory.md อาจจะระบุ approach เดิม — อ่านก่อน ถ้ามีให้ confirm ก่อนใช้ |
| "scope เล็กมาก" | ถ้าเล็กจริง user จะตอบ clarifying question ทันที 1 ประโยค ไม่เสียเวลา |
| "ไม่อยากถามเยอะ ดูโง่" | ถามถูกจุด = senior. รีบเขียนผิด = junior. ตามเป้าหมาย CLAUDE.md "คิดก่อนทำ" |

## ตัวอย่าง

**Bad (skipped brainstorm)**:
```
user: ทำสกิล superpowers ให้หน่อย
claude: [เริ่มสร้าง 13 skills ทันที]
```

**Good (followed brainstorm)**:
```
user: ทำสกิล superpowers ให้หน่อย
claude: ก่อนทำขอ confirm:
  - ติดเต็ม 13 skills หรือ cherry-pick?
  - เน้น coding หรือ wiki workflow?
  - token budget เพิ่มได้ไหม?
[รอตอบ → เสนอ 2 approach → user เลือก → ค่อยทำ]
```
