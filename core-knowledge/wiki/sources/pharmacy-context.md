---
type: source
title: "Pharmacy Context & Business Overview"
slug: pharmacy-context
date_ingested: 2026-04-30
original_file: raw/pharmacy-context.md
tags: [pharmacy, business, workflow]
---

# Pharmacy Context & Business Overview

**ประเภท**: Business Context  
**วันที่ Ingest**: 2026-04-30  

## ประเด็นหลัก

1. **ร้านยา ภูฟาร์มาซี** — ขาย ยา, เครื่องสำอาง, อาหารเสริม
   - ตั้งอยู่ในสมุดรายชื่อเครื่องสำอาง
   - ผู้จัดจำหน่ายหลัก: **S.P. Drugstore 2020** (3,760 SKU)

2. **Workflow สั่งซื้อ** — 4 ขั้นตอน:
   - ลูกค้ากลับ LINE (ข้อความ/รูปภาพ)
   - ระบบตรวจสอบชื่อยา → match กับฐานข้อมูล
   - Validate category code, unit, supplier
   - Export order (CSV / Copy LINE)

3. **ฐานข้อมูล**:
   - **Primary**: sp_drugs_full_3760.json — 3,760 รายการ
   - **Reference**: sp_drugs_medications_2895.json — 2,895 ยา (กรองเฉพาะ)

## ข้อมูลที่น่าสนใจ

| ประเด็น | รายละเอียด |
|--------|-----------|
| ความท้าทาย | ชื่อยาสะกดผิด (Amoxycillin vs amox, omeprazol vs ome) |
| โสหล้วน | ต้องใช้ fuzzy matching + drug aliases reference |
| ตัวเลขพื้นฐาน | 3,760 SKU ครอบคลุม ยา + เครื่องสำอาง + อาหารเสริม + สินค้าอื่น |

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — เป็นข้อมูลเพิ่มเติมเพื่อสร้าง web app สำหรับธุรกิจยา

## หน้า Wiki ที่ได้รับการอัปเดต

- [[wiki/entities/pharmacy/pharmacy-business]]
- [[wiki/entities/pharmacy/sp-drugstore-2020]]
- [[concepts/pharmacy/ordering-workflow]]
- [[wiki/concepts/pharmacy/drug-aliases]]
- [[index-pharmacy]]
