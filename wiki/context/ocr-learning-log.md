---
type: context
tags: [env, ocr, learning, waste-report, hospital]
created: 2026-05-27
updated: 2026-05-27
---

# OCR Learning Log — ใบรายงานขยะโรงพยาบาล

> **วัตถุประสงค์**: บันทึก corrections ที่สะสมจากการใช้งานจริง  
> ทุก device/editor ที่ clone A-Wiki อ่านไฟล์นี้ได้ → ใช้ข้อมูลปรับ system prompt ใน `wiki/synthesis/garbage-report-ocr.md`  
> เมื่อ corrections สะสมมากพอ → merge กลับเข้า system prompt vocabulary section

---

## Corrections Log (สะสม)

| วันที่ | Field | OCR อ่านว่า | ค่าจริง | บริบท / เหตุผล |
|---|---|---|---|---|
| 2026-05-21 | location | จอดรถ | วอร์ด | ลายมือ ว ≈ จ, อักษรท้ายคล้ายกัน |
| 2026-05-21 | location | ลาว | เวช | เวชกรรม — ว-เ-ช vs ล-า-ว รูปใกล้เคียง |
| 2026-05-21 | location | แผนไทย+ฝ่ายแม่ | แผนไทย+ฝังเข็ม | สองแผนก ไม่ใช่ฝ่ายสูตินรี |
| 2026-05-21 | recorder | เพิ่ง | เพ็ญ | ไม้หันอากาศ ≈ ไม้ตรี |
| 2026-05-21 | recorder | กอยง | กลอยใจ | อ่านผิดชื่อย่อ |
| 2026-05-21 | recorder | แสงอร | ณฐอร | อักษรนำ ณ อ่านผิด |
| 2026-05-02 | location | เวช | ฝังเข็ม | row 11 (IMG_4520.jpg) — เวช ↔ ฝังเข็ม ลายมือใกล้เคียง |
| 2026-05-02 | row-mapping | เวช→row13 | ฝังเข็ม→row11 | user override (IMG_4520.jpg) — OCR map row ผิดตำแหน่ง |
| 2026-05-07 | weight | 41 | 36 | row 12 = OPD (S__25362495.jpg) — เลข 6 ↔ 1 อ่านผิด (หรือ 4 ↔ 3) |
| 2026-05-07 | weight | 8 | 9 | row 14 = Ward (S__25362495.jpg) — เลข 8 ↔ 9 อ่านผิด |
| 2026-05-08 | weight | 47 | 33 | row 12 = OPD (S__25362495.jpg) — 4↔3 + 7↔3 (double-digit อ่านผิดทั้งคู่) |
| 2026-05-09 | weight | 23 | 13 | row 12 = OPD (S__25362495.jpg) — 2↔1 หลักสิบอ่านผิดอีก (รูปแบบซ้ำ row 12 OPD) |
| 2026-05-09 | location | OPD | Ward | row 27 = 10 kg, recorder อ้อย (S__25362495.jpg) — userscript ตกหล่น row นี้เพราะ OCR อ่าน Ward เป็น OPD |

---

## Accuracy Trend

| เดือน | รูปที่ scan | corrections | Accuracy (ประมาณ) |
|---|---|---|---|
| เม.ย. 2569 | ไม่ทราบ | — | — |
| พ.ค. 2569 | ไม่ทราบ | 13 fields | ~88% (ประมาณ) |

> ยังไม่มีข้อมูลที่แม่นยำ — จะนับได้เมื่อ userscript บันทึก feedback อัตโนมัติ

---

## Pending System Prompt Improvements

- [ ] **กะดึก ER**: เพิ่ม STAFF CONTEXT — เพ็ญ cover ER กะดึก (19:30น.+) บางครั้ง recorder = เพ็ญ แม้ location = ER
- [ ] **weight "5+5"**: ชี้แจงให้ชัด — อาจหมายถึง "ชั่ง 2 รอบ รวมกัน" หรือ "ตักแยก 2 ถุง" → Aggregation rule ใน userscript ปัจจุบัน: sum = 10
- [ ] **ditto mark variations**: บางใบใช้ `"`, บางใบใช้ `-`, บางใบใช้ `น` หรือ `ง` → ทดสอบเพิ่ม
- [ ] **น้ำหนักตัวเลขคล้ายกัน**: เพิ่ม double-check rule: 2↔9, 6↔5, 1↔4, 8↔9, 4↔3, 2↔1 (หลักสิบ) (โดยเฉพาะค่า >20 กก. หรือ <1 กก.)
- [ ] **🔥 OPD row 12 weight hotspot** (พ.ค. 2569 ผิด 3 ครั้งติด): OCR มัก over-read หลักสิบ (4_ แทน 3_, 2_ แทน 1_) ที่ตำแหน่ง OPD แถวบ่าย — เพิ่ม contextual hint ว่าค่า OPD ปกติอยู่ในช่วง 10-39 ไม่ใช่ 40+
- [ ] **🔥 Ward ↔ OPD location confusion**: row 27 (S__25362495.jpg) OCR อ่าน Ward เป็น OPD ทำให้ userscript ตกหล่น — เพิ่ม recorder-based disambiguation: `อ้อย` มัก = OPD แต่ถ้าน้ำหนัก ≤10 ตอนเย็น อาจเป็น Ward (cross-check กับ recorder อื่นบนใบ)

---

## วิธีเพิ่ม Correction

เมื่อ OCR อ่านผิดในการใช้งานจริง → เพิ่มแถวใน table ด้านบน:

```
| วันที่ | field ที่ผิด | ค่าที่ OCR อ่าน | ค่าจริง | บริบท |
```

แล้ว `git commit -m "ocr-log: add correction [field]"` → push → ทุก device ได้ข้อมูลใหม่ทันที

---

## ความสัมพันธ์

- [[synthesis/garbage-report-ocr]] — System prompt ที่ใช้ (source of truth)
- [[synthesis/waste-form-automation]] — Pipeline + userscript ที่ใช้ system prompt นี้
- `scripts/userscripts/waste-form-ocr-fill.user.js` — userscript ที่ call Gemini + ใช้ system prompt
