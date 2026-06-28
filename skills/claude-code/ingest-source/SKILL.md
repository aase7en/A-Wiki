---
name: ingest-source
description: Use this skill when the user sends a new source (file in raw/, URL, or pasted text) to be ingested into the wiki. Full workflow below — model-agnostic.
---

# ingest-source

> **วัตถุประสงค์**: ใช้เมื่อผู้ใช้ส่ง source ใหม่ (ไฟล์ใน `raw/`, URL, หรือ paste text) เพื่อ ingest เข้า wiki
> **เกณฑ์เรียกใช้**: source ยาว >2,000 บรรทัด → delegate subagent ให้อ่าน+สรุปก่อน

---

## ขั้นตอน

### 0. Pre-flight — ensure source is in `raw/` FIRST (mandatory)

> 🚫 **ข้ามขั้นนี้ไม่ได้** — hook `check_source_original_file` จะ block การ Write
> `wiki/sources/<slug>.md` ถ้า `original_file:` ไม่ชี้ไปไฟล์จริงใต้ `raw/`
> (since 2026-05-30 — ดู [[ingest-flow-raw-first]])

ตรวจสอบและจัด source เข้า `raw/` ก่อนสร้าง source summary:

| สิ่งที่ user ส่ง | ทำอะไร |
|------------------|--------|
| Path ใน `raw/` แล้ว | ✅ ผ่าน — ไปต่อ Step 1 |
| **URL** | `WebFetch` → **save markdown ลง `raw/<slug>.md` ทันที** พร้อม frontmatter: `source_url`, `fetched_at: YYYY-MM-DD`, `fetched_via: WebFetch`, ถ้าเป็น model-filtered ให้ใส่ `note:` แจ้งด้วย |
| | ถ้า URL คืน 403/JS-rendered → ใช้ `scripts/wiki/scrape-advanced.py --url <url>` แทน |
| **Paste text** | ขอ slug จาก user → save ลง `raw/<slug>.md` พร้อม `pasted_at:`, `language:` |
| **Binary/PDF/DOCX/XLSX/PPTX/EPUB** | save ลง `raw/<slug>.<ext>` (gitignored อัตโนมัติ) — `ingest-source.py` ใช้ MarkItDown แปลงเป็น Markdown อัตโนมัติ; output ไป `raw/<slug>.md` เพื่อให้ hook provenance ผ่าน |

**ทำไม**: `raw/` คือ symlink → Google Drive A-Wiki-Data/raw — ออกแบบให้รองรับไฟล์ดิบ
หนักๆ + เก็บ provenance permanent. ถ้าข้าม:
- เสีย provenance หากต้นทาง (URL/paste) หาย
- ขัด rule "frontmatter บังคับ" ใน `wiki/sources/CLAUDE.md`
- โดน hook block ทันที (exit 2) → ทำต่อไม่ได้

### 1. อ่าน source จาก `raw/`
- อ่าน `raw/<slug>.<ext>` ที่เพิ่ง save ใน Step 0
- ถ้า source ยาว >2,000 บรรทัด → delegate `general-purpose` subagent สรุป
- สรุปประเด็นหลัก → ถามผู้ใช้ว่าต้องการเน้นอะไรเป็นพิเศษ

### 2. ระบุ domain

| เกณฑ์ | Domain |
|-------|--------|
| เกี่ยวข้องกับ hardware, sensor, protocol, wireless | **IoT** |
| เกี่ยวข้องกับ ขยะติดเชื้อ, น้ำเสีย, กฎหมายสิ่งแวดล้อม | **Environmental Health** |
| เกี่ยวกับ AI agent, LLM, framework | **AI Tools** |
| เกี่ยวกับ ยา, ร้านขายยา, drug catalog | **Pharmacy** |
| หลาย domain | **Cross-domain** → synthesis |

### 3. สร้าง source summary page

ไฟล์: `wiki/sources/<slug>.md`

slug format: `kebab-case-english-based-on-title`

```markdown
---
type: source
title: "Title"
slug: source-slug
date_ingested: YYYY-MM-DD
original_file: raw/filename.md  # หรือ web-YYYY-MM-DD.md
tags: [tag1, tag2]
---

# Title

**ประเภท**: article | paper | video | podcast | book-chapter
**วันที่**: YYYY-MM-DD หรือ unknown
**ผู้เขียน**: ...

## ประเด็นหลัก
1. ...
2. ...

## ข้อมูลที่น่าสนใจ / สถิติ
- ...

## ข้อโต้แย้งหรือความขัดแย้ง
- เปรียบเทียบกับข้อมูลที่ wiki มีอยู่แล้ว

## หน้า Wiki ที่ได้รับการอัปเดต
- [[entities/...]]
- [[concepts/...]]
```

### 4. อัปเดต entities/concepts ที่เกี่ยวข้อง

- สร้างใหม่ถ้ายังไม่มี
- แก้ไขหน้าปัจจุบันถ้ามีข้อมูลเพิ่มเติม
- ตรวจสอบ contradiction กับข้อมูลที่มีอยู่

### 5. Large file check

ถ้า source เป็น **binary หรือ data ขนาดใหญ่** (PDF / รูปภาพ / CSV / JSON ใน raw/):
- ตัวไฟล์ถูก gitignore อัตโนมัติ — **ไม่ต้อง** และ **ห้าม** เพิ่มในขั้น git add
- เพิ่ม entry ใน `wiki/context/local-sources.md` (manifest): ชื่อไฟล์, domain, ขนาด, วันที่ ingest
- `wiki/context/local-sources.md` จะถูก commit แทน (tracked ใน git)

### 6. ปิดท้าย

- [ ] อัปเดต `index-{domain}.md` — เพิ่มทุกหน้าที่สร้าง/แก้ไข
- [ ] อัปเดต `wiki/context/wiki-overview.md` → รัน `python3 scripts/gen-index.py`
- [ ] เพิ่ม log entry ใน `log.md`:

  ```
  ## [YYYY-MM-DD] ingest | <slug>
  - สร้าง: <paths>
  - อัปเดต: <paths>
  ```

- [ ] รายงานสรุปให้ผู้ใช้: หน้าที่สร้าง, หน้าที่อัปเดต, สิ่งที่ขัดแย้ง
- [ ] ถ้า ingest กระทบ >3 หน้า → เสนอ `/snapshot-nb <domain>` เพื่อ refresh NotebookLM

## กฎ
- raw/ เป็น immutable — ห้ามแก้ไข source ต้นฉบับ
- domain ต้องระบุก่อน create file ใดๆ
- ทุก wiki page ต้องมี cross-reference ไปหาหน้าที่เกี่ยวข้อง
- ถ้าเป็น binary/large file — ห้าม git add, ใช้ `local-sources.md` แทน