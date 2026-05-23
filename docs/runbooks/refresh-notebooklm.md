# Runbook: Refresh NotebookLM Snapshot

> **วัตถุประสงค์**: Export wiki → `exports/notebooklm/` → upload ไป NotebookLM Pro
> **Last updated**: 2026-05-09

---

## Prerequisites

- Desktop environment (Mac/Windows) — **ทำบน mobile/cloud ไม่ได้**
- Bash + git tools

---

## ขั้นตอน

### 1. Export wiki

```bash
# ทั้งหมดทุก domain
bash scripts/export-to-notebooklm.sh

# หรือเฉพาะ domain
bash scripts/export-to-notebooklm.sh iot
bash scripts/export-to-notebooklm.sh env
bash scripts/export-to-notebooklm.sh ai-tools
bash scripts/export-to-notebooklm.sh pharmacy
```

### 2. ไฟล์ที่ได้

```
exports/notebooklm/
├── iot.md
├── env.md
├── ai-tools.md
└── pharmacy.md
```

### 3. Upload ไป NotebookLM

- เปิด [notebooklm.google.com](https://notebooklm.google.com)
- เลือก notebook ที่ต้องการ (Wiki/IoT, Wiki/Env, ฯลฯ)
- Add source → Upload → เลือกไฟล์จาก `exports/notebooklm/<domain>.md`

### 4. ตรวจสอบ

- NotebookLM จะ index เนื้อหาใหม่
- ทดสอบถามคำถามที่เกี่ยวข้องกับ domain นั้น

---

## เมื่อไหร่ควร refresh

- หลัง ingest source ที่กระทบ entities/concepts >3 หน้า
- หลัง batch edit (เช่น `/lint` → fix หลายหน้า)
- ก่อน session end ถ้า session แก้ wiki >5 หน้า
- เมื่อผู้ใช้ถามว่า "NotebookLM ของฉันเก่าหรือยัง"

---

## ข้อควรระวัง

- Script ทำงานบน **desktop** เท่านั้น
- NotebookLM **ไม่ใช่ source-of-truth** — ของจริงอยู่ใน `wiki/`
- ถ้า upload version เก่าทับผิด → re-export แล้ว upload ใหม่
- ตรวจสอบ `exports/` ก่อน push ว่าไม่มี secret/IP/MAC รั่วไหล