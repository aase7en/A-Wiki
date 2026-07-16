---
name: a-doc-form-record
description: "แบบบันทึก/แบบประเมิน — record form + ลายเซ็น. STUB รอ user สอน. Pattern from: แบบบันทึก ทส.1, ENV-CFP-004. Trigger: 'แบบบันทึก', 'แบบประเมิน', 'ทส.', 'ENV-CFP', 'ฟอร์ม', 'form'"
version: 0.1.0
author: A-Wiki (stub)
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
---

# A-Doc Type: Form Record (แบบบันทึก/แบบประเมิน)

> **STUB** — แบบฟอร์ม record มีหลายรหัส (ทส./ENV-CFP) รอ user สอน template แต่ละรหัส

## เมื่อไหร่ใช้
- บันทึกกิจกรรม (ทส.1, ทส.2)
- บันทึกผลการตรวจวัด (water quality, etc.)
- แบบประเมิน (5S, OSH, internal audit)

## ไฟล์ตัวอย่างใน `_uThaiHos`

| ไฟล์ | รหัส |
|---|---|
| `20260318_แบบบันทึก ทส.1.pdf` | ทส.1 — มูลฝอย |
| `20260318_แบบบันทึก ทส.1-1.pdf` | ทส.1-1 |
| `20260318_แบบบันทึก ทส.2.pdf` | ทส.2 |
| `20260318_แบบบันทึกกิจกรรมบ่อบำบัด.xlsx` | — |
| `20260318_แบบบันทึกคุณภาพน้ำประปา ENV-CFP-004.docx` | ENV-CFP-004 — คุณภาพน้ำ |
| `20240819_แบบประเมินตนเอง OSH รพช.ปี65.xlsx` | OSH self-assessment |

## Form code convention
- **ทส.X** = มูลฝอย (ตามพระราชบัญญัติความสะอาด)
- **ENV-CFP-XXX** = Environmental - Carbon Footprint
- **EOH-XXX** = Environmental & Occupational Health
- **WI-XXX** = Work Instruction

## Structure (draft — 4 ส่วน)

```
[โลโก้ รพ.]
แบบบันทึก <รายการ>
รหัส: <XXX-NNN>                          ฉบับที่: <REV>

| วันที่ | เวลา | รายการ | จำนวน | หน่วย | ผู้บันทึก | หมายเหตุ |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

หมายเหตุ: <เพิ่มเติม>

ผู้บันทึก                              ผู้ตรวจสอบ
(ลายเซ็น)                            (ลายเซ็น)
(ชื่อ)                                (ชื่อ)
วันที่ X เดือน X พ.ศ. XXXX             วันที่ X เดือน X พ.ศ. XXXX
```

## Format consideration
- ส่วนใหญ่ใช้ **xlsx** มากกว่า docx (table-heavy)
- ถ้าเป็น form ที่ต้อง print + เซ็น → docx หรือ pdf
- ENV-CFP-004 = docx (มี text + table ผสม)

## TODO (รอ user สอน)
- [ ] form code registry (ทส.X, ENV-CFP-XXX, etc.)
- [ ] template แต่ละรหัส
- [ ] xlsx vs docx choice rule
- [ ] signature chain
- [ ] test generate จริง
