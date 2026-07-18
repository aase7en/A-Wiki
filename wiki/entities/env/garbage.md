---
type: entity
tags: [env, waste, garbage, disposal, module]
schema: garbage
module_id: MOD-WA
created: 2026-07-17
---

# ขยะและการเก็บขยะ (Waste Collection)

## หน้าที่
บันทึกปริมาณขยะที่เก็บ แยกตามประเภท (ทั่วไป/ติดเชื้อ/รีไซเคิล/เคมี) และเส้นทางกำจัด — รายงานต่อหน่วยงานตามกฎหมาย

## ประเภทขยะ
- **ทั่วไป (general)** — ส่ง ทกจ. / บริษัทเอกชน
- **ติดเชื้อ (infectious)** — เผา / บริษัทเฉพาะทาง
- **รีไซเคิล (recyclable)** — ขาย / บริจาค
- **เคมี (chemical)** — ส่งผ่าน chemical disposal route

## Schema
`garbage.collection_log` (skeleton applied SCHEMA-1 2026-07-17)
- Columns extended in **MOD-WA-a** (pending)
- Legacy data migration **MIG-WA** (blocked — รอ user export AppSheet CSV)

## กฎหมาย/มาตรฐาน
- พ.ร.บ. ส่งเสริมและรักษาคุณภาพสิ่งแวดล้อมแห่งชาติ พ.ศ. 2535
- ประกาศกระทรวงสาธารณสุข — การกำจัดขยะติดเชื้อจากสถานพยาบาล
- มาตรฐาน รพ. สิ่งแวดล้อม (Green Hospital)

## Carbon scope
**Scope 3** — waste-to-landfill emission factor × weight_kg

## WO
`docs/work-orders/MOD-WA-waste.md`
