---
type: source
title: "เอสพีดรักสโตร์ 2020 — Drug Catalog 3,760 รายการ"
slug: sp-drugstore-2020-catalog
date_ingested: 2026-04-29
original_file: raw/pharmacy/sp_drugs_full_3760.json
tags: [pharmacy, drug-catalog, sp-drugstore, drug-database]
---

# เอสพีดรักสโตร์ 2020 — Drug Catalog

**ประเภท**: ฐานข้อมูลสินค้า (JSON)
**วันที่**: 2020 (catalog ปี 2563)
**ผู้จัดทำ**: เอสพีดรักสโตร์ 2020 (SP Drugstore 2020)

## ประเด็นหลัก

1. **3,760 รายการ** — ครอบคลุมยา + เครื่องสำอาง + อาหารเสริม + สินค้าอื่นๆ
2. **ฐานข้อมูลหลักสำหรับ Pharmacy domain** — ใช้ตรวจสอบรายการสั่งซื้อจากร้าน ภูฟาร์มาซี
3. **มีทั้งชื่อสามัญและชื่อการค้า** — เช่น Paracetamol, SARA, TYLENOL, ASUMOL
4. **Sub-dataset**: `sp_drugs_medications_2895.json` — กรองเฉพาะยา 2,895 รายการ (ไม่รวมเครื่องสำอาง/อาหารเสริม)

## ข้อมูลที่น่าสนใจ

- หมวดหมู่ยาที่พบบ่อยครอบคลุม ATC Levels J01, N02, R05, R06, A02, C02, A11, D07, D08, M01
- ชื่อยาในฐานข้อมูลมีทั้งภาษาอังกฤษ ย่อ (AMK, CPM) และบางรายการเป็นชื่อการค้าภาษาไทย
- ใช้เป็น ground truth สำหรับ fuzzy matching เมื่อรับ input จาก LINE message

## ข้อจำกัด

- เป็น catalog ปี 2563 — ยาหรือราคาอาจเปลี่ยนแปลง
- ไม่รวมยาที่ต้องใบสั่งแพทย์บางประเภท
- ราคาใน catalog อาจต่างจากราคาปัจจุบัน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[wiki/concepts/pharmacy/drug-classification]] — ATC codes และหมวดยา
- [[wiki/concepts/pharmacy/ordering-workflow]] — workflow สั่งซื้อ
- [[wiki/concepts/pharmacy/fuzzy-match]] — การ match ชื่อยาสะกดผิด
- [[wiki/synthesis/pharmacy-order-checker]] — ระบบ AI ตรวจสอบรายการยา
