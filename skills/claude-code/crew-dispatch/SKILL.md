# Skill: Crew Dispatch (Sanji's Kitchen)

> Vegapunk (Claude Sonnet) วิเคราะห์คำถาม → แตกเป็น subtasks → dispatch ให้ลูกเรือ parallel

## เมื่อไหร่ใช้

✅ คำถามที่ต้องการ **ข้อมูลหลายมิติพร้อมกัน** เช่น:
- "เปรียบเทียบ X กับ Y แล้วหาข้อมูลล่าสุดด้วย"
- "scan wiki ทุก domain แล้วสรุป"
- "ingest 3 sources พร้อมกัน"

✅ งานที่ **sequential จะช้าเกินไป** (>3 subtasks คนละประเภท)
✅ มี API key อย่างน้อย 1 ตัว (Nami/Luffy/Robin/Franky)

❌ ข้าม: คำถามง่าย 1 มิติ, งานที่ต้อง Vegapunk เขียนเอง, sensitive tasks

---

## ขั้นตอน (Vegapunk ทำตามนี้)

### 1. วิเคราะห์คำถาม
แตกออกเป็น subtasks — ระบุ task_type ตาม routing table:
- `search` / `lookup` / `url` → Nami (Gemini)
- `analyze` / `compare` / `reason` → Robin (DeepSeek)
- `scan` / `lint` / `execute` → Luffy (Groq)
- `code` / `build` / `refactor` → Franky (OpenRouter)

### 2. ตรวจสอบ crew status
```bash
python3 scripts/crew-dispatch.py --list-crew
```

### 3. Dispatch parallel
```bash
python3 scripts/crew-dispatch.py \
  --task "search:..." \
  --task "analyze:..." \
  --task "scan:..."
```

### 4. Synthesize
อ่าน Report → Vegapunk เขียนคำตอบสรุป / wiki page ให้ user

---

## Routing ย่อ

| งาน | ลูกเรือ | Cost |
|-----|---------|------|
| หาข้อมูล/web | Nami 🗺️ | ฟรี |
| วิเคราะห์/เปรียบ | Robin 📚 | ถูก |
| scan/lint ไฟล์ | Luffy ⚡ | ฟรี |
| เขียนโค้ด | Franky 🔧 | ฟรี |
| วางแผน/เขียน wiki | Vegapunk 🧠 | ปกติ |

รายละเอียดเต็ม: `docs/protocols/crew.md`
