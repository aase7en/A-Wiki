# Session Lifecycle Protocols — Mobile & Session End

> อ่านไฟล์นี้เมื่อต้องการรายละเอียด Mobile workflow หรือ Session End steps

---

## 📱 Mobile Workflow (iPhone / Web claude.ai/code)

> Claude: เมื่อรู้ว่า user อยู่บน mobile → ปรับ workflow อัตโนมัติ ไม่ต้องบอก user

### ความสามารถบน Mobile

| งาน | Mobile (iPhone/Web) | Desktop (Mac/Windows) |
|-----|--------------------|-----------------------|
| ถามคำถาม wiki | ✅ | ✅ |
| Ingest text / paste URL | ✅ | ✅ |
| WebSearch | ✅ | ✅ |
| อ่าน/เขียนไฟล์ใน repo | ✅ | ✅ |
| Commit + Push GitHub | ✅ | ✅ |
| Gemini CLI | ❌ (cloud env) | ✅ |
| รัน bash scripts | ⚠️ จำกัด | ✅ |
| Phase 2 Drive setup | ❌ | ✅ |
| `/snapshot-nb` (NotebookLM export) | ❌ | ✅ |
| Edit Protection hard lock | ⚠️ อาจไม่ทำงาน | ✅ |

### Permission Prompts บน Mobile

บน iPhone ผู้ใช้**ไม่เห็น Allow/Deny popup** เหมือน desktop — เป็นเรื่องปกติ  
Claude Code web จะใช้ permission ที่ตั้งไว้ใน `.claude/settings.json` โดยอัตโนมัติ  
ถ้าต้องการควบคุม permission → ต้องแก้ไขผ่าน desktop ก่อน

### Mobile-friendly Tasks

งานที่เหมาะทำจาก iPhone:
- ถามคำถาม / ค้นหาข้อมูล
- Paste บทความ/URL → ingest ลง wiki
- สั่ง `/verify` เพื่อ fact-check ข้อมูล
- สั่ง `/ask-nb` ถาม NotebookLM Pro (ถ้าตั้งค่าไว้แล้ว)
- Review และ approve งานที่ Claude เสนอ
- Push commit ที่เตรียมไว้แล้ว

---

---

## 🔚 SESSION END PROTOCOL (ทำทุกครั้งที่ผู้ใช้บอกจะออก)

> Claude: เมื่อผู้ใช้พูดคำเหล่านี้ → **ทำ Session End Protocol ทันทีโดยไม่ต้องถาม**
> คำที่ trigger: ไป, จากไป, ลาก่อน, บาย, bye, พรุ่งนี้ค่อยคุย, ออกแล้ว, หยุดก่อน, เดี๋ยวกลับมา

**ขั้นตอน (ทำตามลำดับ):**

1. **สรุปสิ่งที่คุยวันนี้** — จับใจความสำคัญเท่านั้น (ไม่เกิน 10 bullet)
   - งานที่ทำเสร็จ
   - งานที่ค้างอยู่ (todo)
   - ข้อมูลสำคัญที่ค้นพบ

1b. **อัปเดต `## 🔥 Active TODOs` ใน `wiki/context/session-memory.md`**:
   - **เพิ่ม** `- [ ] **[project-slug]** description` สำหรับงานค้างที่ต้องตามต่อข้าม session
   - **ลบบรรทัด** สำหรับงานที่ทำเสร็จแล้วใน session นี้ แล้วสรุปผลไว้ใน `log.md`
   - SessionStart hook ของทุก agent (Claude Code / Codex / Gemini) จะอ่านเฉพาะ `- [ ]` ใน block นี้ — ทำให้ไม่ลืมงานค้างที่ต้องเห็นทุก session
   - รักษา active list ให้ไม่เกิน 12 รายการ; งาน project/dream ที่ยังไม่ต้องโชว์ทุก session ให้ย้ายไป `wiki/context/project-backlog.md`
   - Cancelled project = ลบบรรทัดเลย
   - ตรวจสุขภาพด้วย `python3 scripts/todo-health.py`

2. **บันทึกลง log.md** ในรูปแบบ:
   ```
   ## [YYYY-MM-DD] session | <หัวข้อหลักวันนี้>
   - สรุปสั้นๆ
   - [ ] งานค้าง 1
   - [ ] งานค้าง 2
   ```

3. **commit + push ตรงลง main (solo workflow):**
   ```bash
   git add log.md wiki/context/session-memory.md
   git commit -m "session(YYYY-MM-DD): <สรุปสั้น>"
   git push origin main
   ```
   > Wiki นี้มีผู้ใช้คนเดียว multi-device — ไม่ใช้ PR/branch (ดู session-memory.md §Sticky)
   > SessionStart hook จะ `git pull --ff-only origin main` ทุก session → single brain

4. **ถ้า session แก้ wiki page > 5 หน้า** → เสนอ user ว่าควร refresh NotebookLM (`/snapshot-nb`) ก่อนปิด

5. **แจ้งผู้ใช้ว่าบันทึกเสร็จแล้ว** — ไม่ต้องบอกว่าครั้งหน้าเปิด branch ไหน (main เสมอ)

---

## Format ของ log.md

ทุก entry ขึ้นต้นด้วย:
```
## [YYYY-MM-DD] <action> | <title>
```

action types: `ingest` | `query` | `lint` | `update` | `synthesis` | `snapshot` | `session`
