---
name: a-business
description: "งานธุรกิจส่วนตัว — stub รอ user สอนบริบทเพิ่ม. ปัจจุบันชี้ไปยัง: finance-pipeline (investment analysis), project-flow-ops, agent-sort. เมื่อ user ใช้ครั้งแรก → ถามบริบทธุรกิจเพื่ออัพเดท SKILL.md ให้ specific. Trigger: 'ธุรกิจ', 'business', 'ลงทุน', 'โครงการส่วนตัว'."
version: 0.1.0
author: A-Wiki
domain: [business, trader]
lifecycle_phase: meta
category: pipeline
agents: [all]
invocation: manual
---

# A-Business — งานธุรกิจส่วนตัว (STUB)

> **STUB** — รอ user สอนบริบทเฉพาะ ค่อยขยาย
> Pattern เดียวกับ `/A-Doc` — เริ่มจาก chain canonical skills → เพิ่ม subskill เฉพาะทางทีหลัง

## ปัจจุบันทำอะไรได้ (via existing canonical skills)

| งาน | Skill ที่เรียก |
|---|---|
| วิเคราะห์การลงทุน (stock/crypto) | `finance-pipeline` (3-stage: data → analyst → debater) |
| จัดการโครงการ | `project-flow-ops` |
| Sort / ตัดสินใจหลายทาง | `agent-sort` |
| Risk review (trading) | `prediction-market-risk-review` + `ito-trade-planner` |
| Monte Carlo quant | `monte-carlo-quant-analysis` |

## First-use protocol

เมื่อ user เรียก `/A-Business` ครั้งแรก ให้ถาม `grill-with-docs`:
1. ประเภทธุรกิจ? (service / product / trading / อสังหา / etc.)
2. งานประจำคืออะไร? (ประจำวัน / สัปดาห์ / เดือน)
3. Deliverable หลัก? (report / plan / contract / analysis)
4. เครื่องมือปัจจุบัน? (spreadsheet / app / manual)

จากคำตอบ → อัพเดท SKILL.md ฉบับนี้ + เพิ่ม `subskills/` เฉพาะทาง

## ไอเดียร์ subskill ในอนาคต (รอสอน)

```
a-business/
└── subskills/           ← สร้างเมื่อ user สอน
    ├── _template/
    ├── accounting/      ← บัญชี/ภาษี
    ├── invoice/         ← ใบแจ้งหนี้/ใบกำกับ
    ├── proposal/        ← proposal/quote ลูกค้า
    └── ...
```

## Invocation

```
/A-Business [task description]
```
