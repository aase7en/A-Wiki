---
type: entity
tags: [env, water-supply, groundwater, potable-water, module]
schema: water_supply
module_id: MOD-WS
created: 2026-07-17
---

# น้ำประปาบาดาล (Water Supply / Groundwater)

## หน้าที่
บันทึกผลตรวจคุณภาพน้ำประปาบาดาลของ รพ.อุทัย รายวัน เพื่อรายงานต่อหน่วยงานควบคุมตามกฎหมาย และตรวจสอบความปลอดภัยก่อนใช้บริโภค

## พารามิเตอร์ที่ตรวจ
- **pH** (6.5–8.5)
- **คลอรีนอิสระ (free chlorine residual)** 0.2–1.0 mg/L
- **ความขุ่น (turbidity)** ≤ 5 NTU
- **Total coliform** ไม่พบ / พบ (MPN/100ml)
- **Fecal coliform / E. coli** ไม่พบ
- **เหล็ก (Fe), แมงกานีส (Mn), ความกระด้าง (hardness), TDS** — periodic

## Schema
`water_supply.daily_check` (skeleton applied SCHEMA-1 2026-07-17)
- Columns extended in **MOD-WS-a** (pending)

## กฎหมาย/มาตรฐานอ้างอิง
- ประกาศกระทรวงสาธารณสุข ฉบับที่ 135 (พ.ศ. 2534) — มาตรฐานคุณภาพน้ำดื่ม
- กรมควบคุมโรค — แนวทางการเฝ้าระวังคุณภาพน้ำประปาบาดาล

## Cross-module
- ผลตรวจ coliform ส่งต่อไป module `food` (lab_test) สำหรับการวิเคราะห์เชิงลึก
- ใช้ reagent จาก `chemical` module (auto-decrement TBD)

## WO
`docs/work-orders/MOD-WS-water-supply.md` (env-wastewater-webapp repo)
