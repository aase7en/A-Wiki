---
name: root-cause-first
description: Use when user reports a bug, error, or wrong behavior. Triggers: "แก้บั๊ก", "ทำไมพัง", "ไม่ทำงาน", "error", "bug", "fix", "เพี้ยน", "ผิด". Forces reproduce → root cause in ONE sentence → fix. SKIP if user explicitly says "just patch" or "quick hack".
---

# root-cause-first

> Adapted from Superpowers `systematic-debugging` — wiki+coding hybrid, ไม่บังคับ TDD

## เมื่อไหร่ใช้

✅ user แจ้งว่ามีอะไรพัง / ผิด / error
✅ hook ไม่ block ตามที่คาดหวัง
✅ skill ไม่ trigger ตอนที่ควร trigger
✅ git push fail / commit fail / build fail
❌ ข้าม: user บอกชัดว่า "แก้แบบเร็วๆ ก่อน" / "patch ไปก่อน"
❌ ข้าม: feature request ใหม่ (ใช้ brainstorm-before-build แทน)

## Iron Law

> **NO FIX WITHOUT REPRODUCE + ROOT CAUSE FIRST**

ห้ามแก้ code/config ก่อนตอบ 2 คำถาม:
1. **Reproduce ได้ไหม?** ขั้นตอนเป๊ะๆ ที่ทำให้พังซ้ำ
2. **Root cause คืออะไร?** อธิบายเป็น **ประโยคเดียว** ไม่เกิน 20 คำ

## ขั้นตอน (บังคับเรียง)

### 1. Reproduce
- รัน command ที่พัง → เก็บ error message เป๊ะๆ (copy stderr/stdout)
- ถ้า reproduce ไม่ได้ → ถาม user เพิ่ม (env, OS, command exact)
- ห้ามแก้ blind จาก guess

### 2. Investigate (Cost-First — ตาม CLAUDE.md Pyramid)
- Level 1: `cat`, `ls`, `grep` ดูสภาพไฟล์ → free
- Level 1: `git log -- <file>` ดูประวัติแก้ล่าสุด → free
- Level 2: ถ้าซับซ้อน → delegate free subagent scan (`Explore`)
- ⚠️ ห้าม Sonnet scan >5 ไฟล์เอง — delegate ก่อน

### 3. Root cause (ประโยคเดียว)
รูปแบบ:
```
Root cause: [สาเหตุที่แท้จริง — ไม่ใช่อาการ]
```

ตัวอย่าง:
- ❌ อาการ: "hook ไม่ทำงาน"
- ✅ root cause: "settings.json matcher 'Edit|Write' ไม่ match 'MultiEdit' เพราะ regex ต้องเป็น 'Edit|Write|MultiEdit'"

### 4. เสนอ fix → confirm กับ user
- ระบุไฟล์ + บรรทัดที่จะแก้
- ถ้า fix กระทบ >1 ไฟล์ → เข้า brainstorm-before-build แทน

### 5. Verify หลัง fix
- Reproduce step เดิม → ต้องไม่พังแล้ว
- ใช้ skill `verify-before-done` 4-point check

## Red flags (STOP signals)

- "น่าจะเป็นเพราะ X" → guess → ต้อง verify ก่อนแก้
- "ลอง restart/clear cache ดูก่อน" → workaround → ยังไม่ root cause
- "เพิ่ม try/except กลบ error" → ปกปิด → ไม่แก้รากปัญหา
- "user มีปัญหาเฉพาะตัว" → blame user → check env แล้วยัง

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "แก้ตามที่เคยเจอ" | bug เดียวกันที่อื่นไม่ได้แปลว่ารากเดียวกัน — reproduce ก่อน |
| "fix แล้วเดี๋ยวดูทีหลัง" | bug ครึ่งๆ กลางๆ = bug ใหม่ที่ debug ยากกว่าเดิม |
| "user รีบ" | แก้ผิดรอบแรก → 2 รอบ. ถ้าจริงๆรีบ → ทำ workaround + log "TODO root cause" ที่ session-memory.md |

## ตัวอย่าง

**Bad**:
```
user: hook ไม่ทำงานเลย
claude: ลอง restart Claude Code ดูครับ [แก้ blind]
```

**Good**:
```
user: hook ไม่ทำงานเลย
claude: ขอ reproduce ก่อน:
  - แก้ไฟล์ไหน?
  - error message อะไร?

[user ตอบ → claude check settings.json + run hook manual]

Root cause: settings.json matcher field "Edit|Write" ไม่ครอบ "MultiEdit"

Fix: แก้บรรทัด 89 ใน .claude/settings.json จาก "Edit|Write" → "Edit|Write|MultiEdit"
ดำเนินการได้ไหม?
```

## Workaround mode (เมื่อ user สั่ง "just patch")

ถ้า user บอกชัดว่า "แก้เร็วๆ ก่อน" / "patch ไปก่อน":
1. ✅ ทำ workaround ได้
2. ต้องบันทึก TODO ใน `wiki/context/session-memory.md`:
   ```
   - [ ] Root cause TBD: <ปัญหา> — workaround ที่ <ไฟล์:บรรทัด> เมื่อ YYYY-MM-DD
   ```
3. แจ้ง user ว่า "บันทึก TODO ไว้แล้ว — ควรกลับมา debug จริงๆ ภายใน X วัน"
