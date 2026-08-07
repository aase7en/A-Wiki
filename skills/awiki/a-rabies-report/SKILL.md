---
name: a-rabies-report
description: "รายงานไตรมาสพิษสุนัขบ้าส่ง สธ.จังหวัด — นับรายเคส 28 วัน, 9-cell (ครบชุด/<5/ไม่ครบ IM-ID × ERIG-HRIG). Engine: scripts/hospital/classify_rabies.py. ใส่ไฟล์ HIS Q<x>.xls → ตัวเลข Q1-Q4 กรอก template .doc"
version: 1.0.0
author: A-Wiki
domain: [document, thai, medical]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: both
aliases: [/a-rabies-report, /a-report-rabies-vacc, /a-rabies]
---

# A-Rabies-Report — รายงานไตรมาสพิษสุนัขบ้า

> Quarterly Rabies Vaccination Report — ส่งสำนักงานควบคุมโรค จังหวัด
> Template: "แบบรายงานสรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้าและอิมมุโนโกลบุลิน"

## เมื่อไหร่ใช้

✅ Trigger (ไทย): "สรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้า", "พิษสุนัขบ้า", "rabies report", "Q1/Q2/Q3/Q4 rabies", "รายงานไตรมาสพิษสุนัขบ้า", "rabies vacc"
✅ Trigger (อังกฤษ): "rabies quarterly report", "rabies vaccination summary"
✅ User ส่งไฟล์ HIS `RabiesQ<x>.xls` มา + ขอสรุปตัวเลข

❌ ไม่ใช่:
- การสั่งยา/ฉีดวัคซีนรายคน → ใช้ระบบ HIS ตรงๆ
- รายงานโรคอื่น → ดู a-doc types/report/

## 📊 หน่วยนับ: "รายเคส" (ไม่ใช่ doses)

**1 case = cluster ของ doses ของ HN เดียวกันภายใน 28 วันนับจากเข็มแรก**
- dose ถัดไปห่าง ≤28 วันจากเข็มแรก → อยู่ case เดียวกัน
- dose ห่าง >28 วัน → **case ใหม่ (อุบัติการณ์ใหม่)** แม้ HN เดียวกัน

## 🎯 Algorithm (canonical, verified 2026-08-07)

### Prior history (booster)
"Prior" = dose rabies vaccine (ID หรือ IM) ใดๆ ก่อน start_date ของ case ปัจจุบัน
- ≤180 วัน → booster ต้องการ **1 เข็ม** ใน case นี้
- ≥181 วัน → booster ต้องการ **2 เข็ม** ใน case นี้

⚠️ **ต้องมีข้อมูลย้อนหลัง ≥180 วัน** — รายไตรมาส (90 วัน) ไม่พอ ต้องส่ง `--history` Q ก่อนหน้า

### 9-cell classification

**① ฉีดครบชุด** (ครบ ๕ เข็ม หรือต่ำกว่าด้วย booster)
- IM: `IM ≥ 5` หรือ `(IM=1 + prior ≤180d)` หรือ `(IM=2 + prior ≥181d)`
- ID: `ID ≥ 4` หรือ `(ID=1 + prior ≤180d)` หรือ `(ID=2 + prior ≥181d)`
- ⚠️ **Over-dose within 28d = complete** (HN6949 ID=5, HN5552 total=6 → complete)

**② ฉีดต่ำกว่า ๕ เข็ม** (สังเกตสัตว์ ๑๐ วัน → หยุดฉีด)
- IM: `3 ≤ IM < 5`
- ID: `ID = 3`

**③ ฉีดไม่ครบชุด**
- IM: `(IM < 3 AND no prior)` หรือ `(IM < 2 + prior ≥181d)`
- ID: `(ID < 3 AND no prior)` หรือ `(ID < 2 + prior ≥181d)`
- ⚠️ **IG-only case** (ERIG เข็มเดียว ไม่มี vaccine ใน 28d) → incomplete (tiebreak ด้วยอายุ)

**④ Immunoglobulin (parallel กับ ①②③)**
- ERIG: `ERIG ≥ 1` (Equine, ม้า)
- HRIG: `HRIG ≥ 1` (Human — ปกติ 0 เพราะไม่มี stock)

### Mixed ID+IM (cannot apply pure-route)
1. total ≥ 5 → **complete/IM**
2. total == 4 → **complete/ID**
3. total == 3 → **sub-5** + age tiebreak (<9=IM, ≥9=ID)
4. total ≤ 2 + no prior → **incomplete** + age tiebreak
5. Mixed + prior → REVIEW (spec undefined)

## 🛠️ Workflow (4 ขั้น)

