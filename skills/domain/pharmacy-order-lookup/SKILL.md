---
name: pharmacy-order-lookup
description: >
  Use when user sends a drug order list (text or images) for Phu Pharmacy.
  Handles typos, wrong sizes, mixed Thai/English. Fuzzy matches against
  SP Drugstore DB + verified-search DB, queues unknowns for subagent web search,
  updates the DB with newly verified items, outputs grouped summary table,
  exports to CSV/Excel, saves order history, and prints LINE-copyable format.
triggers:
  - "รายการยาหมด"
  - "รายการสั่งยา"
  - list of drug names (multi-line text with brand names, mg, ml)
  - "ช่วย match ยา"
  - "ตรวจรายการยา"
  - "export excel"
  - "ส่งออก csv"
  - "ประวัติการสั่ง"
---

# pharmacy-order-lookup

> **Domain**: Pharmacy (ภูฟาร์มาซี — บางปูใหม่ จ.สมุทรปราการ)
> **DBs**: `drugs.db` (SQLite FTS5) ← built from SP 3,760 SKU + verified-search items
> **Script**: `scripts/pharmacy_lookup.py`

---

## หลักการ (Rules)

1. **ชื่อยาสะกดผิดเป็นเรื่องปกติ** — fuzzy match เสมอ ไม่ reject ทันที
2. **Search result = ข้อมูลแท้** — เมื่อ web search พบชื่อใกล้เคียง >80% ให้ยึด search เป็นหลัก
3. **อัปเดต DB อัตโนมัติ** — รายการที่ verified จาก search → เพิ่มใน `alternative-source-items.json` → hook rebuild `drugs.db`
4. **แยกขนาดบรรจุ/ความแรงเสมอ** — "Diora 28" ≠ "Diora 21", "NUROFEN 400mg" ≠ "NUROFEN 600mg"

---

## Confidence Tiers

| Score | ป้าย | Action |
|-------|------|--------|
| ≥ 80% | ✅ | Accept — แสดงใน summary |
| 60-79% | ⚠️ | Candidate — แสดงพร้อม top-3 ให้ user เลือก |
| < 60% | ❌ | Not found → queue subagent search |

---

## ขั้นตอน (Workflow)

### Step 1 — Parse input
- รับ text list (1 รายการ/บรรทัด) หรือรูปภาพ
- แยกชื่อยา ออกจาก จำนวน/หน่วย (เช่น "betadine 2 ขวด" → query = "betadine")
- Normalize: lowercase, ตัด special chars

### Step 2 — DB Lookup
```bash
echo "<item1>\n<item2>..." | python3 scripts/pharmacy_lookup.py
# หรือ JSON mode สำหรับ Claude:
python3 scripts/pharmacy_lookup.py --json < items.txt
```
- FTS5 keyword search ก่อน (fast)
- Fuzzy fallback ถ้า FTS ไม่พอ
- Return: matched ✅ / candidates ⚠️ / not_found ❌

### Step 3 — Subagent search (เฉพาะ ❌)
สำหรับแต่ละรายการที่ไม่พบ → spawn subagent ด้วย prompt:

```
Search Thai pharmacy market for: "<item_name>"
Find: correct brand name, available strengths/sizes in Thailand, where to buy.
If found with >80% name similarity to query, return structured JSON:
{
  "name": "...", "name_th": "...", "name_en": "...",
  "aliases": ["original_query", ...],
  "strength": "...", "package_size": "...", "unit": "...",
  "category_name": "...", "where_to_buy": "...",
  "note": "...", "verified_date": "YYYY-MM-DD"
}
If not found, return {"not_found": true, "note": "reason"}
```

### Step 4 — อัปเดต DB
สำหรับแต่ละรายการที่ subagent verified:
```python
from scripts.pharmacy_lookup import add_to_alt_db
add_to_alt_db(verified_item_dict)
```
แล้ว rebuild DB:
```bash
python3 scripts/build_pharmacy_db.py
```

