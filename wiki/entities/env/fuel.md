---
type: entity
tags: [env, fuel, fleet, diesel, gasoline, lpg, module]
schema: fuel
module_id: MOD-FU
created: 2026-07-17
---

# น้ำมันเชื้อเพลิง (Fuel / Fleet)

## หน้าที่
บันทึกการจ่ายน้ำมันของยานพาหนะและเครื่องจักร รวมถึง meter reading ก่อน/หลัง เพื่อตรวจสอบ delta และคำนวณ carbon footprint

## ประเภทเชื้อเพลิง
- **diesel** — รถบรรทุก, เครื่องกำเนิดไฟฟ้า
- **gasoline** — รถเก๋ง, จักรยานยนต์
- **lpg** — รถบรรทุกบางรุ่น, เครื่องทำความร้อน
- **other** — น้ำมันหล่อลื่น, น้ำมันเครื่องบางประเภท

## Schema
`fuel.dispense_log` (skeleton applied SCHEMA-1 2026-07-17)
- Columns extended in **MOD-FU-a** (pending)
- Legacy data migration **MIG-FU** (blocked — รอ user export AppSheet CSV)
- Helper `computeDelta(meter_before, meter_after)` — เตือนถ้า delta ≠ litres

## กฎหมาย/มาตรฐาน
- กฎกระทรวง ควบคุมการจัดเก็บเชื้อเพลิง — มาตรการความปลอดภัย
- มาตรฐาน EPA / PTT สำหรับ greenhouse gas reporting

## Carbon scope
**Scope 1** — direct combustion; kgCO₂e/litre × factor ใน `carbon.emission_factor`

## WO
`docs/work-orders/MOD-FU-fuel.md`
