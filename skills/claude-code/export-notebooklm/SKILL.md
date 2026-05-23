---
name: export-notebooklm
description: Use when the user types /snapshot-nb, asks to refresh the NotebookLM snapshot, asks to export the wiki for NotebookLM, or wants to update NotebookLM after ingesting new sources. Bundles wiki/{entities,concepts}/<domain> + index-<domain>.md + matching sources/synthesis into a single Markdown file at exports/notebooklm/<domain>.md, ready to upload as a single NotebookLM source.
---

# export-notebooklm

ใช้ skill นี้เมื่อ user ต้องการ snapshot wiki ไปเป็น source ของ NotebookLM Pro

## เมื่อไหร่ใช้

- User พิมพ์ `/snapshot-nb` หรือ `/snapshot-nb <domain>`
- User ขอ "อัปเดต NotebookLM" / "export wiki ไป NotebookLM"
- หลัง ingest source ใหญ่ที่กระทบหลายหน้า → **เสนอเองว่าจะ snapshot ไหม**
- ก่อนปิด session ที่มี wiki edit เยอะ — เตือน user ว่าควร refresh

## เมื่อไหร่ห้ามใช้

- งานปกติที่ไม่ได้แก้ wiki — ไม่ต้องเปลือง commit
- บน mobile/cloud env — script ต้องรัน bash จึงต้อง desktop
- ระหว่าง session ที่ user ยังแก้ wiki ค้างอยู่ — รอให้ stable ก่อน

## ขั้นตอน

1. **ตรวจ environment** — ถ้า `gemini` command not found = อยู่บน cloud → แจ้ง user ว่า:
   > "Script export ต้องรันบน desktop (Mac/Windows) — ตอนนี้คุณอยู่บน mobile/web ไม่สามารถรันได้"

2. **ตรวจว่ามี script** — `test -x scripts/export-to-notebooklm.sh` (ถ้าไม่มี executable bit ให้รัน `chmod +x`)

3. **รัน export**:
   ```bash
   bash scripts/export-to-notebooklm.sh <domain>     # single domain
   bash scripts/export-to-notebooklm.sh              # all domains
   ```

4. **ตรวจ output** ที่ `exports/notebooklm/<domain>.md`:
   - ขนาด <500K คำ (NotebookLM Pro limit)
   - ไม่มี secret/credential หลุด (ถ้ามี grep หาเตือน user)

5. **commit + push**:
   ```bash
   git add exports/notebooklm/<domain>.md
   git commit -m "snapshot(notebooklm): refresh <domain> @ $(date +%Y-%m-%d)"
   ```

6. **แจ้ง user**:
   - path ที่ export
   - ขนาดไฟล์ + จำนวน words
   - ลิงก์ raw GitHub (สำหรับ download upload ไป NotebookLM)
   - reminder: upload ไฟล์ใหม่ทับเดิมใน NotebookLM (ไม่ต้องสร้าง notebook ใหม่)

## วิธีตั้งค่า NotebookLM ครั้งแรก (one-time setup)

ทำแค่ครั้งเดียว แล้วใช้ skill นี้ refresh ต่อไป:

1. เข้า [notebooklm.google.com](https://notebooklm.google.com) (ใช้ Google account ที่เป็น Pro)
2. สร้าง notebook 1 อันต่อ domain — ตั้งชื่อ:
   - `Wiki/IoT`
   - `Wiki/Env`
   - `Wiki/AI-Tools`
   - `Wiki/Pharmacy`
3. ใน notebook → Add source → Upload `exports/notebooklm/<domain>.md`
4. (ทางเลือก) ตั้ง custom instruction:
   > "ตอบเป็นภาษาไทย กระชับ พร้อม cite path ของหน้า wiki (จาก heading `### \`path/to/file.md\``) ในทุกคำตอบ"

## Re-export workflow

```
wiki เปลี่ยน → /snapshot-nb <domain>
         ↓
script รัน → exports/notebooklm/<domain>.md อัปเดต
         ↓
user upload ทับ source เดิมใน NotebookLM
         ↓
NotebookLM index ใหม่ (อัตโนมัติ)
```

## ตัวเลือก domain

- `/snapshot-nb` → export ทุก domain (4 ไฟล์)
- `/snapshot-nb ai-tools` → เฉพาะ AI Tools
- `/snapshot-nb iot env` → 2 domain
- รองรับ: `iot`, `env`, `ai-tools`, `pharmacy`

## ข้อจำกัด

- NotebookLM Pro: ~50 sources/notebook → 1 file/domain เพียงพอ
- ขนาด source: <500K คำ — ถ้า domain โตเกินอาจต้องแบ่ง sub-domain
- Export **ไม่รวม** `raw/` (immutable, เป็น source documents ดิบ ไม่ใช่ความเข้าใจของ wiki)
- Export **ไม่รวม** `journal/`, `decisions/`, `profile.md` (ส่วนตัว, ไม่ควรอยู่ใน NotebookLM)

## ความปลอดภัย

ก่อน push exports/ ให้ Claude ตรวจ:
- ❌ API key, password, token, secret
- ❌ IP/MAC ส่วนตัว (ตาม Security Rules ใน CLAUDE.md)
- ❌ ข้อมูลส่วนบุคคลที่ไม่ควรอัป cloud

ถ้าเจอ → หยุดทันที + แจ้ง user

ดูรายละเอียดเต็มใน [CLAUDE.md > 📘 NotebookLM-first Protocol](../../../CLAUDE.md)
