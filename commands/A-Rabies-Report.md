# /A-Rabies-Report — รายงานไตรมาสพิษสุนัขบ้า

Maps to: `skills/awiki/a-rabies-report/SKILL.md`

## When to use
- สร้างรายงานไตรมาสพิษสุนัขบ้าส่ง สธ.จังหวัด
- นับรายเคส 28 วัน, 9-cell (ครบชุด/<5/ไม่ครบ IM-ID × ERIG-HRIG)

Auto-picks on: `พิษสุนัขบ้า`, `rabies report`, `vaccine report`, `PEP report`

## Flow
1. ใส่ไฟล์ HIS Q<x>.xls
2. `scripts/hospital/classify_rabies.py` ประมวลผล → ตัวเลข Q1-Q4
3. กรอก template .doc → submit สธ.จังหวัด

เต็ม ๆ: `skills/awiki/a-rabies-report/SKILL.md`
