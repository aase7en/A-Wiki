---
name: a-doc
description: "เอกสารราชการไทย/โรงพยาบาล — 8 ประเภทจากไฟล์งานจริง: ประกาศ/คำสั่ง/บันทึก/โครงการ/WI-SP/PR-QT-PO/JD/รายงาน/แบบบันทึก. Flow: detect type → grill-with-docs (format เสมอ) → dispatch types/<type>/ → generate via docx/word-generator → validate + render. รองรับ learn-from-example: ส่ง docx ตัวอย่าง → สกัด style profile. Trigger: 'หนังสือ', 'ราชการ', 'docx', 'คำสั่ง', 'บันทึก', 'ประกาศ', 'โครงการ', 'JD', 'WI', 'SP'."
version: 1.0.0
author: A-Wiki
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: both
---

# A-Doc — เอกสารราชการไทย/โรงพยาบาล (Router)

Aggregator สำหรับเอกสารราชการ — router + grill format + dispatch ไป type-specific subskill

> **ออกแบบจากไฟล์งานจริง `A:\_uThaiHos`** — 7 หมวดงาน, 135 subdirs, 464 เอกสาร
> Pattern ข้ามหมวด: ประกาศ/คำสั่ง/บันทึก/โครงการ/WI-SP/PR-QT-PO/JD/รายงาน/แบบบันทึก

## เมื่อไหร่ใช้

✅ ใช้:
- สร้างเอกสารราชการไทย (โรงพยาบาล/หน่วยงาน)
- แปลง PDF → Docx หรือกลับ
- เรียนรู้จากไฟล์ตัวอย่าง docx → สร้างแบบเดียว
- แก้ format (font/margins/paper) ของเอกสาร

❌ ข้าม:
- เอกสารธุรกิจสากล (English business doc — ใช้ docx ตรงๆ)
- สไลด์ (ใช้ frontend-slides)
- Spreadsheet (ใช้ xlsx)

## Iron Law

> **NO DOC GENERATION WITHOUT FORMAT GRILL FIRST**

ห้าม generate เอกสารก่อนยืนยัน format (paper/margins/font/numbers/date) ผ่าน `grill-with-docs`

## Flow (5 steps)

```
1. DETECT type  →  2. GRILL format  →  3. DISPATCH types/<type>/  →  4. GENERATE  →  5. VALIDATE + render
```

### Step 1: DETECT type

ถาม user หรือ infer จาก keyword:

| Keyword → Type | Folder |
|---|---|
| ประกาศ, นโยบาย, policy | `types/announce/` ✅ (canonical สมบูรณ์) |
| คำสั่ง, แต่งตั้ง, คณะกรรมการ | `types/order/` (stub) |
| บันทึกข้อความ, ขอ, เสนอ | `types/memo/` (stub — ใช้บ่อยสุด) |
| โครงการ, โครง, โครงการอบรม | `types/project/` (stub) |
| WI, SP, WP, วิธีปฏิบัติ, คู่มือ | `types/procedure/` (stub) |
| ขอซื้อ, PR, QT, PO, เบิกจ่าย, จัดซื้อ | `types/procurement/` (stub) |
| JD, job description, ตำแหน่งงาน | `types/jd/` (stub) |
| รายงาน, สรุปผล, การดำเนินงาน | `types/report/` (stub) |
| แบบบันทึก, แบบประเมิน, ทส., ENV-CFP | `types/form-record/` (stub) |
| (ไม่ตรง) | ถาม user + suggest ใกล้สุด |

### Step 2: GRILL format (ผ่าน `grill-with-docs`)

ถาม user **ทีละข้อ** (default ระบุไว้ให้เลือก):

```
Q1 ขนาดกระดาษ: A4 (default) | A5 | Letter | จดหมาย
Q2 Margins (DXA, default ราชการไทย):
   - Top: 1.75cm (default) | 2.54cm | custom
   - Bottom: 2.54cm (default) | custom
   - Left: 3cm (default) | custom
   - Right: 2cm (default) | custom
Q3 Font:
   - TH SarabunPSK 16pt (default มาตรฐานราชการใหม่)
   - TH SarabunIT๙ 16pt (รพ.อุทัย)
   - TH SarabunNew 16pt
   - Cordia New 14pt
   - Angsana New 14pt
Q4 ตัวเลข: ไทย [๑๒๓] (default ราชการ) | อารบิก [123]
Q5 วันที่: พ.ศ. (default — ใช้ thai-date-format) | ค.ศ.
Q6 Style profile ที่มีอยู่: hospital-announce | gov-letter-standard | procedure-wi-sp | custom
```

