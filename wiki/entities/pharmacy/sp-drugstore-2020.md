---
type: entity
category: supplier
tags: [pharmacy, supplier, thai]
sources: [pharmacy-context]
created: 2026-04-30
updated: 2026-04-30
---

# S.P. Drugstore 2020 (ผู้จัดจำหน่าย)

**ประเภท**: Wholesale Supplier  
**สถานะ**: ✅ ปัจจุบัน  
**จำนวน SKU**: 3,760  

## ภาพรวม

บริษัทจัดจำหน่ายยา เครื่องสำอาง และสินค้าสุขภาพในประเทศไทย เป็นผู้จัดจำหน่ายหลักของร้านยาภูฟาร์มาซี

## ฐานข้อมูล

### Primary (sp_drugs_full_3760.json)
- **จำนวน**: 3,760 รายการ
- **ครอบคลุม**: ยา + เครื่องสำอาง + อาหารเสริม + สินค้าอื่นๆ
- **ขนาด**: ~5-10 MB JSON
- **โครงสร้าง**:
  - `code`: รหัสสินค้า (เช่น "OMEPRAZOLE GPO 10x10s")
  - `category_code`: รหัสหมวดหมู่ (A01, A02, N02, etc.)
  - `category_name`: ชื่อหมวดหมู่ไทย
  - `name`: ชื่อสินค้า
  - `strength`: ความเข้มข้น (mg, mcg, %)
  - `unit`: หน่วยสั่งซื้อ (box, vial, bottle)
  - `supplier`: ชื่อผู้จัดจำหน่าย

### Reference (sp_drugs_medications_2895.json)
- **จำนวน**: 2,895 รายการ
- **ใช้สำหรับ**: ตรวจสอบหมวดหมู่ยาที่ถูกต้อง
- **หมายเหตุ**: ใช้เมื่อต้องกรองเฉพาะยาเท่านั้น

## Category Code Mapping (ATC-based)

| Code | ชื่อหมวดหมู่ |
|------|------------|
| A01 | ยาแช่งชา/ลำไส้ |
| A02 | ยาลดกรด |
| A04 | ยาต้านอาการคลื่นไส้ |
| N02 | ยาแก้ปวด |
| N07 | ยาระงับประสาท |
| R05 | ยาแก้ไอ |
| R06 | ยาต้านแพ้ |
| S01 | ยาหยอดตา |
| D07 | ยาทาผิว |
| และอื่นๆ... | ... |

## ความเกี่ยวข้อง

- [[wiki/entities/pharmacy/pharmacy-business]] — ร้านยา
- [[wiki/entities/pharmacy/drug-database]] — ฐานข้อมูลยา
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]]