### Step 5 — สรุปผล + Export + History

```bash
# Summary grouped by category (default)
python3 scripts/pharmacy_lookup.py < items.txt

# Export Excel (color-coded, ช่องจำนวนว่าง)
python3 scripts/pharmacy_lookup.py --export excel --save --line < items.txt

# Export CSV
python3 scripts/pharmacy_lookup.py --export csv < items.txt

# JSON สำหรับ Claude
python3 scripts/pharmacy_lookup.py --json < items.txt
```

Output ตัวอย่าง (grouped by category, sorted A-Z):
```
📂  ยาต้านแบคทีเรีย
ชื่อที่สั่ง     ชื่อยาในฐานข้อมูล        ความแรง    จำนวน  สถานะ
AMK 650mg       AMK 625 (Amox+Clav625)   Amox500+…         ✅ (100%)

📂  ยาแอนติเซพติค
betadine 15ml   BETADINE 15ml            15ml              ✅ (92%)
```

Excel: `drive/pharmacy/exports/order_YYYYMMDD_HHMMSS.xlsx`
History: `drive/pharmacy/order-history.json` (append per session)
LINE format: copy-paste ได้ทันที พร้อม `___` ช่องกรอกจำนวน

---

## SQLite Database

```
wiki/entities/pharmacy/drugs.db
├── TABLE drugs          — 3,760 SP + N verified-search items
│   fields: name, name_th, name_en, aliases(JSON), category_*, strength,
│           package_size, unit, supplier, where_to_buy, note, source, verified_date
└── VIRTUAL TABLE drugs_fts (FTS5, tokenize=unicode61)
    — fast keyword search across name/name_th/name_en/aliases
```

**Rebuild trigger**: SessionStart hook `build-pharmacy-db.sh` — ตรวจ timestamp อัตโนมัติ

---

## ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ |
|------|---------|
| `raw/pharmacy/sp_drugs_full_3760.json` | ฐานข้อมูล SP (immutable) |
| `drive/pharmacy/alternative-source-items.json` | รายการ verified-search (อัปเดตได้; real business data → drive/, ดู `scripts/drive_path.py::get_pharmacy_dir()`) |
| `wiki/entities/pharmacy/drugs.db` | SQLite compiled (auto-rebuilt, gitignored) |
| `drive/pharmacy/order-history.json` | ประวัติการสั่งทุก session |
| `drive/pharmacy/exports/` | ไฟล์ CSV/Excel ที่ export |
| `drive/pharmacy/deliveries/` | ใบส่งสินค้า (invoice JSON) สำหรับ `compare_delivery.py` |
| `scripts/build_pharmacy_db.py` | Build/rebuild drugs.db จาก JSON |
| `scripts/pharmacy_lookup.py` | Lookup + fuzzy match + export + history |
| `.claude/hooks/build-pharmacy-db.sh` | Auto-rebuild hook (SessionStart) |

---

## เมื่อ DB ใหญ่ขึ้น — SQLite Strategy

- FTS5 tokenize=unicode61 รองรับ Thai/English mixed text
- Index บน `source` column สำหรับ filter SP vs verified
- DB ขนาด < 10MB สำหรับ 10,000+ items — ยังเร็วพอ
- ถ้า > 50,000 items → พิจารณา trigram index หรือ embedding-based search
- ไม่ต้องการ server — SQLite file ตามไปกับ git repo

---

## ตัวอย่างการใช้งาน

```
User: "รายการยาหมด: เบตาดีน 15ml, ดิออร์รา 28, AMK 650mg..."
Claude: → ใช้ skill pharmacy-order-lookup
         → Step 1: parse list
         → Step 2: python3 scripts/pharmacy_lookup.py --export excel --save --line
         → Step 3: spawn subagent สำหรับรายการ ❌
         → Step 4: add_to_alt_db() + rebuild
         → Step 5: แสดง summary table (grouped by category)
                   + ส่ง Excel file
                   + LINE-copyable format
                   + บันทึก history
```
