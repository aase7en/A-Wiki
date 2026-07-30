---
name: a-med-order
description: "ใบสั่งซื้อยาร้านภูฟาร์มาซี end-to-end — รับลิสต์ยาหมดที่พิมพ์มั่ว (ไทยปนอังกฤษ / คาราโอเกะ / สะกดผิด / หน่วยเพี้ยน) → normalize + verify ชื่อยาจากคลังคำพ้องและสต๊อกจริง → ออกไฟล์ Excel/Google Sheet ตาม template (12 หมวด, ช่องกรอกจำนวน, ทุนต่อหน่วย) → ผู้ใช้กรอกจำนวน → สรุปเป็นข้อความ copy วาง LINE. มีเลน Telegram ไม่ใช้ browser สำหรับ Pi5. Trigger: 'รายการยาหมด', 'รายการสั่งยา', 'สั่งยา', 'ใบสั่งยา', 'ยาหมด', ลิสต์ชื่อยาหลายบรรทัด"
version: 1.2.0
author: A-Wiki
domain: [pharmacy, business]
lifecycle_phase: build
category: pipeline
agents: [all, hermes]
status: canonical
invocation: both
---

# A-Med-Order — ใบสั่งซื้อยา ร้านภูฟาร์มาซี

> **เจ้าของงาน**: ศุภศิษฎิ์ คงสุวรรณ · ร้านยาภูฟาร์มาซี (สมุทรปราการ)
> Progressive disclosure — ไฟล์นี้คือขั้นตอนที่ต้องทำ; รายละเอียดอยู่ใน `references/` โหลดเฉพาะที่ใช้

## 🚨 กฎที่ห้ามพลาด (อ่านก่อนเสมอ)

1. **ห้าม "มโน" ชื่อยา / ตัวยา / ความแรง / ขนาดบรรจุ** — ไม่ชัวร์ให้ปล่อยว่าง + หมายเหตุ
   "ยืนยันกับผู้แทน" **ดีกว่าเดาผิด** สั่งยาผิดตัวหรือผิดขนาด = อันตรายกับคนไข้
2. **ขนาดบรรจุต่างกัน = คนละ SKU** — `Minny 21` ≠ `Minny 28`, `MYDA-B 15g` ≠ `MYDA-B 25g` ห้ามยุบรวม
3. **ยาที่ต้องระวังเป็นพิเศษ**
   - ยาควบคุมพิเศษ/ยาอันตราย (VENTOLIN, ยาปฏิชีวนะ) → ใส่หมายเหตุเตือนตรวจใบสั่งซื้อ
   - ยาคุมฉุกเฉิน → แยกชนิด 1 เม็ด (Levonorgestrel 1.5 mg) กับ 2 เม็ด (0.75 mg) ให้ชัด
   - สเตียรอยด์ทาภายนอก (Tacinol / Kela / ที.วี.โลน / TRAM = Triamcinolone acetonide 0.1% ทั้งหมด)
     → ชื่อต่างแต่ตัวยาเดียวกัน **คนละ SKU คนละราคา อย่ายุบ**