```bash
# 1. รัน engine ต่อไตรมาส — ส่ง --history ของ Q ก่อนหน้าทั้งหมด (180-day lookback)
# Q1 (ต.ค.–ธ.ค. ปีก่อน): ไม่มี history
python scripts/hospital/classify_rabies.py \
  "<drive>/RabiesVacc/<date>_RabiesQ1.xls" \
  --period-start 2025-10-01 --period-end 2025-12-31

# Q2 (ม.ค.–มี.ค.): history = Q1
python scripts/hospital/classify_rabies.py \
  "<drive>/RabiesVacc/<date>_RabiesQ2.xls" \
  --history "<drive>/RabiesVacc/<date>_RabiesQ1.xls" \
  --period-start 2026-01-01 --period-end 2026-03-31

# Q3 (เม.ย.–มิ.ย.): history = Q1+Q2
python scripts/hospital/classify_rabies.py \
  "<drive>/RabiesVacc/<date>_RabiesQ3.xls" \
  --history "<drive>/RabiesQ1.xls" "<drive>/RabiesQ2.xls" \
  --period-start 2026-04-01 --period-end 2026-06-30

# Q4 (ก.ค.–ก.ย.): history = Q1+Q2+Q3
# (เหมือน pattern — เพิ่ม Q3 ใน --history)

# 2. ระหว่างรัน → ตรวจ Mixed list + REVIEW list (stderr)
#    - Mixed HN ทั้งหมด engine ตัดสินด้วย rule #1-5 แล้ว — ดูเพื่อ audit
#    - REVIEW = cases ที่ไม่เข้า rule (ควรเป็น 0; ถ้าไม่ใช่ แจ้ง user)

# 3. กรอกตัวเลข 9-cell ลง template .doc ด้วย python-docx (หรือ Word COM)
#    Template: <drive>/RabiesVacc/20260206_Template_RabiesReport.doc
#    Output:   <drive>/RabiesVacc/<yymmdd>_rabiesvac.<HOSPITAL>Y<be>.doc

# 4. ส่งให้ user ตรวจ + sign + ส่งจังหวัด
```

### ⚠️ กำหนดส่ง (deadline)
- งวด ๑ (ต.ค.–ธ.ค.) → ๕ ก.พ.
- งวด ๒ (ม.ค.–มี.ค.) → ๕ พ.ค.
- งวด ๓ (เม.ย.–มิ.ย.) → ๕ ส.ค.
- งวด ๔ (ก.ค.–ก.ย.) → ๕ พ.ย.

## 🔒 Privacy (Iron Law #6)

- ไฟล์ output (JSON/CSV/Mixed list) **ต้องอยู่ใน `drive/`** — engine enforce ด้วย `enforce_drive_path()`
- HN mask `****<last4>` default; `--verbose-phi` เปิดเฉพาะตอน capture ลง drive log
- PHI lists → stderr; stdout มีแค่ตัวเลข 9-cell (safe to pipe)
- **ชื่อโรงพยาบาล/จังหวัด → placeholder `<HOSPITAL>` / `<PROVINCE>`** ในทุก artifact ใน public repo
- ชื่อคนไข้ไม่ออกจาก breakdown JSON

## 📁 ไฟล์ในงานนี้

| ไฟล์ | หน้าที่ | ที่อยู่ |
|---|---|---|
| `scripts/hospital/classify_rabies.py` | classification engine | repo (public-safe) |
| `<drive>/RabiesVacc/<date>_RabiesQ<x>.xls` | HIS export รายไตรมาส | drive/ (gitignored) |
| `<drive>/RabiesVacc/20260206_Template_RabiesReport.doc` | template ราชการว่าง | drive/ (gitignored) |
| `<drive>/RabiesVacc/_q<x>_breakdown.json` | audit breakdown รายเคส | drive/ (gitignored) |
| `<drive>/RabiesVacc/_q<x>_mixed.csv` | Mixed list สำหรับ review | drive/ (gitignored) |
| `<drive>/RabiesVacc/<yymmdd>_rabiesvac.<HOSPITAL>Y<be>.doc` | report ส่งจังหวัด | drive/ (gitignored) |

## 🧪 Validate engine (regression)

```bash
# 1. Dose reconciliation: engine รายงาน "OK: all N in-period doses reconciled"
#    ถ้า mismatch → engine มี bug หรือ data มี duplicate

# 2. Sum check: 9-cell + IG-only + REVIEW == total cases
#    Q3 ตัวอย่าง: 14+76+17+60+18+126+0(IG)+0(REV) = 311 ✓

# 3. Audit Mixed cases ใน _q<x>_mixed.csv — engine ตัดสินครบทุกเคส
```

## 🔗 Cross-reference

- **Algorithm source**: spec จาก รพ. + สอบถามจังหวัด (2026-08-07)
- **Council review**: 4 critical + 12 important fixes applied (A-Council)
- **A-Think**: confirmed Q1 history จำเป็น (180-day lookback)
- **Iron Laws**: #1 (test-first), #6 (privacy), #10 (registry), #11 (claim)
- **Related skills**: `a-doc` (สร้างเอกสารทั่วไป), `a-council` (review), `a-think` (reasoning)

## 📝 Changelog

- **v1.0.0** (2026-08-07): initial — Q1+Q2+Q3 ปีงบ ๒๕๖๘-๖๙ ครบ, REVIEW=0, engine + template + skill
