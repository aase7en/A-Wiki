---
type: entity
tags: [env, safety, fire, emergency-lighting, extinguisher, module]
schema: safety
module_id: MOD-FS
created: 2026-07-17
---

# ความปลอดภัย (Fire Safety / Emergency Lighting)

## หน้าที่
บันทึกการตรวจสอบระบบความปลอดภัยเดือนละครั้ง (ประพจำ) — ถังดับเพลิง, ไฟส่องสว่างฉุกเฉิน, สัญญาณเตือนอัคคีภัย — ตามที่กฎหมายกำหนด

## Schema
`safety.monthly_check` (skeleton applied SCHEMA-1 2026-07-17)
- Columns: check_date, location_id, extinguisher_inspected, exit_light_functional, issues_found, recorded_by
- Extended in **MOD-FS-a** (pending): extinguisher_count, extinguisher_expired_count, exit_light_count, fire_alarm_tested, sprinkler_tested, apd_aed_checked, next_check_due

## รอบตรวจที่บังคับ (legal requirement)
- **ประพจำดับเพลิง** — ทุกเดือน
- **ไฟส่องสว่างฉุกเฉิน** — ทุกเดือน
- **ระบบสัญญาณเตือนอัคคีภัย** — ทุก 6 เดือน (test)
- **AED** — ทุกเดือน (ตรวจสภาพ/แบตเตอรี่)

## กฎหมาย/มาตรฐาน
- พ.ร.บ. ป้องกันอัคคีภัย พ.ศ. 2542
- ประกาศกระทรวงมหาดไทย — ระบบป้องกันอัคคีภัย สำหรับสถานพยาบาล
- มาตรฐาน NFPA 10 (extinguisher) / NFPA 101 (life safety)

## Cross-module
- ปัญหาที่พบ → seed `core.repair_request`
- รอบตรวอเลยกำหนด → trigger alerts via V3a

## WO
`docs/work-orders/MOD-FS-fire-safety.md`
