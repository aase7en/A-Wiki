---
type: entity
category: system
tags: [pharmacy, drug-matching, validation, ai]
sources: [pharmacy-context, drug-aliases-reference]
created: 2026-04-30
updated: 2026-04-30
---

# Drug Matching System

**ประเภท**: AI System / Validation Logic  
**สถานะ**: ✅ In Development  
**Engine**: Fuzzy Match + Drug Aliases + Claude API (อนาคต)  

## ภาพรวม

ระบบแมปชื่อยา/สินค้าที่ลูกค้าส่งมา (อาจสะกดผิด, ใช้ชื่อท้องถิ่น) ให้เป็น**ชื่อมาตรฐาน** ในฐานข้อมูล แล้ว validate ความถูกต้อง

## Algorithm

### Step 1: Input Processing
```
Input: "omeprazol" (typo หรือ abbreviation)
↓
Normalize: lowercase, strip whitespace
→ "omeprazol"
```

### Step 2: Exact Match
```
Search database for exact match
database.find(name == "omeprazol")
→ Not found ❌
```

### Step 3: Alias Lookup
```
Check drug-aliases dictionary
aliases["omeprazol"] = "Omeprazole"
→ Found ✅
Mapped name: "Omeprazole"
```

### Step 4: Fuzzy Search
```
Use fuzzy matching on database
fuzz.ratio("Omeprazole", "OMEPRAZOLE GPO 20mg") = 96%
→ Match confidence: 96% ✅
```

### Step 5: Validation
```
Return matched drug:
{
  "code": "OMEPRAZOLE GPO 20mg 2x7s",
  "name": "Omeprazole",
  "category_code": "A02",
  "category_name": "ยาลดกรด",
  "unit": "box",
  "supplier": "S.P. 2020",
  "confidence": 0.96,
  "match_type": "alias+fuzzy"
}
```

## Confidence Levels

| Score | Interpretation | Action |
|-------|-----------------|--------|
| 100% | Exact match in database | ✅ Proceed |
| 90-99% | High similarity | ✅ Proceed (แจ้ง "fuzzy match") |
| 70-89% | Possible match | ⚠️ Ask user to confirm |
| < 70% | Low similarity | ❌ Not found, ask for reentry |

## Error Handling

### Case 1: Drug not found
```
Input: "supercalifragilisticexpialidocious"
→ No match found
→ Return ❌ "ไม่พบชื่อยา, กรุณาตรวจสอบ"
```

### Case 2: Multiple matches
```
Input: "Aspirin"
→ Possible matches:
  • ASPIRIN 100mg
  • ASPIRIN 500mg
→ Show list, ask user to choose
```

### Case 3: Supplier mismatch
```
Input: "Omeprazole" (found in DB แต่จาก supplier อื่น)
→ ⚠️ Warning: "Found from different supplier"
→ Ask user: confirm or search alternative
```

## Components

### 1. Drug Aliases Reference
- ไฟล์: `drug-aliases.md` (manual reference)
- ลำดับ: 45+ aliases
- Update: Manual, based on user feedback
- Example: "อมอก" → Amoxicillin

### 2. Fuzzy Matcher
- Library: fuzzywuzzy (Python)
- Algorithm: Levenshtein distance
- Threshold: 70-80%

### 3. Database
- Primary: sp_drugs_full_3760.json
- Reference: sp_drugs_medications_2895.json
- Indexed by: name, category_code, code

### 4. AI Engine (Future)
- Tool: Claude API with vision
- Use case: OCR ของรูปภาพยา
- Validation: ตรวจสอบว่าชื่อยาที่ recognize มาถูกต้องหรือไม่

## Integration Points

### Line Bot
```
User sends: "omeprazol 2 กล่อง"
↓
Drug Matching System:
  1. Extract drug name: "omeprazol"
  2. Match → "Omeprazole"
  3. Return formatted message
↓
Bot responds with order form
```

### Web App
```
User types in search field: "amox"
↓
Real-time validation:
  1. On-keystroke matching
  2. Show suggestions (dropdown)
  3. User selects
↓
Form updates with drug details
```

### Claude API Integration
```
User sends image of drug
↓
Claude API:
  1. Read text from image
  2. Extract drug names
  3. Validate each name
↓
Return structured data: [drug_1, drug_2, ...]
```

## Metrics

### Accuracy
- **Target**: > 95% correct match
- **Current** (estimated): 85-90%
- **Tracking**: Log failed matches → add to aliases

### Performance
- **Target**: < 100ms per lookup
- **Current**: ~10-50ms (fuzzy in-memory)

### Coverage
- **Covered**: 3,760 items in database
- **Aliases**: 45+ common drugs
- **Gap**: Need to grow aliases from user feedback

## ความเกี่ยวข้อง

- [[wiki/concepts/pharmacy/drug-aliases]] — แมปชื่อยา
- [[wiki/concepts/pharmacy/drug-validation]] — ตรวจสอบความถูกต้อง
- [[wiki/entities/pharmacy/drug-database]] — ฐานข้อมูล
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]]
- [[wiki/sources/drug-aliases-reference]]