4. **ข้อมูลธุรกิจอยู่ใน `<drive>/pharmacy/` เท่านั้น** — resolve path ผ่าน
   `scripts/drive_path.py::get_pharmacy_dir()` ห้าม hardcode (Iron Law #6)

## เริ่มงานทุกครั้ง

```bash
python3 scripts/import_medi_list.py          # รีเฟรชสต๊อก + ราคาทุน (ควรรันวันละครั้ง)
python3 scripts/import_medi_list.py --stats  # เช็คว่าอัปเดตวันไหน
```

---

## เลน A — เต็ม (มี Google Sheet) · ใช้บน Claude Code / Cowork

```bash
# 1) ลิสต์ดิบ → JSON draft: คลังคำพ้อง → สต๊อกจริง → unknown
python3 scripts/build_order_sheet.py resolve list.txt

# 2) เฉพาะรายการ status=unknown เท่านั้นที่ต้องตัดสินใจ  → references/normalization.md
# 3) จัด 12 หมวด แล้วสร้างไฟล์
python3 scripts/build_order_sheet.py build items.json \
        --out "<drive>/pharmacy/order-history/PO-YYYY-MM-NN_ใบสั่งยา.xlsx" --po PO-YYYY-MM-NN

# 4) ผู้ใช้กรอกจำนวน → 5) ข้อความ LINE
python3 scripts/build_order_sheet.py line "<path ที่กรอกแล้ว>"

# 6) จำคำที่ยืนยันรอบนี้ ห้ามข้าม
python3 scripts/build_order_sheet.py learn confirmed.json
```

## เลน B — Telegram ไม่ใช้ browser · Pi5 / Hermes / ZCode / โมเดล free-tier

```bash
python3 scripts/med_order_telegram.py draft list.txt --session YYYYMMDD-NN
python3 scripts/med_order_telegram.py set  <id> <ข้อ> --name "..." --strength "..." \
        --pack "..." --unit "..." --category "..."      # เฉพาะรายการ ❓ unknown
python3 scripts/med_order_telegram.py qty  <id> "1=12 2=10 3=40"
python3 scripts/med_order_telegram.py finish <id> --po PO-YYYY-MM-NN
```

`finish` = เขียน xlsx ลง `order-history/` + พิมพ์ข้อความ LINE + เรียน alias อัตโนมัติ
รายละเอียด (รูปแบบคำตอบจำนวน, session, ข้อจำกัด) → `references/telegram-lane.md`

---

## 12 หมวดมาตรฐาน (คงลำดับนี้เสมอ)

```
1. ยาแก้ปวด / ลดไข้              7. ยาคุมกำเนิด
2. ยาแก้แพ้ / เวียนศีรษะ          8. ยาใช้ภายนอก / ผิวหนัง
3. ยาปฏิชีวนะ / ต้านเชื้อรา       9. เวชภัณฑ์ / ทำแผล
4. ยาโรคเรื้อรัง / ทางเดินปัสสาวะ 10. ยาหยอดตา
5. ยาระบบทางเดินอาหาร           11. วิตามิน / อาหารเสริม
6. ยาระบบทางเดินหายใจ           12. ยาดม / พิมเสน
```

## ✅ Checklist ก่อนส่งงาน

- [ ] `import_medi_list.py` รันแล้ววันนี้
- [ ] ทุกรายการมีหมวด (ชีต "สรุปตามหมวด" ต้องนับได้ = จำนวนรายการจริง)
- [ ] ยอดรวมจำนวนชีต 1 = ชีต 2
- [ ] รายการซ้ำยุบแล้ว (ยกเว้นต่างขนาดบรรจุ)
- [ ] รายการที่ยังไม่ชัด มีหมายเหตุ + **รวบถามครั้งเดียวท้ายงาน** อย่าถามทีละรายการ
- [ ] ไฟล์อยู่ใน `<drive>/pharmacy/order-history/`
- [ ] **เรียน alias จากชื่อที่ยืนยันรอบนี้แล้ว** (`pharmacy_aliases.py stats` ต้องเพิ่มขึ้น)
- [ ] ข้อความ LINE ผ่าน `line` mode (ไม่พิมพ์มือ — กันตกหล่น)

---

## 📚 references/ (โหลดเฉพาะเมื่อต้องใช้)

| ไฟล์ | เปิดเมื่อ |
|---|---|
| `references/normalization.md` | ต้องแก้คำผิด/เดาชื่อยา — กฎคาราโอเกะ, หน่วยเพี้ยน, 5 ด่าน, auto-learn |
| `references/order-sheet.md` | ต้องสร้าง/แก้ไฟล์ Excel หรือ import ขึ้น Google Sheet — โครงคอลัมน์ + ขั้นตอน |
| `references/telegram-lane.md` | ทำงานผ่าน Telegram / Pi5 — รูปแบบคำตอบ, session, ข้อจำกัด |
| `references/data-sources.md` | ต้องรู้ว่าข้อมูลอยู่ไหน — drive layout, DB, สคริปต์ทั้งหมด |

## Invocation

```
/A-Med-Order รายการยาหมด <วางลิสต์ที่นี่>     # เลน A
/A-Med-Order telegram <วางลิสต์ที่นี่>         # เลน B
/A-Med-Order line <path ไฟล์ที่กรอกจำนวนแล้ว>
```

## Related

`pharmacy-order-lookup` (fuzzy match ชั้นเดิม) · `a-wiki-telegram` (transport ของเลน B) ·
`a-doc-procurement` (เอกสารจัดซื้อทั่วไป) · `a-business` · `excel-generator`
