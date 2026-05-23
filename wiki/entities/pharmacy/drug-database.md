---
type: entity
category: database
tags: [pharmacy, database, inventory, drugs]
sources: [pharmacy-context]
created: 2026-04-30
updated: 2026-04-30
---

# Drug Database — sp_drugs_full_3760.json

**ประเภท**: Database / Catalog  
**สถานะ**: ✅ Active  
**ขนาด**: ~5-10 MB JSON  

## ภาพรวม

ฐานข้อมูลสินค้ากลาง จากผู้จัดจำหน่าย **S.P. Drugstore 2020** ครอบคลุมยา เครื่องสำอาง อาหารเสริม และสินค้าสุขภาพอื่นๆ ทั้งหมด **3,760 รายการ**

## ไฟล์ฐานข้อมูล

### Runtime (primary): `wiki/entities/pharmacy/drugs.db`
- **รูปแบบ**: SQLite + FTS5 (gitignored — build จาก JSON)
- **คำสั่ง build/refresh**: `python3 scripts/build_pharmacy_db.py`
- **ใช้สำหรับ**: search/fuzzy-match, order processing runtime (`scripts/pharmacy_lookup.py`)

### Source (immutable): sp_drugs_full_3760.json
- **จำนวน**: 3,760 รายการ
- **ขอบเขต**: ยา + เครื่องสำอาง + อาหารเสริม + สินค้าอื่นๆ
- **ตำแหน่ง**: `raw/pharmacy/sp_drugs_full_3760.json`

### Reference: sp_drugs_medications_2895.json
- **จำนวน**: 2,895 รายการ (ยาเท่านั้น)
- **ตำแหน่ง**: `raw/pharmacy/sp_drugs_medications_2895.json`

## โครงสร้าง JSON

```json
{
  "code": "AMOXYCILLIN 500MG 20X10S",
  "category_code": "A01",
  "category_name": "ยาแช่งชา/ลำไส้",
  "name": "Amoxicillin",
  "strength": "500mg",
  "unit": "box",
  "supplier": "S.P. Drugstore 2020",
  "_note": "optional หมายเหตุเพิ่มเติม"
}
```

### Fields
| Field | ประเภท | ตัวอย่าง | หมายเหตุ |
|-------|--------|---------|---------|
| code | string | AMOXYCILLIN 500MG 20X10S | รหัสสินค้า |
| category_code | string | A01, N02, R06 | ATC Code |
| category_name | string | ยาแช่งชา/ลำไส้ | ชื่อหมวดหมู่ไทย |
| name | string | Amoxicillin | ชื่อทั่วไป |
| strength | string | 500mg, 20% | ความเข้มข้น |
| unit | string | box, vial, bottle | หน่วยสั่งซื้อ |
| supplier | string | S.P. Drugstore 2020 | ผู้จัดจำหน่าย |
| _note | string | optional | หมายเหตุ |

## Category Code Mapping (ATC-based)

| Code | ชื่อหมวดหมู่ | รายการตัวอย่าง |
|------|------------|-------------|
| A01 | ยาแช่งชา/ลำไส้ | Antidiarrheal |
| A02 | ยาลดกรด | Omeprazole, Antacid |
| A04 | ยาต้านอาการคลื่นไส้ | Metoclopramide |
| A06 | ยาถ่ายชำรวย | Laxative |
| A11 | วิตามิน/อาหารเสริม | Vitamin C, B complex |
| C02 | ยาลดความดัน | Amlodipine, Enalapril |
| D07 | ยาสเตียรอยด์ทาผิว | Topical steroids |
| D08 | ยาฆ่าเชื้อ | Iodine, Chlorhexidine |
| D10 | ยาแก้ผื่น | Antifungal, Anti-itch |
| G03 | ยาฮอร์โมน | Contraceptive |
| J01 | ยาต้านแบคทีเรีย | Amoxicillin, Azithromycin |
| J02 | ยาต้านเชื้อรา | Antifungal |
| N02 | ยาแก้ปวด | Paracetamol, Ibuprofen |
| N07 | ยาระงับประสาท | Psychotropic |
| R05 | ยาแก้ไอ | Ambroxol, Bromhexine |
| R06 | ยาต้านแพ้ | Cetirizine, Loratadine |
| S01 | ยาหยอดตา | Antibiotic drops |

## Data Quality

### Strengths
- ✅ Comprehensive coverage (3,760 items)
- ✅ Structured JSON format
- ✅ Category standardized (ATC-based)
- ✅ Updated regularly from supplier

### Known Issues
- ⚠️ Some spelling variations between primary and reference
- ⚠️ Not all items have complete description
- ⚠️ Price information not included
- ⚠️ Stock information not available (static data)

## Usage

### Search
```python
# Find by name
drugs = filter(lambda d: "Amoxicillin" in d['name'], database)

# Find by category
drugs = filter(lambda d: d['category_code'] == "A02", database)

# Fuzzy match
from fuzzywuzzy import fuzz
matches = [d for d in database if fuzz.ratio(query, d['name']) > 80]
```

### Validation
```python
def validate_drug(name):
    # Lookup in aliases first
    if name in aliases:
        name = aliases[name]
    
    # Search in database
    for drug in database:
        if fuzzy_match(name, drug['name']):
            return drug
    
    return None
```

## ความเกี่ยวข้อง

- [[wiki/entities/pharmacy/sp-drugstore-2020]] — ผู้จัดจำหน่าย
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่
- [[wiki/concepts/pharmacy/drug-aliases]] — แมปชื่อยา
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]]
