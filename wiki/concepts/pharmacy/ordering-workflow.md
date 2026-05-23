---
type: concept
tags: [pharmacy, workflow, ordering, line-message, validation, fuzzy-match, business-process]
sources: [sp-drugstore-2020-catalog, pharmacy-context]
created: 2026-04-29
updated: 2026-05-11
---

# Workflow การสั่งซื้อยา (Ordering Workflow)

## ปัญหาปัจจุบัน (Manual Process)

1. ลูกน้องเช็คสต็อก → ส่งรายการมาทาง **LINE** (ข้อความ/รูปภาพ)
2. รายชื่อยา **สะกดผิดบ้างถูกบ้าง** — ต้องตรวจสอบก่อนสั่ง
3. บางครั้งส่งเป็น **รูปภาพ** (ต้องใช้ OCR)
4. ต้องการ export เป็นข้อความสั่งซื้อส่งบริษัทขายส่ง

---

## Workflow เปรียบเทียบ

### ปัจจุบัน (Manual)

```
ลูกน้องส่ง LINE
      ↓
ผู้สั่ง (เจ้าของ) ตรวจสอบชื่อยาด้วยตา/ความจำ
      ↓ (เสี่ยงพลาด)
พิมพ์รายการส่งให้บริษัทขายส่ง
```

### เป้าหมาย (AI-assisted)

```
ลูกน้องส่ง LINE (ข้อความ หรือ รูปภาพ)
      ↓
[Web App หรือ Chat Interface]
      │── OCR ถ้าเป็นรูปภาพ
      │── วิเคราะห์ข้อความ (Claude API)
      │── fuzzy match กับ drug database
      ↓
แสดงรายการที่แก้ไขชื่อถูกต้องแล้ว
พร้อม flag รายการที่ไม่แน่ใจ
      ↓
เจ้าของ review + ใส่จำนวน
      ↓
Export เป็นข้อความสั่งซื้อ
```

---

## Technical Flow (ระดับระบบ)

```
┌──────────────────────┐
│  Input จากลูกน้อง    │
│  • ข้อความ / รูปภาพ  │
│  • เลขเครื่องสำอาง    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Validate ชื่อยา                  │
│  • Check drug-aliases.md          │
│  • Fuzzy match → ชื่อมาตรฐาน     │
│  • Find ใน sp_drugs_full_3760    │
└──────────┬───────────────────────┘
           │
     ┌─────▼──────┐
     │ ถ้าไม่เจอ  │ ──► Return ❌ "ไม่พบชื่อยา"
     └────────────┘
           │
           ▼ (พบแล้ว)
┌──────────────────────────────┐
│  Check Attributes            │
│  • Category code (A01, N02)  │
│  • Unit (box, vial, bottle)  │
│  • Supplier (S.P. 2020)      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Generate Order              │
│  • Show ให้ user ตรวจสอบ     │
│  • Allow edit quantity       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Export Options              │
│  • CSV (ใช้ Excel)           │
│  • Copy LINE (ส่งต่อ)        │
│  • JSON Patch (ระบบ)         │
└──────────────────────────────┘
```

---

## รูปแบบรายการที่ลูกน้องส่งมา (ตัวอย่าง)

```
ยาขาด วันนี้
- อม็อก 500 ขาด 5 กล่อง
- พารา 500 2 กล่อง
- ambrox 30 3 กล่อง
- cpm ขาด 2 กล่อง
- omeprazol 1 กล่อง
- Ibupofen 400 2กล่อง
```

---

## Fuzzy Match Logic

เมื่อได้รายการ จะทำการ:
1. **Normalize** — ตัวพิมพ์ใหญ่/เล็ก, ลบ space พิเศษ
2. **Fuzzy match** กับ drug database ด้วย Levenshtein distance
3. **Strength matching** — จับ 500mg, 30mg ออกมาเทียบ
4. **Confidence score** — แสดง % ความมั่นใจ

| Input จากลูกน้อง | Match | Confidence |
|----------------|-------|-----------|
| อม็อก 500 | AMOXYCILLIN 500mg | 95% |
| พารา 500 | PARACETAMOL 500mg | 98% |
| ambrox 30 | AMBROX 30mg | 99% |
| cpm | Chlorpheniramine | 90% |
| omeprazol | OMEPRAZOLE | 97% |
| Ibupofen 400 | IBUPROFEN 400mg | 94% |

---

## ตัวอย่าง End-to-End

### Input
```
ลูกค้า: "อมอก 500mg 2 กล่อง"
```

### Processing
```
1. Lookup: "อมอก" → drug-aliases["อมอก"] = "Amoxicillin"
2. Search: db.find("Amoxicillin 500mg")
3. Found: {
     code: "AMOXYCILLIN 500MG 20X10S",
     category: "A01",
     unit: "box",
     supplier: "S.P. 2020"
   }
4. Validate: ✅ Category OK, ✅ Unit OK, ✅ Supplier OK
```

### Output
```
ด้านผู้ใช้:
├─ ชื่อยา: AMOXYCILLIN 500MG 20X10S
├─ หมวดหมู่: A01 (ยา GI tract)
├─ หน่วย: box
├─ จำนวน: 2 (editable)
└─ Badge: ✅ (match)

Export:
├─ CSV: AMOXYCILLIN 500MG,A01,2
└─ LINE: "• AMOXYCILLIN 500MG 20X10S × 2"
```

---

## Flag & Warnings

| สถานการณ์ | Badge | Action |
|---------|-------|--------|
| พบยาตรง | ✅ | Export ได้ตรงไป |
| ชื่อคล้าย (fuzzy) | ⚠️ | แจ้ง "ไม่ใช่ exact match" |
| ไม่พบในฐานข้อมูล | ❌ | ขอชื่อใหม่ |
| Supplier ต่างแบรนด์ | ⚠️ | แจ้ง "กรุณาตรวจสอบ" |

---

## หน่วยสั่งซื้อ (Units)

| หน่วยที่ลูกน้องพูด | หน่วยจริง | ตัวอย่าง |
|-----------------|---------|--------|
| กล่อง | ก.10แผง / ก.50แผง | ขึ้นกับยา |
| แผง | แผง (1 แผง) | Amoxicillin 1 แผง = 10 เม็ด |
| ขวด | ก.1ขวด | น้ำเชื่อม/suspension |
| กระปุก | กระปุก | ยาเม็ด 500-1000 เม็ด |

---

## ความสัมพันธ์

- [[wiki/concepts/pharmacy/drug-aliases]] — การแมปชื่อยาสะกดผิด → ชื่อมาตรฐาน
- [[wiki/concepts/pharmacy/drug-validation]] — การตรวจสอบ category, unit, supplier
- [[wiki/concepts/pharmacy/fuzzy-match]] — algorithm Levenshtein + confidence score
- [[wiki/concepts/pharmacy/ui-design-pharmacy]] — ออกแบบ UI สำหรับ review + export
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่ชื่อยา
- [[wiki/synthesis/pharmacy-order-checker]] — web app design (FastAPI + React)

## แหล่งข้อมูล

- [[wiki/sources/sp-drugstore-2020-catalog]]
- [[wiki/sources/pharmacy-context]]
