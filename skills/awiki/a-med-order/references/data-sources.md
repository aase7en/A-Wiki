# A-Med-Order · references/data-sources.md — ข้อมูลอยู่ไหน + สคริปต์อะไรทำอะไร

> เปิดไฟล์นี้เมื่อ: ต้องรู้ path, สร้าง DB ใหม่, หรือหาสคริปต์ที่ถูกตัว

## Data layer

| ชั้น | ที่อยู่ | ใช้ทำอะไร |
|---|---|---|
| **คลังคำพ้อง (auto-learn)** | `<drive>/pharmacy/order-aliases.json` | "ชื่อที่พิมพ์มั่ว → รายการที่ยืนยันแล้ว" — **ถามก่อนเสมอ** |
| **สต๊อกจริง + ทุน** | `<drive>/pharmacy/medi.list/รายการยาทั้งหมด.xls` | ชื่อสินค้าที่ร้านใช้จริง, หน่วย, คงเหลือ, **ราคาทุน/หน่วย** |
| ↳ compiled | `wiki/entities/pharmacy/medi_list.db` (SQLite+FTS5, gitignored) | สร้างด้วย `scripts/import_medi_list.py` |
| **แคตตาล็อก SP 2020 + verified** | `wiki/entities/pharmacy/drugs.db` | fallback fuzzy match — `scripts/pharmacy_lookup.py` |
| **ยอดขาย 2020→ปัจจุบัน** | `<drive>/pharmacy/Sales report/*.xls` | ดูอัตราการขาย/ฤดูกาล ก่อนแนะนำจำนวนสั่ง |
| **ประวัติการสั่ง** | `<drive>/pharmacy/order-history/` | `PO-YYYY-MM-NN_*.xlsx` ทุกใบ + `order-history.json` |
| **session เลน Telegram** | `<drive>/pharmacy/order-sessions/<id>.json` | งานที่ยังค้างอยู่ |
| **ไฟล์ export** | `<drive>/pharmacy/exports/` | csv/xlsx ระหว่างทาง |

`<drive>` = resolve ผ่าน `scripts/drive_path.py::get_pharmacy_dir()` **เท่านั้น**
ห้าม hardcode path เครื่องใดเครื่องหนึ่ง (Iron Law #6) — Mac บ้าน / PC ที่ทำงาน / WSL คนละ path

ข้อมูลธุรกิจจริงอยู่ใน Drive ทั้งหมด — repo เก็บได้แค่ script + template (public-safe)

## รีเฟรชฐานข้อมูล

```bash
python3 scripts/import_medi_list.py          # อ่าน .xls (cp874, ต้องใช้ xlrd) → medi_list.db
python3 scripts/import_medi_list.py --stats  # เช็คว่าอัปเดตวันไหน กี่รายการ
python3 scripts/import_medi_list.py --xls <path>   # ระบุไฟล์เอง
```

ผลลัพธ์อ้างอิง (2026-07-30): 5,291 รายการ · มีราคาทุน 5,101 · ขาดสต๊อก 178

> `.xls` จาก POS ของร้านเป็น OLE2 เข้ารหัส **TIS-620/cp874** — `pandas.read_excel`
> และ `openpyxl` อ่านไม่ได้ ต้อง `xlrd.open_workbook(path, encoding_override="cp874")`

## สคริปต์

| สคริปต์ | หน้าที่ |
|---|---|
| `scripts/import_medi_list.py` | stock .xls → `medi_list.db` + ราคาทุน |
| `scripts/build_order_sheet.py` | `build` / `line` / `cost` / `resolve` / `learn` |
| `scripts/pharmacy_aliases.py` | คลังคำพ้อง — `resolve` / `learn` / `stats` / `list` / `forget` |
| `scripts/med_order_telegram.py` | เลน Telegram — `draft` / `set` / `qty` / `status` / `list` / `finish` |
| `scripts/pharmacy_lookup.py` · `build_pharmacy_db.py` | fuzzy match ชั้นเดิม (drugs.db) |
| `scripts/compare_delivery.py` | เทียบใบส่งของกับที่สั่ง |
| `scripts/drive_path.py` | resolver ของ path ทั้งหมด — ใช้ตัวนี้เสมอ |

## Schema ของ `order-aliases.json`

```json
{
  "schema_version": 1,
  "updated": "2026-07-30",
  "aliases": {
    "<token set เรียงตัวอักษร>": {
      "raw": ["TACTNOL 0.1% 15g"],
      "category": "8. ยาใช้ภายนอก / ผิวหนัง",
      "name": "TACINOL ครีม",
      "strength": "Triamcinolone acetonide 0.1%",
      "pack": "15 g", "unit": "หลอด", "note": "ยาทาสเตียรอยด์",
      "hits": 3, "source": "user-confirmed", "confirmed_at": "2026-07-30"
    }
  }
}
```

เรียนซ้ำ = merge `raw` variant + นับ `hits` · ค่าว่างไม่ทับของเดิม
`raw` ที่ normalize แล้วตรงกับ `name` อยู่แล้ว จะถูก skip (ไม่ได้ช่วยอะไร)
