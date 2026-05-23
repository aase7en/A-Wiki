---
type: concept
tags: [pharmacy, ui-design, web-app, interactive]
sources: [pharmacy-ui-instructions]
created: 2026-04-30
updated: 2026-04-30
---

# UI Design for Pharmacy App (v3)

## ภาพรวม

Interactive form สำหรับตรวจสอบ, แก้ไข และ export รายการสั่งซื้อยา ออกแบบให้ใช้ง่ายและ support การเปลี่ยนแปลงข้อมูลแบบ real-time

## 6 Component หลัก

### 1. 📝 Editable Name Input
- ช่อง input แสดงชื่อยา + option edit
- Auto-validate ตรวจสอบ fuzzy match ขณะพิมพ์
- ถ้าไม่เจอ → suggestions จาก drug-aliases
- Badge indicator:
  - ✅ exact match
  - ⚠️ fuzzy match (แจ้งเตือน)
  - ❌ not found

### 2. 🔄 DB Update / JSON Patch Panel
- สำหรับเพิ่มยาใหม่ที่ยังไม่มีในฐานข้อมูล
- Generate JSON entry พร้อม:
  - `code`: NEW-{idx}
  - `category_code`: (select dropdown)
  - `category_name`: auto-fill from CAT_MAP
  - `name`: ชื่อสินค้า
  - `strength`: ความเข้มข้น (mg, mcg, %)
  - `unit`: box, vial, bottle
  - `supplier`: S.P. 2020
  - `_note`: หมายเหตุเพิ่มเติม
- Button "Copy JSON Patch" → copy array ของ entries

### 3. 📊 Category Code Mapping (CAT_MAP)
| category_code | category_name |
|---|---|
| A01 | ยาแช่งชา/ลำไส้ |
| A02 | ยาลดกรด |
| N02 | ยาแก้ปวด |
| R06 | ยาต้านแพ้ |
| S01 | ยาหยอดตา |
| ... | ... |

### 4. 📤 Export / Copy OPTIONS

#### Export CSV
- ไฟล์ `.csv` UTF-8 BOM (Excel compatible)
- Columns: code, category_code, category_name, name, strength, unit, supplier

#### Copy LINE (v3 — Clean Format)
```
🔊 รายการสั่งซื้อยา — ร้านขายยา ภูฟาร์มาซี
================================

[A02 ยาลดกรด]
• OMEPRAZOLE GPO 10x10s ฿.10อัน × 6
• MIRACID 20mg 2x7s ฿.2อัน × 12

[R06 ยาต้านแพ้]
• CODIPHEN 50mg 1x10s ฿.1อัน × 20

================================
รวม 3 รายการ
```

**Show only qty > 0**, organized by category_code, clean format

#### JSON Patch (ระบบ)
- สำหรับ API update database
- Format: array ของ objects

### 5. 🔢 Quantity Editor
- Number input field สำหรับแก้ไขจำนวน
- Button "ล้างจำนวน" reset → 0
- Real-time update preview

### 6. 🎫 Badge & Status System

| Status | Badge | ความหมาย |
|--------|-------|---------|
| Match DB | ✅ | พบยาตรง |
| Fuzzy match | ⚠️ | ชื่อคล้าย, ตรวจสอบเพิ่มเติม |
| Not found | ❌ | ไม่พบในฐานข้อมูล |
| Info | ℹ️ | หมายเหตุ (supplier, category) |

## Workflow (End-to-End)

```
1. User พิมพ์ "omeprazol" (typo)
   ↓
2. UI ตรวจสอบ → ⚠️ "ไม่เป็น exact match"
   ↓
3. AI lookup aliases → "omeprazol" = "Omeprazole"
   ↓
4. Search DB → พบ "OMEPRAZOLE GPO 20mg"
   ↓
5. Show ✅ "match" + สามารถแก้ qty
   ↓
6. User click "Copy LINE" → copy formatted text to clipboard
   ↓
7. User ส่งต่อ LINE ลูกค้า
```

## Technology Stack (อนาคต)

- **Frontend**: React.js
- **Backend**: FastAPI
- **Database**: sp_drugs_full_3760.json (initial), ค่อยๆ migrate to SQLite/MySQL
- **Host**: Raspberry Pi 5
- **OCR**: Claude API (image recognition)

## ความเกี่ยวข้อง

- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ
- [[wiki/concepts/pharmacy/drug-validation]] — ตรวจสอบชื่อยา
- [[wiki/concepts/pharmacy/drug-aliases]] — แมปชื่อยา
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-ui-instructions]]
