---
type: entity
tags: [env, garden, landscaping, grass-cutting, module]
schema: garden
module_id: MOD-GA
created: 2026-07-17
---

# งานคนสวน / ตัดหญ้า (Garden / Landscaping)

## หน้าที่
บันทึกการปฏิบัติงานคนสวนในแต่ละรอบ — ตัดหญ้า, ตัดแต่งไม้, กำจัดวัชพืช — พร้อมเชื้อเพลิงที่ใช้ (น้ำมัน 2-stroke) เพื่อคำนวณ carbon footprint

## Schema
`garden.work_round` (skeleton applied SCHEMA-1 2026-07-17)
- Columns: round_date, location_id, work_type, area_sqm, worker_count, fuel_used_l, recorded_by
- Extended in **MOD-GA-a** (pending): duration_hours, equipment_used, waste_collected_kg, photo_path

## ประเภทงาน
- ตัดหญ้า
- ตัดแต่งไม้
- กำจัดวัชพืช
- อื่นๆ (ปลูก, บำรุง)

## Carbon scope
**Scope 1** — fuel_used_l × diesel/gasoline factor; ส่งไป `carbon.v_unified_co2e`

## WO
`docs/work-orders/MOD-GA-garden.md`
