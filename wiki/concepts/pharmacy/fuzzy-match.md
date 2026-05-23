---
type: concept
tags: [pharmacy, fuzzy-match, drug-validation, nlp, string-matching]
sources: [sp-drugstore-2020-catalog]
created: 2026-04-30
updated: 2026-04-30
---

# Fuzzy Match ชื่อยา (Drug Name Fuzzy Matching)

## นิยาม

Fuzzy matching คือเทคนิคจับคู่สตริงที่ไม่ต้องตรงกันทั้งหมด ใช้สำหรับหาชื่อยาใน database เมื่อ input สะกดผิด ใช้ตัวย่อ หรือเขียนต่างกับชื่อมาตรฐาน

## ทำไมถึงสำคัญในร้านยา

รายการสั่งยาที่ส่งมาทาง LINE มักมีความไม่สม่ำเสมอ:
- สะกดผิด: `amoxicilin`, `paracetamole`
- ชื่อสามัญ vs ชื่อการค้า: `Paracetamol` vs `SARA`, `TYLENOL`, `ASUMOL`
- ย่อ: `amox 500`, `CPM`
- ภาษาไทย-อังกฤษปะปน

## วิธีการทำงาน

### Algorithm ที่ใช้บ่อย

| Algorithm | เหมาะกับ | ตัวอย่าง |
|-----------|---------|---------|
| **Levenshtein Distance** | สะกดผิด 1-2 ตัวอักษร | `amoxicilin` → `Amoxicillin` |
| **Jaro-Winkler** | ชื่อสั้น ตัวย่อ | `CPM` → `Chlorpheniramine` |
| **Token Sort Ratio** | คำสลับที่ | `amox 500mg` → `Amoxicillin 500mg` |
| **BM25** | ค้นหาข้อความยาว | query เต็มประโยค |

### Python Libraries

```python
from rapidfuzz import fuzz, process

# หา match ที่ดีที่สุดจาก database
result = process.extractOne(
    query="amoxicilin 500",
    choices=drug_names,
    scorer=fuzz.WRatio,
    score_cutoff=70
)
```

### Threshold แนะนำ

- **≥ 90**: confident match → แสดงทันที
- **70–89**: probable match → แสดงให้ผู้ใช้ยืนยัน
- **< 70**: no match → แจ้งว่าไม่พบ ให้ search manual

## Aliases และ Brand Names

SP Drugstore catalog มีทั้งชื่อสามัญและชื่อการค้า ควรสร้าง alias map เพิ่มเติม:

```json
{
  "paracetamol": ["SARA", "TYLENOL", "ASUMOL", "TEMPRA"],
  "amoxicillin": ["AMK", "AMOXIL", "A.M.MOX", "OMOXILLIN"],
  "chlorpheniramine": ["CPM", "CTM"]
}
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| รับ input ที่สะกดผิดได้ | อาจ match ผิดถ้า threshold ต่ำเกินไป |
| ไม่ต้องพิมพ์ตรงเป๊ะ | ชื่อยาบางตัวสั้นมาก เกิด false positive |
| ใช้ร่วมกับ Claude API ได้ | ต้องปรับ threshold ตามข้อมูลจริง |

## ความสัมพันธ์

- ใช้ใน: [[wiki/synthesis/pharmacy-order-checker]] — ขั้นตอน validation
- ข้อมูลยา: [[wiki/concepts/pharmacy/drug-classification]] — ATC codes + ชื่อยา
- Workflow: [[wiki/concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ

## แหล่งข้อมูล

- [[wiki/sources/sp-drugstore-2020-catalog]] — ฐานข้อมูลยา 3,760 รายการ
