---
type: source
title: "AppSheet ENV App Data Dictionary (ActivatedSludge-29279640)"
slug: appsheet-env-datadict
date_ingested: 2026-05-04
original_file: raw/manual-input-appsheet-env-2026-05-04.md
tags: [appsheet, env, web-app, migration, wastewater, epidemiology, food-sanitation, safety]
---

# AppSheet ENV Data Dictionary

**ประเภท**: app-export (YAML via NotebookLM)
**วันที่**: 2026-05-04
**ผู้เขียน**: ผู้ใช้ (ระบบ AppSheet ActivatedSludge-29279640)

## ภาพรวม

เอกสารโครงสร้างแอป AppSheet "ENV" ที่ใช้งานอยู่ในกลุ่มงานอนามัยสิ่งแวดล้อมและควบคุมโรคติดต่อ ส่งออกจาก NotebookLM เป็น YAML เพื่อวิเคราะห์โครงสร้างสำหรับการ migrate ไปเป็น FastAPI+React บน Pi5

## ขนาดและสถิติ

| รายการ | จำนวน |
|--------|-------|
| Tables | 81 |
| Columns | 1,639 |
| Actions | 155 |
| Views | 128 |
| Slices | 10 |
| Format Rules | 12 |

## App Metadata

- **App ID**: ActivatedSludge-29279640
- **Short Name**: ENV
- **Version**: 3.001403
- **Default folder**: `/appsheet/data/ActivatedSludge-29279640`
- **Data locale**: th-TH

## Google Sheet Sources

| Google Sheet | Domain |
|-------------|--------|
| ข้อมูลน้ำประจำวัน | Wastewater + Admin |
| ข้อมูลหมากัด | Epidemiology (Rabies) |
| สุขาภิบาลอาหารและน้ำ2 | Food Sanitation |
| ข้อมูลคุณภาพน้ำประปา | Water Supply |
| fire_extinguisher | Safety (Fire) |
| Items | Safety (Emergency Light) |
| งานสวน | Admin (Job/GPS) |
| Patients | Epidemiology |

## ประเด็นหลัก

1. ระบบบำบัดน้ำเสียรายวัน — ซับซ้อนที่สุด: TDS, pH, DO×3, SV30, Free Chlorine, คำนวณพลังงาน
2. ระบาดวิทยา rabies PEP — บันทึกผู้ถูกสัตว์กัด, วัคซีน 5 เข็ม, lookup HN จาก sql_export
3. ตรวจสุขาภิบาลอาหาร — coliform 4 กลุ่ม (น้ำ/น้ำดื่ม/อาหาร/ผู้สัมผัสอาหาร)
4. ความปลอดภัย — QR scan ถังดับเพลิง + ไฟฉุกเฉิน + PDF report
5. GPS check-in — คำนวณระยะห่างจากโรงพยาบาล (Haversine)
6. Auto-complete ที่อยู่ — TambonID → อำเภอ/จังหวัด/ไปรษณีย์

## ข้อโต้แย้ง / สิ่งที่แตกต่างจาก wiki เดิม

- Session 1 สร้าง schema 5 ตารางเท่านั้น — จากการวิเคราะห์ YAML พบว่าต้องการอย่างน้อย 15-20 ตาราง PostgreSQL
- `sql_export 1-5` ใน AppSheet ไม่ใช่ backup แต่เป็น patient lookup table สำหรับ OCR HN
- บุคลากรใน AppSheet ใช้ `Employee_id` เป็น key (ไม่ใช่ email)

## สถานะ raw file

⚠️ `raw/manual-input-appsheet-env-2026-05-04.md` — บันทึกได้แค่ 2 chunks (partial)
ข้อมูล YAML เต็มยังไม่ได้บันทึกครบ — ต้องขอ re-export จากผู้ใช้ในครั้งต่อไปถ้าต้องการ schema ละเอียด

## หน้า Wiki ที่เกี่ยวข้อง

- [[synthesis/appsheet-to-webapp-pi5]] — แผน migration ทั้งหมด + 6 domain analysis
- [[entities/env/activated-sludge-system]] — ระบบบำบัดน้ำเสีย
- [[entities/env/rabies-pep-surveillance]] — ระบบเฝ้าระวัง rabies
