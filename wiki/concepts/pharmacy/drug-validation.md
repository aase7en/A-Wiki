---
type: concept
tags: [pharmacy, validation, quality-assurance]
sources: [pharmacy-context, drug-aliases-reference]
created: 2026-04-30
updated: 2026-04-30
---

# Drug Validation — ตรวจสอบความถูกต้อง

## นิยาม

Drug Validation คือกระบวนการตรวจสอบว่า**ชื่อยา, หมวดหมู่, หน่วยสั่งซื้อ, ผู้จัดจำหน่าย** ถูกต้องและ consistent กับฐานข้อมูล ก่อนปล่อยออกเป็นรายการสั่งซื้อ

## ขั้นตอนการ Validate

### 1. Name Validation
```
Input: "omeprazol"
↓
Check exact match in DB → No
Check aliases.md → Yes! "Omeprazole"
Check fuzzy match → 96% match with "OMEPRAZOLE GPO 20mg"
✅ Status: VALID
```

### 2. Category Validation
```
Drug name: "Amoxicillin"
Found in DB: category_code = "A01"
Expected: "ยาแช่งชา/ลำไส้"
✅ Status: VALID
```

### 3. Unit Validation
```
Drug: "AMOXICILLIN 500MG 20X10S"
Unit in DB: "box"
✅ Status: VALID
```

### 4. Supplier Validation
```
Supplier: "S.P. Drugstore 2020"
Match DB: ✅ Yes
Status: ✅ VALID
```

### 5. Quantity Validation
```
User input: "5" (boxes)
Check: > 0 and is integer
✅ Status: VALID
```

## Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| **Name** | Must match DB (exact or fuzzy > 80%) | "amoxil" → "Amoxicillin" ✅ |
| **Category** | Must be in ATC code list (A01-S01) | "A02" ✅, "Z99" ❌ |
| **Unit** | Must be in unit list (box, vial, bottle) | "box" ✅, "kg" ❌ |
| **Supplier** | Must be "S.P. Drugstore 2020" | ✅ (only one supplier currently) |
| **Quantity** | Must be positive integer | "5" ✅, "0" ❌, "-2" ❌, "5.5" ❌ |

## Error Cases & Responses

### Case 1: Drug name not found
```
Input: "xyzabc"
↓
Validation Result: ❌ INVALID
Message: "ไม่พบชื่อยา 'xyzabc' ในระบบ"
Suggestion: "ตรวจสอบการสะกด หรือกลับมาลองใหม่"
```

### Case 2: Fuzzy match (ambiguous)
```
Input: "aspirin"
Found matches:
  • ASPIRIN 100MG (A11 - อาหารเสริม)
  • ASPIRIN 325MG (N02 - ยาแก้ปวด)
↓
Status: ⚠️ WARNING
Message: "พบหลายรายการ กรุณาเลือก:"
Action: Show list, user picks one
```

### Case 3: Invalid quantity
```
Input: qty = "0"
↓
Status: ❌ INVALID
Message: "จำนวนต้องมากกว่า 0"
```

### Case 4: Supplier mismatch (future)
```
Input: "Omeprazole" from supplier X
Drug DB: Only from "S.P. Drugstore 2020"
↓
Status: ⚠️ WARNING
Message: "ยาชนิดนี้มีเฉพาะจาก S.P. Drugstore 2020"
Action: Confirm or reject
```

## Flags & Indicators

| Badge | Meaning | Action |
|-------|---------|--------|
| ✅ | All validations passed | Proceed to export |
| ⚠️ | Warning (fuzzy match, similar names) | Ask user to confirm |
| ❌ | Invalid (not found, wrong qty) | Block, ask for correction |
| ℹ️ | Info (category, supplier info) | Display, user can ignore |

## Validation Workflow

```
┌────────────────────────┐
│ User inputs drug list  │
└───────┬────────────────┘
        │
        ▼
┌────────────────────────┐
│ For each drug:         │
│  1. Name validation    │
│  2. Category check     │
│  3. Unit check         │
│  4. Supplier check     │
│  5. Qty check          │
└───────┬────────────────┘
        │
        ▼
┌────────────────────────┐
│ All valid? (✅ only)   │
└───┬──────────────┬─────┘
    │ YES          │ NO (⚠️ or ❌)
    │              │
    ▼              ▼
  EXPORT      ASK USER TO
              FIX & RETRY
```

## Best Practices

1. **Fail early** — ตรวจสอบตอนมีการเปลี่ยนแปลง (ไม่ต้องรอ submit)
2. **Descriptive messages** — บอกผู้ใช้ว่า**อะไร** ผิด **ทำไม**
3. **Suggest fix** — ถ้าเป็นไปได้ ให้ suggestion
4. **Log failures** — เก็บ records ของการจับคู่ที่ไม่สำเร็จ → อัปเดต aliases ต่อไป
5. **Cache results** — ยาที่ validated ให้เก็บไว้ เพื่อไม่ต้องตรวจสอบซ้ำ

## ความเกี่ยวข้อง

- [[wiki/concepts/pharmacy/drug-aliases]] — การแมปชื่อยา
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่
- [[wiki/concepts/pharmacy/ui-design-pharmacy]] — ออกแบบ UI

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]]
- [[wiki/sources/drug-aliases-reference]]
