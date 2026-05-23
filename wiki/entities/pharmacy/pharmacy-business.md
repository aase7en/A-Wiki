---
type: entity
category: business
tags: [pharmacy, retail, thai-local]
sources: [pharmacy-context]
created: 2026-04-30
updated: 2026-04-30
---

# ภูฟาร์มาซี (Pharmacy Business)

**ประเภท**: ร้านขายยา  
**สถานี**: ✅ ดำเนินการ  
**ผู้ดูแล**: Aase7en  

## ภาพรวม

ร้านขายยาขนาดเล็ก ตั้งอยู่ในสมุดรายชื่อเครื่องสำอาง โดยขาย ยา เครื่องสำอาง อาหารเสริม และสินค้าสุขภาพอื่นๆ จากผู้จัดจำหน่ายหลัก **S.P. Drugstore 2020** (3,760 SKU)

## ธุรกิจปัจจุบัน

### สมุดรายชื่อ (Catalog)
- **ฐานข้อมูลหลัก**: sp_drugs_full_3760.json
  - 3,760 รายการ (ยา + เครื่องสำอาง + อาหารเสริม + อื่นๆ)
  - แหล่งมา: S.P. Drugstore 2020

- **ฐานข้อมูลอ้างอิง**: sp_drugs_medications_2895.json
  - 2,895 รายการ (ยา เฉพาะ)
  - ใช้สำหรับตรวจสอบประเภท

### Workflow ปัจจุบัน
1. ลูกค้ากลับ LINE → ส่งเลขเครื่องสำอาง/ชื่อยา (ข้อความหรือรูปภาพ)
2. ตรวจสอบชื่อยา → match กับรายการในฐานข้อมูล
3. Validate category code, unit, supplier
4. Export order → CSV / Copy LINE

## ความท้าทาย

- ชื่อยาสะกดผิด (Amoxycillin vs amox, omeprazol vs ome)
- ต้องใช้ fuzzy matching + drug aliases reference
- OCR จากรูปภาพ (ยังไม่ทำ)

## โอกาสพัฒนา

### ระยะสั้น
- Telegram/Line bot ที่ตรวจสอบยาอัตโนมัติ
- Drug aliases database ที่ครอบคลุม

### ระยะยาว
- **Web App (FastAPI + React)** บน Raspberry Pi 5
  - Interactive form ตรวจสอบและปรับแต่งรายการ
  - Claude API ขำสำหรับ OCR + drug validation
  - Database sync กับ supplier
- Integration สต็อกจริง (inventory)

## ความเกี่ยวข้อง

- [[wiki/entities/pharmacy/sp-drugstore-2020]] — ผู้จัดจำหน่ายหลัก
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่ยา
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ
- [[wiki/synthesis/pharmacy-web-app-roadmap]] — แผนการพัฒนา web app

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]] — บริบทร้านยา
- [[wiki/sources/pharmacy-ui-instructions]] — ออกแบบ UI app
