---
name: a-doc-procurement
description: "PR/QT/PO flow — ขอซื้อ/เสนอราคา/สั่งซื้อ/เบิกจ่าย 68. STUB รอ user สอน. Pattern from: _uThaiHos/05_Finance_Admin/{01_PR,02_QT,03_Disbursement,04_Procurement}. Trigger: 'ขอซื้อ', 'PR', 'เสนอราคา', 'QT', 'PO', 'เบิกจ่าย', 'จัดซื้อ'"
version: 0.1.0
author: A-Wiki (stub)
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
---

# A-Doc Type: Procurement (PR/QT/PO flow)

> **STUB** — flow 4 ขั้นตอน รอ user สอน template แต่ละ stage

## Flow (4 stages)

```
PR (ขอซื้อ)  →  QT (เสนอราคา)  →  PO (สั่งซื้อ)  →  เบิกจ่าย 68
บันทึกข้อความ     ใบเสนอราคาจาก      ใบสั่งซื้อ/ใบกำกับ     e-budgeting
                 บริษัท                ภาษี
```

## Stage 1: PR (Purchase Request)
**Output**: บันทึกข้อความขอซื้อ
**Sub-type**: เชื่อมโยง `types/memo/` (variant ขอซื้อ)
**ไฟล์ตัวอย่าง**:
- `20260105_ขอซื้อกระจก.docx`
- `20260305_690503_ขอซื้อบ่อบำบัด.pdf`
- `20260624_ขอซื้อ probe.pdf`

## Stage 2: QT (Quotation)
**Output**: เก็บใบเสนอราคาจาก ≥3 บริษัท (มาตรฐานภาครัฐ)
**ไฟล์ตัวอย่าง**:
- `20250417_ใบเสนอราคา ORP HANNA.pdf`
- `20250507_บริษัทBB_Compare Cl2HN-ORP BB.pdf.pdf` (เปรียบเทียบ)

## Stage 3: PO (Purchase Order)
**Output**: ใบสั่งซื้อ + ใบกำกับภาษี

## Stage 4: เบิกจ่าย 68
**Output**: เอกสาร e-budgeting ปีงบ 68 (2568)

## ไฟล์ตัวอย่างเพิ่มเติม

| ไฟล์ | stage |
|---|---|
| `20250515_KTB_Presentation_User_Update.pdf` | เบิกจ่าย (KTB) |
| `20250515_PCA310-2 ลดราคา.pdf` | ต่อรองราคา |

## Style profile
✅ `style-profiles/gov-letter-standard.md` (PR/บันทึก) + xlsx (QT เปรียบเทียบ)

## TODO (รอ user สอน)
- [ ] PR template (ขอซื้อบ้าง/ครุภัณฑ์/วัสดุ)
- [ ] QT comparison table (xlsx)
- [ ] PO template + เลขประจำตัวผู้เสียภาษี
- [ ] เบิกจ่าย 68 form (e-budgeting)
- [ ] test generate จริง