ถ้า user ส่งไฟล์ตัวอย่าง → ข้ามไป learn-from-example flow (ด้านล่าง)

### Step 3: DISPATCH → `types/<type>/SKILL.md`

อ่าน subskill ของ type นั้น → ทำตาม structure เฉพาะ (แต่ละ type มีโครงต่างกัน)

### Step 4: GENERATE

ผ่าน canonical skills:
- **`docx`** (docx-js) — สร้างเอกสารใหม่พร้อม style + numbering
- **`word-generator`** — Thai Standard Word Document (TH SarabunPSK)
- **`thai-government-form`** — structure ตาม ระเบียบสารบรรณ 2526

### Step 5: VALIDATE + render
- `python scripts/office/validate.py output.docx` (docx skill)
- `render-html` → preview ใน browser ก่อนส่ง user

## Learn-from-Example Flow (ใหม่ — รองรับการสอนของ user)

เมื่อ user ส่ง `example.docx` แล้วบอก "ทำแบบนี้":

### Iron Law #8: raw/ first
- copy `example.docx` → `raw/<slug>.docx` ก่อน (auto-sync Drive)
- แล้วค่อย analyze

### Extract style profile
```bash
python scripts/office/unpack.py raw/<slug>.docx unpacked/
# อ่าน unpacked/word/styles.xml + document.xml
# สกัด: font, size, margins, paper, heading styles
```

→ เขียนเป็น `style-profiles/<new-name>.md` (copy `_template.md` เป็นตัวตั้งต้น)
→ apply ให้เอกสารใหม่ใน Step 4

## โครง Folder

```
a-doc/
├── SKILL.md                          ← ไฟล์นี้ (router)
├── style-profiles/                   ← shared font/margins profiles
│   ├── _template.md
│   ├── hospital-announce.md          ← จาก ประกาศ รพ.อุทัย (Poppy analysis)
│   ├── gov-letter-standard.md        ← ราชการมาตรฐาน L3cm/R2cm
│   └── procedure-wi-sp.md            ← WI/SP/WP QA format
└── types/                            ← 8+ ประเภทเอกสาร
    ├── _template/                    ← สำหรับสร้าง type ใหม่ (copy + edit)
    ├── announce/                     ← ✅ CANONICAL สมบูรณ์
    ├── order/                        ← STUB
    ├── memo/                         ← STUB (ใช้บ่อยสุด)
    ├── project/                      ← STUB
    ├── procedure/                    ← STUB (WI/SP/WP)
    ├── procurement/                  ← STUB (PR/QT/PO)
    ├── jd/                           ← STUB
    ├── report/                       ← STUB
    └── form-record/                  ← STUB
```

**หลักการ (กันสับสน)**:
- `types/<X>/` = ประเภทเนื้อหา (1 folder = 1 type) — เพิ่ม type = copy `_template/`
- `style-profiles/<X>.md` = รูปแบบตัวอักษร/margins (แชร์ข้าม type) — 1 profile ใช้ได้หลาย type
- STUB = heading + TODO (รอ user สอน + มีไฟล์ตัวอย่างใน `_uThaiHos`)
- ANNOUNCE = canonical สมบูรณ์ (จากประกาศ รพ.อุทัย)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ default ไปเลย" | ราชการมีหลายมาตรฐาน (ม.ค. / รพ. / กทม.) — ต้อง confirm |
| "font SarabunPSK อยู่แล้ว" | รพ.อุทัยใช้ SarabunIT๙ — ต้องถามทุกครั้ง |
| "เลข 123 ก็ได้" | ราชการไทย = เลขไทย (๑๒๓); เลขอารบิก = เอกสารสากล |
| "ข้าม validate" | docx corrupt เปิดไม่ได้ทำได้บ่อย — validate ทุกครั้ง |

## Examples

**ใช้งาน**:
```
/A-Doc สร้างประกาศนโยบายความปลอดภัย รพ.อุทัย ปี 69
→ detect: announce (keyword "ประกาศ")
→ grill: A4? SarabunIT๙? L3cm/R2cm? เลขไทย? พ.ศ.?
→ dispatch: types/announce/SKILL.md (canonical)
→ generate: docx + style-profiles/hospital-announce.md
→ validate + render preview
```

```
/A-Doc บันทึกข้อความขอซื้อถังดับเพลิง (ส่ง example.docx มาด้วย)
→ detect: memo (keyword "บันทึกข้อความ" + "ขอ")
→ learn-from-example: unpack example.docx → extract style → new profile
→ grill: paper/margins/font จาก profile? หรือ override?
→ dispatch: types/memo/SKILL.md (stub — ถาม user structure)
→ generate + validate
```

## Invocation

```
/A-Doc [task description + optional example.docx]
```
