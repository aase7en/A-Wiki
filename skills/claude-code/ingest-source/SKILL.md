---
name: ingest-source
description: Use this skill when the user sends a new source (file in raw/, URL, or pasted text) to be ingested into the wiki. Full workflow below — model-agnostic.
---

# ingest-source

> **วัตถุประสงค์**: ใช้เมื่อผู้ใช้ส่ง source ใหม่ (ไฟล์ใน `raw/`, URL, หรือ paste text) เพื่อ ingest เข้า wiki
> **เกณฑ์เรียกใช้**: source ยาว >2,000 บรรทัด → delegate subagent ให้อ่าน+สรุปก่อน

---

## ขั้นตอน

### 1. อ่าน source ทั้งหมด
- ถ้า source อยู่ใน `raw/` → อ่านจาก path ที่ผู้ใช้ระบุ
- ถ้า source เป็น URL → ใช้ WebFetch / แจ้ง user ให้ paste
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