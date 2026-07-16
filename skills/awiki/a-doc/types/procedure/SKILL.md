---
name: a-doc-procedure
description: "WI/SP/WP — Work Instruction/Standard Procedure/Work Procedure (QA standard). STUB รอ user สอน. Pattern from: WI-EOH-001, SP-EOH-002, WP-ENV-001. Trigger: 'WI', 'SP', 'WP', 'วิธีปฏิบัติ', 'คู่มือ', 'มาตรฐาน'"
version: 0.1.0
author: A-Wiki (stub)
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
---

# A-Doc Type: Procedure (WI/SP/WP — QA Standard)

> **STUB** — structure 6 sections มีอยู่แล้วใน `style-profiles/procedure-wi-sp.md`
> รอ user สอน variant เฉพาะ (WI vs SP vs WP)

## เมื่อไหร่ใช้
- คู่มือปฏิบัติงาน (WI)
- มาตรฐาน/แนวทาง (SP)
- กระบวนการทำงาน (WP)
- สำหรับ HA Standard audit

## ไฟล์ตัวอย่างใน `_uThaiHos`

| Code | หัวข้อ |
|---|---|
| WI-EOH-001-00 | ระบบบำบัดน้ำเสีย |
| SP-EOH-002-00 | ดูแลจัดเก็บ/ขนย้ายมูลฝอย |
| WP-ENV-001 | วิธีปฏิบัติงานมูลฝอย |
| WP-ENV-002 | วิธีปฏิบัติงานระบบบำบัดน้ำเสีย |

## Style profile
✅ `style-profiles/procedure-wi-sp.md` (มี 6-section structure + docx-js + revision table)

## Document code convention
- `WI-<DEPT>-<NNN>-<REV>` — Work Instruction
- `SP-<DEPT>-<NNN>-<REV>` — Standard Procedure
- `WP-<DEPT>-<NNN>-<REV>` — Work Procedure
- DEPT: EOH (Environmental+Occupational Health), ENV (Environmental)

## 6-section structure (มาตรฐาน QA — บังคับ)

อ้างอิง `style-profiles/procedure-wi-sp.md` §Document structure:
1. วัตถุประสงค์ (Purpose)
2. ขอบเขต (Scope)
3. นิยามและตัวย่อ (Definitions)
4. ขั้นตอนการปฏิบัติงาน (Procedure)
5. เอกสารอ้างอิง (References)
6. บันทึก (Records)
+ Revision history table (ท้ายเอกสาร)

## TODO (รอ user สอน)
- [ ] ความแตกต่าง WI vs SP vs WP (depth)
- [ ] flowchart section 4 (mermaid vs image)
- [ ] record form codes (ENV-CFP-XXX)
- [ ] approval signature chain
- [ ] test generate จริง
