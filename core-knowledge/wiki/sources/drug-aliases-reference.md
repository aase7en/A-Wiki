---
type: source
title: "Drug Aliases Reference Dictionary"
slug: drug-aliases-reference
date_ingested: 2026-04-30
original_file: raw/drug-aliases.md
tags: [pharmacy, drug-matching, aliases, validation]
---

# Drug Aliases Reference Dictionary

**ประเภท**: Reference Dictionary  
**วันที่ Ingest**: 2026-04-30  

## ประเด็นหลัก

1. **Drug Aliases** — การแมปชื่อสะกดผิด / ชื่อท้องถิ่น ไปยังชื่อมาตรฐาน
   - "อมอก" / "amox" / "อ.ม.มอก" → Amoxicillin
   - "การา" / "para" / "paracet" → Paracetamol
   - "ความโล่ง" → Loratadine

2. **หมวดหมู่และจำนวนยา** — 45+ ยาทั่วไป ครอบคลุม:
   - ยาแก้ปวด (Paracetamol, Ibuprofen, Mefenamic Acid)
   - ยาแก้ไอ (Ambroxol, Bromhexine)
   - ยาต้านแพ้ (Cetirizine, Loratadine, Chlorpheniramine)
   - ยาแก้กล้อม (Omeprazole)
   - ยากับเบาหวาน (Metformin)
   - ยาความดัน (Amlodipine, Enalapril)
   - และอื่นๆ

3. **Aliases Pattern** — 4 ประเภท:
   - **Abbreviation**: CPM → Chlorpheniramine
   - **Misspelling**: Amoxycillin → Amoxicillin
   - **Thai transliteration**: อมอก → Amoxicillin
   - **Trade name mapping**: Ponstan → Mefenamic Acid

4. **Use Case** — AI drug matching:
   - ลูกค้าส่ง "omeprazol" (ไม่ใช่ exact match)
   - AI lookup aliases → "omeprazol" = "Omeprazole"
   - Search DB → พบ "OMEPRAZOLE GPO 20mg"
   - Return match ✅

## ข้อมูลที่น่าสนใจ

| ประเด็น | ตัวอย่าง |
|--------|---------|
| ชื่อสะกดผิด | Hirudoid (ผิด) → HIRUDOID (ถูก) |
| การแทนอักษร | "l" vs "I" (BETA-DOPO vs BETA-DIPO) |
| ชื่อประเทศไทย | Ponstan = Mefenamic Acid |
| Abbreviation | ORS = Oral Rehydration Salts |

## ข้อโต้แย้ง / ความขัดแย้ง

- **ไม่มี aliases ที่ครอบคลุม 100%** — ต้องเพิ่มเติมจากการใช้งานจริง (feedback จากลูกค้า)
- **Fuzzy match อาจจับคู่ผิด** เช่น "Aspirin" vs "Albuterol" ลักษณะ similar แต่ยาต่างหมวด

## หน้า Wiki ที่ได้รับการอัปเดต

- [[wiki/concepts/pharmacy/drug-aliases]]
- [[wiki/concepts/pharmacy/drug-validation]]
- [[wiki/entities/pharmacy/drug-matching-system]]
- [[index-pharmacy]]
