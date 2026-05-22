---
type: source
title: "Pharmacy App UI Design Instructions (v3)"
slug: pharmacy-ui-instructions
date_ingested: 2026-04-30
original_file: raw/pharmacy-ui-instructions.md
tags: [pharmacy, ui-design, web-app, interactive-form]
---

# Pharmacy App UI Design Instructions (v3)

**ประเภท**: UI/UX Design Specification  
**วันที่ Ingest**: 2026-04-30  
**เวอร์ชัน**: 3  

## ประเด็นหลัก

1. **Interactive Form UI** — 6 หลัก:
   - **Editable Name** — ตรวจสอบและแก้ไขชื่อยา
   - **DB Update / JSON Patch** — อัปเดตฐานข้อมูล (add new drug)
   - **Export/Copy** — CSV, Copy LINE, JSON Patch
   - **Drug Aliases Lookup** — ตรวจสอบชื่อสะกดผิด
   - **Quantity Editor** — ปรับแต่งจำนวนสั่งซื้อ
   - **Badge/Flag System** — ✅ ✅ ⚠️ ❌ ℹ️

2. **Category Code Mapping (ATC-based)**:
   - A01-A11: ยาเพื่อระบบทางเดิน
   - C05-D10: ยาเพื่อหนัง
   - G03: ฮอร์โมน
   - J02: ยาต้านเชื้อ
   - N02-N07: ยาเพื่อระบบประสาท
   - R05-R06: ยาเพื่อระบบหายใจ
   - S01: ยาหยอดตา

3. **Export/Copy Options**:
   - **CSV** — ไฟล์ `.csv` (UTF-8 BOM, Excel compatible)
   - **Copy LINE** — สำหรับส่งต่อลูกค้า (clean format)
   - **JSON Patch** — สำหรับระบบอัปเดต DB

4. **Drug Matching Logic**:
   - ค้นหา sp_drugs_full_3760.json
   - ถ้าไม่เจอ → ตรวจสอบ drug-aliases.md
   - Fuzzy match → แนะนำตัวเลือก
   - Flag ❌ ⚠️ ✅ ตามสถานการณ์

## ข้อมูลที่น่าสนใจ

| คุณสมบัติ | รายละเอียด |
|---------|-----------|
| Editable Fields | ชื่อยา (name), ปริมาณ (qty) |
| Badge Colors | ✅ (match), ⚠️ (warning), ❌ (error), ℹ️ (info) |
| Export Quality | UTF-8 BOM สำหรับ Excel |
| Quantity Reset | Button เพื่อ reset qty → 0 |
| Real-time Validation | Instant feedback ขณะพิมพ์ |

## ข้อโต้แย้ง / ความขัดแย้ง

- **UI ซับซ้อน** — ต้องมี UX testing กับผู้ใช้งานจริง
- **Category Code เยอะ** — ต้อง filter/search เพื่อหลีกเลี่ยง confusion
- **Image OCR (ยังไม่ได้ลง)** — ต้อง Claude API สำหรับอ่านรูปภาพ

## Aliases Reference (ตัวอย่างจากเอกสาร)

ตามเอกสาร drug-aliases.md มี 45+ ยาทั่วไป พร้อม:
- Aliases (อมอก, amox, amox)
- Generic Name (Amoxicillin)
- Category Code (A01)
- Standard Form (AMOXICILLIN 500MG 20X10S)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[wiki/concepts/pharmacy/ui-design-pharmacy]]
- [[wiki/synthesis/pharmacy-web-app-roadmap]]
- [[wiki/entities/pharmacy/drug-matching-system]]
- [[index-pharmacy]]
