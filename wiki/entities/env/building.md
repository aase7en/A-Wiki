---
type: entity
tags: [env, building, inspection, premises, module]
schema: building
module_id: MOD-BL
created: 2026-07-17
---

# ตรวจอาคารสถานที่ (Building Inspection)

## หน้าที่
บันทึกการตรวจสอบอาคารและสถานที่เป็นรอบ — พื้น, ฝาผนัง, ระบบไฟ, ระบบน้ำ, สุขภัณฑ์ — ถ้าพบปัญหาส่งต่อ repair_request อัตโนมัติ

## Schema
`building.inspection_round` (skeleton applied SCHEMA-1 2026-07-17)
- Columns: round_date, location_id, inspector, findings, issues_found, repair_needed, recorded_by
- Extended in **MOD-BL-a** (pending): round_type (monthly/quarterly/annual), checklist jsonb, photos text[], severity, assigned_to

## Cross-module
- `repair_needed=true` → seed `core.repair_request` (V1a layer)
- `photos` → `core.attachment` (DOC-3)

## กฎหมาย
- มาตรฐานกรมสาธารณสุข — การตรวจสอบสถานพยาบาล
- ระเบียบ รพ. สิ่งแวดล้อม

## WO
`docs/work-orders/MOD-BL-building.md`
