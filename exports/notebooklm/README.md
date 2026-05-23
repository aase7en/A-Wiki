# exports/notebooklm/

ไฟล์ snapshot ของ wiki ตาม domain สำหรับ upload ไป NotebookLM Pro

## ไฟล์ที่จะถูกสร้าง

หลังรัน `bash scripts/export-to-notebooklm.sh`:

| ไฟล์ | Domain | Notebook ที่ตั้งชื่อแนะนำ |
|---|---|---|
| `iot.md` | Internet of Things | Wiki/IoT |
| `env.md` | Environmental Health | Wiki/Env |
| `ai-tools.md` | AI Tools | Wiki/AI-Tools |
| `pharmacy.md` | Pharmacy | Wiki/Pharmacy |

แต่ละไฟล์ประกอบด้วย:
- Snapshot metadata (commit hash, วันที่)
- `index-<domain>.md` (domain index)
- `wiki/entities/<domain>/*.md`
- `wiki/concepts/<domain>/*.md`
- Sources ที่มี tag domain นั้น
- Synthesis pages ที่อ้างถึง domain

## วิธีใช้

```bash
# Export ทุก domain
bash scripts/export-to-notebooklm.sh

# Export เฉพาะ domain
bash scripts/export-to-notebooklm.sh ai-tools

# Export หลาย domain
bash scripts/export-to-notebooklm.sh iot env
```

หรือผ่าน Claude Code: พิมพ์ `/snapshot-nb` หรือ `/snapshot-nb ai-tools`

## ทำไมต้อง commit ไฟล์เหล่านี้

- Track snapshot history — ดูได้ว่า wiki state ตอน upload เป็นยังไง
- รองรับ rollback ถ้า NotebookLM ตอบเพี้ยนหลัง refresh
- Share ระหว่างเครื่อง (desktop ↔ mobile) ผ่าน git
- ไม่ต้อง re-export เมื่อ wiki ไม่เปลี่ยน

## ข้อควรระวัง

- **ห้าม upload** ถ้ามี secret/credential หลุด — Claude/skill จะ scan ก่อน commit
- ขนาดไฟล์ต้อง <500K คำ (NotebookLM Pro limit) — ถ้าเกิน script จะเตือน
- Re-export หลัง wiki เปลี่ยนใหญ่ ๆ → upload ทับ source เดิมใน NotebookLM (ไม่ต้องสร้าง notebook ใหม่)

ดูรายละเอียดเต็มใน [CLAUDE.md > 📘 NotebookLM-first Protocol](../../CLAUDE.md)
