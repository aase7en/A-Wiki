---
name: a-doc-jd
description: "Job Description (JD) — ตำแหน่งงาน/หน้าที่/คุณสมบัติ. STUB รอ user สอน. Pattern from: job description พี่ปรี, พี่เดี่ยว, แม่บ้าน + 13 files. Trigger: 'JD', 'job description', 'ตำแหน่งงาน', 'หน้าที่', 'คุณสมบัติ'"
version: 0.1.0
author: A-Wiki (stub)
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
---

# A-Doc Type: JD (Job Description)

> **STUB** — มีตัวอย่าง 13+ ไฟล์ รอ user สอน template มาตรฐาน

## เมื่อไหร่ใช้
- เขียน JD ใหม่สำหรับตำแหน่ง
- ปรับปรุง JD ที่มีอยู่
- มอบหมายงาน (JD + assignment)

## ไฟล์ตัวอย่างใน `_uThaiHos`

| ไฟล์ | ตำแหน่ง |
|---|---|
| `20240730_job description พี่ปรี.docx` | ตำแหน่ง ปรี |
| `20240730_job description พี่เดี่ยว.docx` | ตำแหน่ง เดี่ยว |
| `20240819_JD_แม่บ้าน.doc` | แม่บ้าน |
| `20240819_job discription บี.docx` | บี |
| `20240819_มอบหมายงานปรีกับปาล์ม.docx` | มอบหมายงาน |
| `ENV-Evaluation-Form-2026.xlsx` | evaluation (related) |

## Style profile
✅ `style-profiles/gov-letter-standard.md`

## Structure (draft — 4 sections มาตรฐาน)

```
job description

ตำแหน่ง: <ชื่อตำแหน่ง>
หน่วยงาน: <หน่วยงาน>
รายงานต่อ: <หัวหน้า>

๑. หน้าที่ความรับผิดชอบ
   ๑) ...
   ๒) ...

๒. คุณสมบัติของผู้สมัคร
   - การศึกษา: ...
   - ประสบการณ์: ...
   - ทักษะ: ...

๓. อัตราเงินเดือน / สวัสดิการ
   ...

๔. เงื่อนไขการจ้าง
   ...
```

## Variant: มอบหมายงาน (Assignment)
- Pattern: JD + วันที่เริ่ม + ผู้มอบหมาย + ผู้รับมอบ
- ไฟล์ตัวอย่าง: `มอบหมายงานปรีกับปาล์ม.docx`

## TODO (รอ user สอน)
- [ ] template มาตรฐาน JD รพ.
- [ ] field mapping (ชื่อตำแหน่ง → หน้าที่ → คุณสมบัติ)
- [ ] ความแตกต่าง JD พนักงานราชการ vs ลูกจ้างชั่วคราว vs พนักงานกระทรวงสาธารณสุข
- [ ] มอบหมายงาน variant
- [ ] test generate จริง
