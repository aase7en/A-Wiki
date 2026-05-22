# NotebookLM-first Protocol

> อ่านไฟล์นี้เมื่อต้องการ synthesize หลาย wiki page หรือใช้ /snapshot-nb

---

## 📘 NotebookLM-first Protocol (บีบอัด wiki ให้ NotebookLM ตอบแทน)

> **หลักการ**: User มี NotebookLM Pro — ใช้มันเป็น "ชั้นบีบอัด" ก่อนถึง Claude main context
> งานที่ต้อง synthesize หลาย wiki page → ให้ NotebookLM ตอบก่อน → user paste สรุปกลับมา → Claude ใช้ทำ action ต่อ

### ใช้กับ NotebookLM ดียังไง (ลด token)

- NotebookLM อ่าน wiki snapshot **ครั้งเดียว** (upload `exports/notebooklm/<domain>.md`) — **ไม่กิน Claude token เลย**
- คำถามเชิง synthesize ("เปรียบเทียบ X และ Y", "สรุปทั้ง domain") → NotebookLM ตอบเก่ง
- Claude หลักเหลือ context ไว้สำหรับ **เขียน wiki + reasoning + verify**

### Workflow ของผู้ใช้ (one-time setup → ใช้ตลอดไป)

```
1. รัน /snapshot-nb <domain>  (Claude เรียก scripts/export-to-notebooklm.sh)
2. Upload exports/notebooklm/<domain>.md → NotebookLM notebook ของ domain นั้น
3. ใช้ NotebookLM ตอบคำถาม synthesize → paste กลับ Claude เมื่อต้องการ action ต่อ
4. wiki เปลี่ยน → /snapshot-nb อีกครั้ง → upload ทับ
```

### ✅ เมื่อไหร่ควรเสนอ NotebookLM

- คำถามที่ต้อง synthesize หลาย wiki page (>3-5) — เสนอ user ใช้ NotebookLM ก่อน
- คำถามเชิง overview/summary ของทั้ง domain
- คำถามที่ user ถามซ้ำๆ คล้ายๆ เดิม — ย้าย load ไป NotebookLM

### ❌ เมื่อไหร่ห้าม / ไม่ควรเสนอ NotebookLM

- คำถามที่ต้องการ action (เขียน/แก้ไฟล์) — Claude ต้องทำเอง
- คำถามที่ wiki ยังไม่ถูก snapshot — NotebookLM จะตอบจากข้อมูลเก่า
- คำถามเร่งด่วน 1-2 หน้า — Claude ตอบเร็วกว่า
- ข้อมูล time-sensitive (ราคา/version) — ใช้ Gemini/WebSearch

### Quick Commands ที่เกี่ยวข้อง

| คำสั่ง | หน้าที่ |
|---|---|
| `/snapshot-nb` | export ทุก domain ไป `exports/notebooklm/` |
| `/snapshot-nb <domain>` | export เฉพาะ domain นั้น |
| `/ask-nb <คำถาม>` | Claude แนะนำให้ user ถาม NotebookLM ก่อน → รอ user paste คำตอบ → Claude นำไปใช้ต่อ |

### ตัวอย่าง

- User: "เปรียบเทียบ Hermes Agent กับ Claude Code ใน 5 มิติ"
  → Claude: "คำถามนี้ต้อง synthesize 2 entities + 1 concept page — แนะนำให้ถาม NotebookLM `Wiki/AI-Tools` ก่อน (ตอบไว ไม่กิน Claude token) แล้ว paste กลับมาถ้าอยาก save เป็น synthesis page"

- User: "สรุปทั้ง domain IoT"
  → Claude: "ใช้ NotebookLM `Wiki/IoT` ดีกว่า — ผมอัปเดต snapshot ล่าสุดเมื่อ <date> — ถ้าเก่าเกินไป รัน `/snapshot-nb iot` ก่อนครับ"

- User: paste คำตอบจาก NotebookLM
  → Claude: review → ถ้ามีค่า → save เป็น `wiki/synthesis/<slug>.md` พร้อม confidence marker `[notebooklm YYYY-MM-DD]`

### Re-export Triggers

Claude ควรเสนอ `/snapshot-nb` เมื่อ:
- หลัง ingest source ที่กระทบ entities/concepts >3 หน้า
- หลัง batch edit (เช่น `/lint` → fix หลายหน้า)
- ก่อน session end ถ้า session แก้ wiki >5 หน้า
- User ถามว่า "NotebookLM ของฉันเก่าหรือยัง"

### ข้อจำกัด

- Script ต้องรันบน **desktop** เท่านั้น (`bash` + git tools) — บน mobile/cloud ทำไม่ได้
- NotebookLM **ไม่ใช่ source-of-truth** — ของจริงอยู่ใน `wiki/` ของ repo
- ถ้า upload version เก่าทับใหม่ผิด → re-export แล้ว upload ใหม่ ไม่กระทบ wiki

ดูรายละเอียดวิธี setup ครั้งแรก: [`exports/notebooklm/README.md`](exports/notebooklm/README.md) และ skill `export-notebooklm`

---
