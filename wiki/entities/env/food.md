---
type: entity
tags: [env, food, sanitation, coliform, lab-test, module]
schema: food
module_id: MOD-FO
created: 2026-07-17
---

# สุขาภิบาลอาหาร (Food Sanitation / Coliform)

## หน้าที่
บันทึกผลตรวจทางห้องปฏิบัติการความสะอาดน้ำและอาหาร — total coliform, E. coli, fecal coliform — เพื่อยืนยันความปลอดภัยและรายงานต่อหน่วยงานควบคุม

## ⚠️ PHI boundary
การตรวจ coliform ของ รพ.อุทัย = **ตรวจน้ำ/อาหาร/สิ่งแวดล้อม** — ไม่ใช่ patient sample
ถ้าอนาคตมี patient-adjacent sample → **ห้าม route ผ่าน AI** (ZCode/GLM อยู่ใต้กฎหมายจีน)

## พารามิเตอร์ที่ตรวจ
- **Total coliform** — MPN/100ml
- **E. coli** — MPN/100ml (presence/absence)
- **Fecal coliform** — MPN/100ml
- **sample_type**: น้ำประปา / น้ำบาดาล / อาหาร / ผัก / น้ำแข็ง

## Schema
`food.lab_test` (skeleton applied SCHEMA-1 2026-07-17)
- Columns: sample_date, sample_type, test_type, result, reported_date, technician, recorded_by
- Extended in **MOD-FO-a** (pending): sample_point, mpn_value, reagent_used jsonb, follow_up_action

## Cross-module
- **Reagent stock decrement**: AFTER INSERT บน lab_test → อัปเดต `chemical.movement` (direction='out')
- Sample จาก `water_supply` อาจส่งมาวิเคราะห์เพิ่ม

## กฎหมาย/มาตรฐาน
- ประกาศกระทรวงสาธารณสุข ฉบับที่ 135 — มาตรฐานน้ำดื่ม
- มาตรฐาน APHA/AWWA — Standard Methods for the Examination of Water and Wastewater
- กรมวิทยาศาสตร์การแพทย์ — แนวทางการตรวจ coliform

## Carbon scope
**Scope 3** — waste disposal ของ reagent หมดอายุ + sample ปนเปื้อน

## WO
`docs/work-orders/MOD-FO-food.md`
