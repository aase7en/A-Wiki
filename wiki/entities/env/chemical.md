---
type: entity
tags: [env, chemical, inventory, chlorine, sub-store, module]
schema: chemical
module_id: MOD-CH
created: 2026-07-17
---

# คลังเคมีภัณฑ์ย่อย (Chemical Sub-store)

## หน้าที่
บันทึกการรับเข้า/จ่ายออกของเคมีภัณฑ์ที่ใช้ในระบบสิ่งแวดล้อม — คลอรีน (ฆ่าเชื้อน้ำเสีย), สารส้ม, ด่างทับทิม, น้ำยาเอนไซม์ — พร้อมคำนวณยอดคงเหลืออัตโนมัติ

## เคมีหลัก (ตัวอย่าง)
- **คลอรีนเหลว** — ฆ่าเชื้อน้ำเสียก่อนปล่อยลงสู่แม่น้ำ
- **สารส้ม** — จับตะกอนในน้ำ
- **ด่างทับทิม (KMnO₄)** — ฆ่าเชื้อ, กำจัดกลิ่น
- **น้ำยาเอนไซม์** — ย่อยสลายสารอินทรีย์
- **HCl, NaOH** — ปรับ pH

## Schema
`chemical.movement` (skeleton applied SCHEMA-1 2026-07-17)
- Columns: movement_date, chemical_name, direction (in/out), quantity, unit, balance_after, purpose, recorded_by
- Optional `chemical.master` (pending MOD-CH-a) — catalog + auto-computed balance

## Cross-module
- **Balance trigger**: AFTER INSERT → update `chemical.master.current_balance` (TBD)
- **food.lab_test** auto-decrement เมื่อใช้ reagent
- **wastewater.chlorine_used** ส่งต่อมาจาก daily form เดิม

## กฎหมาย/มาตรฐาน
- พ.ร.บ. วัตถุอันตราย พ.ศ. 2535
- ประกาศกระทรวงอุตสาหกรรม — การจัดเก็บสารเคมี
- Material Safety Data Sheet (MSDS) — ต้องมีต่อ chemical แต่ละตัว

## Carbon scope
**Scope 1/3** — kgCO₂e คำนวณจาก `carbon.emission_factor` matching chemical_name (production + disposal)

## WO
`docs/work-orders/MOD-CH-chemical.md`
