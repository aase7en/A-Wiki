# A-Wiki — Schema & Rules

> **วัตถุประสงค์**: A-Wiki เป็น hybrid wiki system — skills/scripts/wiki สาธารณะบน GitHub, ข้อมูลส่วนตัว/ดิบบน Google Drive

---

## Session setup

Wiki หลักอยู่ที่ repo root (detect จาก git root)

### 📚 Context Auto-Load
Agent อ่านไฟล์เหล่านี้ก่อนตอบคำถาม:
- `README.md` ← project overview
- `.local/profile.md` ← ข้อมูลเจ้าของ (gitignored, GDrive sync)
- `.local/session-memory.md` ← decisions ค้าง + TODO (gitignored, GDrive sync)

> ถ้า `.local/` ไม่มี → แจ้ง user ให้ setup GDrive sync ก่อน (ดู `docs/protocols/gdrive-sync.md`)

---

## 🗜️ Cost-First Decision Pyramid

| Level | ช่องทาง | ค่าใช้จ่าย | ใช้กับงาน |
|---|---|---|---|
| **-1** | Local search (grep/FTS5) | ฟรี + ออฟไลน์ | ค้น wiki หลายไฟล์ |
| **0** | Hook | ฟรี | งานซ้ำทุก session |
| **1** | Free API (OpenRouter free / Gemini Flash) | ฟรี | search, lookup, สรุป |
| **2** | Cheap paid (DeepSeek, Qwen) | ถูก | reasoning เบา |
| **3** | Subagent | ถูก | scan ไฟล์เยอะ |
| **4** | Current agent | ปกติ | เขียน wiki, schema |

---

## 🔒 Solo Wiki — No Branch, No PR

> **commit ตรงลง `main` เท่านั้น** — ห้ามสร้าง branch, ห้ามเปิด PR

---

## 💰 Knowledge Currency

> Training cutoff = ข้อมูลหลังจากนั้นห้ามเดา → ใช้ skill `web-research` เสมอ
> Confidence markers: `[training]` `[verified YYYY-MM-DD]` `[wiki]` `[notebooklm YYYY-MM-DD]`

---

## 🛠️ Skills (ดู `skills/README.md` สำหรับ catalog)

Skills อยู่ที่ `skills/{category}/{name}/SKILL.md`
Link to agent: `bash scripts/link-skills.sh`

---

## ✅ กฎสำคัญ

1. **raw/ เป็น immutable** — อ่านได้ ห้ามแก้ไขหรือลบ
2. **wiki/ เป็นของ agent** — สร้าง แก้ไข และดูแลทุกหน้า
3. **ชื่อไฟล์ wiki** ใช้ kebab-case ภาษาอังกฤษ
4. **Cross-reference** — ทุกหน้าต้องลิงก์ไปหาหน้าที่เกี่ยวข้อง
5. **ใช้ภาษาไทย** ในการสื่อสารกับผู้ใช้ (เว้นแต่ถูกขอให้ใช้ภาษาอื่น)
6. **confidence marker** — บังคับระบุทุกครั้งที่ตอบข้อมูลสำคัญ
7. **CLAUDE.md ห้ามแก้เองโดยไม่ได้รับอนุญาต**

---

## 📁 โครงสร้างโฟลเดอร์

```
A-Wiki/
├── README.md           ← Home (Public)
├── CLAUDE.md           ← Schema นี้
├── skills/             ← Agent skills
├── scripts/            ← Utility scripts
├── docs/               ← Protocols + guides
├── wiki/               ← Knowledge pages
├── decisions/          ← ADRs
├── .local/             ← [GDrive] Profile, sessions
├── raw/                ← [GDrive] Source documents
└── exports/            ← [GDrive] NotebookLM bundles
```

---

*Schema v1.0 — อัปเดตล่าสุด: 2026-05-22*