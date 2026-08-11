---
name: a-rabies-report
description: "รายงานไตรมาสพิษสุนัขบ้าส่ง สธ.จังหวัด — นับรายเคส, 9-cell, prior=complete-series (10y lookback), 33d first-dose-anchored window + abandoned-dose detection + quarter-straddle deferral. Engine: scripts/hospital/classify_rabies.py + .sql. Roadmap: standalone PDPA-safe tool"
version: 1.3.0
author: A-Wiki
domain: [document, thai, medical]
lifecycle_phase: build
category: pipeline
agents: [all]
status: canonical
invocation: both
invocation_hint: "/A-Rabies-Report"
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

**1 case = cluster ของ doses ของ HN เดียวกันภายใน 33 วันนับจากเข็มแรก** (v1.3.0)

> **เหตุผลที่ใช้ 33 วัน ไม่ใช่ 28:**
> - Schedule IM (Essen): Day 0,3,7,14,**28** → last dose ตกวันที่ 28
> - Schedule ID (IPC): Day 0,3,7,**28-30** → last dose ตกวันที่ 28-30
> - CDC MMWR RR-5703: "delays of a few days are unimportant" → +3d grace
> - รวม = **30d schedule + 3d grace = 33d** ครอบคลุมทั้ง IM และ ID + การมาสาย 1-3 วัน
> - 28d window (เวอร์ชั่นเก่า) split เคสที่ Day-28 dose มาสาย 1 วัน (HN 10217, 388351)

- dose ถัดไปห่าง ≤33 วันจากเข็มแรก → อยู่ case เดียวกัน
- dose ห่าง >33 วัน → **case ใหม่ (อุบัติการณ์ใหม่)** — "หลักเดือน = รอบใหม่"
- anchored ที่เข็มแรก (ไม่ใช่ sliding) → คนไข้ที่หายไป 2+ เดือนถูกแยกเป็นเคสใหม่ถูกต้อง

### 🆕 Bugfix #4 (v1.3.0): "Abandoned dose + clean restart" detection

บางครั้งคนไข้ได้ 1 เข็มแล้วหายไป (ขาดช่วง) แล้วมาเริ่มซีรี่ส์ใหม่ภายหลัง:
```
HN 176434:
  03/03  ID + ERIG       (1 เข็ม → หายไป)
  10/03  ID              (Day 0 ใหม่)
  13/03  ID              (Day +3)
  17/03  ID              (Day +7)
  07/04  ID              (Day +28 — ID schedule สมบูรณ์จาก 10/03)
```

**อัลกอริทึม** (`refine_clusters_cross_window`):
1. หลัง time-window clustering ให้ตรวจ schedule-fit ของ forward slice จากแต่ละ dose
2. แยกเป็น 2 เคสเมื่อทั้ง 4 เงื่อนไข:
   - **Strict schedule-fit**: ทุกเข็มต้องอยู่ใน ±2 วันของ day ที่คาดไว้ (no strays)
   - **Dose count**: 4-7 เข็มใน forward slice (ไม่ใช่ 13 เข็มข้ามปี)
   - **Span**: ≤35 วัน (one schedule + grace)
   - **Pre-anchor doses ไม่ fit schedule ใด** (ถ้า fit แปล่า่า prior-complete + booster ไม่ใช่ abandoned)
3. Pre-anchor doses → case A (abandoned, incomplete)
4. Anchor + later doses → case B (clean restart, classified normally)

> **STRICT conditions** สำคัญมาก (audit 2026-08-11): แบบเก้มี false positive
> รวม HN 142753 (13 doses ข้าม 5 ปี → 2016-2026) เป็น 1 เคส "complete" ผิด

### 🆕 Bugfix #5 (v1.3.0): Quarter straddle → defer to next quarter

> **กฎของโรงพยาบาล:** "ถ้ารายการฉีดวัคซีน คาบเกี่ยวหรือข้ามไตรมาส ต้องยังไม่นับเคสนั้น ให้ถือว่าเคสนั้น ขยับไปอยู่อีก Q ไตรมาสถัดไปแทน"

- Case ที่เริ่มใน Q2 แต่จบใน Q3 → นับใน **Q3** (ไม่ใช่ Q2)
- Case ทั้งหมดใน Q3 → ยังอยู่ Q3 (unchanged)
- Case ทั้งหมดใน Q2 → ยังอยู่ Q2 (unchanged)

**Implementation**: period filter ใช้ `end_date` ไม่ใช่ `start_date`

## 🎯 Algorithm (canonical, verified 2026-08-07 — 0 REVIEW across 916 cases)

### Prior history (booster) — v1.2.0+ bugfix #2
"Prior" = **complete rabies vaccination series** (≥3 doses ID+IM combined) ก่อน start_date ของ case ปัจจุบัน
- ≥3 doses = complete series (ตาม DDC pre-exposure 3-dose spec + screening app "เคยฉีด 3 เข็ม หรือมากกว่า")
- ≤180 วัน → booster ต้องการ **1 เข็ม** ใน case นี้
- ≥181 วัน → booster ต้องการ **2 เข็ม** ใน case นี้

**2 แหล่ง prior:**
1. HIS data (lookback 10 ปี จาก `--history`)
2. Screening app (ผู้ป่วยที่ฉีดที่โรงพยาบาลอื่น — `--screening` file)

⚠️ **ต้องมีข้อมูลย้อนหลัง ≥180 วัน** — รายไตรมาส (90 วัน) ไม่พอ ต้องส่ง `--history` Q ก่อนหน้า + DB files 10 ปี

### Default rules (v1.3.0 — รวม special rules, 33d window, abandoned-dose, straddle)
1. **Over-dose within 33d → complete** (เข็มเกิน = ครบ)
2. **IG-only** (ERIG/HRIG ไม่มี vaccine ใน 33d) → incomplete by age
3. **>33d gap → new incident** → case clustering + re-classify with prior
4. **Abandoned dose + clean restart** → split (v1.3.0 bugfix #4)
5. **Quarter straddle** → case belongs to quarter of end_date (v1.3.0 bugfix #5)
6. **Mixed ID+IM**: total doses decide + age tiebreak for 2-3 dose cases
7. **Prior history** = complete series (≥3 doses) within 10y lookback: ≤180d = booster 1 dose, ≥181d = booster 2 doses

### 9-cell classification

**① ฉีดครบชุด** (ครบ ๕ เข็ม หรือ booster หรือ over-dose)
- IM: `IM ≥ 5` หรือ `(IM≥1 + prior ≤180d)` หรือ `(IM≥2 + prior ≥181d)`
- ID: `ID ≥ 4` หรือ `(ID≥1 + prior ≤180d)` หรือ `(ID≥2 + prior ≥181d)`

**② ฉีดต่ำกว่า ๕ เข็ม** (สังเกตสัตว์ ๑๐ วัน → หยุดฉีด)
- IM: `3 ≤ IM < 5`
- ID: `ID = 3`

**③ ฉีดไม่ครบชุด**
- IM: `(IM < 3 AND no prior)` หรือ `(IM < 2 + prior ≥181d)`
- ID: `(ID < 3 AND no prior)` หรือ `(ID < 2 + prior ≥181d)`
- IG-only case → incomplete by age tiebreak

**④ Immunoglobulin (parallel กับ ①②③)**
- ERIG: `ERIG ≥ 1` (Equine, ม้า)
- HRIG: `HRIG ≥ 1` (Human — ปกติ 0)

### Mixed ID+IM (cannot apply pure-route)
1. total ≥ 5 → **complete/IM**
2. total == 4 → **complete/ID**
3. total == 3 → **sub5** + age tiebreak (<9=IM, ≥9=ID)
4. total ≤ 2 + no prior → **incomplete** + age tiebreak
5. total ≤ 2 + prior ≤180d + total≥1 → **complete** by age (booster rule)
6. total ≤ 2 + prior ≥181d + total≥2 → **complete** by age
7. total ≤ 2 + prior ≥181d + total<2 → **incomplete** by age

REVIEW เกิดเฉพาะเมื่อ **age is None** ใน Mixed tiebreak — เป็น data quality gap ของ HIS
ไม่ใช่ algorithm gap. Audit: 916 cases จริง = **0 REVIEW**.

### ⚠️ Prior = "เคยครบชุด" ไม่ใช่ "เคยฉีด" (bugfix 2026-08-07)

**คำนิยามที่ถูก:** `has_prior = True` เมื่อคนไข้เคยได้รับวัคซีน **ครบชุด** (IM≥5 / ID≥4 / Mixed≥4) มาก่อน
**ผิด (เดิม):** `has_prior = True` เมื่อคนไข้เคยฉีดวัคซีนแม้แค่ 1 เข็ม

บั๊กเดิมทำให้ 49 เคสที่ prior เป็นแค่ 1 เข็มตก "complete" ทั้งที่จริงต้องเป็น "incomplete"
แก้แล้ว: `annotate_prior()` ใช้ `is_complete_series()` กรองเฉพาะ prior case ที่ครบชุด

### 📅 Lookback 10 ปี (จำเป็นสำหรับ accuracy)

booster rule: "เคยครบชุด ≤180d = 1 เข้ม booster, ≥181d = 2 เข็ม" วัดจาก **complete series end date**
- คนไข้ที่ครบชุดเมื่อ 3 ปีก่อน แล้วมา booster ใน Q3 ปัจจุบัน → prior_days ≥181 → ต้อง 2 เข็ม
- ถ้า history มีแค่ Q1+Q2 (9 เดือน) → engine มองไม่เห็น complete series นั้น → has_prior=False → misclassify

**ดังนั้น:** ส่ง `--history` ย้อนหลัง **~10 ปี** (ถ้า HIS export ได้) เพื่อ accuracy สูงสุด
engine เตือน `⚠️ WARNING: history span < 1 year` ถ้าข้อมูลน้อยเกินไป

## 📄 Template + Filename (จำใน skill)

### Template (อ้างอิง)
```
drive/hospital-uthai/RabiesVacc/20260206_Template_RabiesReport.doc
```
(resolve ผ่าน `drive/` junction ของเครื่องนั้น — อย่า hardcode `L:\My Drive\...`)
ไฟล์นี้คือ template ว่างของ "แบบรายงานสรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้าและอิมมุโนโกลบุลิน"
มีตาราง 4 งวด × 9 ช่องนับ (ครบชุด/<5/ไม่ครบ × IM-ID + ERIG-HRIG)

### Output filename pattern
```
YYMMDD_rabiesvac.<HOSPITAL>_Y<YY>.doc
```
- `YYMMDD` = วันที่ทำรายงาน (CE, 2 หลักปี)
- `<HOSPITAL>` = ชื่อย่อโรงพยาบาล (เช่น `อุทัย`)
- `Y<YY>` = ปีงบประมาณ (พ.ศ. 2 หลักสุดท้าย, เช่น `Y69` = ปีงบ ๒๕๖๙)

**ตัวอย่าง:**
- `260807_rabiesvac.อุทัย_Y69.doc` = ทำวันที่ 7 ส.ค. 2026, ปีงบ 2569

⚠️ ใน public repo / log: ใช้ placeholder `<HOSPITAL>` ไม่ใช่ชื่อจริง (Iron Law #6)

## 🗄️ SQL version (ส่ง IT ให้ query จาก HIS ตรงๆ)

`scripts/hospital/classify_rabies.sql` — PostgreSQL (HosXP) equivalent ของ Python engine
- IT ปรับ 3 จุด: `icode` (item codes ของ rabies vaccine/ERIG), table names, period dates
- รันแล้ว export เป็น .csv → เทียบกับ Python engine ตัวเลขต้องตรง
- ถ้า REVIEW > 0 → ส่ง row นั้นกลับมาปรับ algorithm

## 🛠️ Workflow (4 ขั้น)

### ⭐ ขั้น 0 (สำคัญที่สุด — ห้ามลืม): รวบรวมข้อมูลย้อนหลัง 10 ปี

**ก่อนรัน engine ทุกครั้ง** ต้องมี history ครอบคลุม **10 ปีย้อนหลัง**
เพราะ booster rule ("เคยครบชุด ≤180d = 1 เข็ม / ≥181d = 2 เข็ม") วัดจาก complete series end date
คนไข้ที่ครบชุดเมื่อ 5 ปีก่อนแล้วมา booster ใน Q3 → prior_days ≥181 → ต้อง 2 เข็ม
ถ้า history มีแค่ Q1+Q2 (9 เดือน) → engine มองไม่เห็น → ตก incomplete ผิด

**ไฟล์ที่ต้องหาใน Google Drive:**
```
drive/hospital-uthai/RabiesVacc/
├── 2608010_Rabies_DB_<YYYY>.xls   ← ข้อมูลรายปี 2559-2568 (ไฟล์หลัก)
├── 251231_RabiesQ1.xls            ← Q1 ปีงบ ๖๘ (เมื่อปีก่อน)
├── 260331_RabiesQ2.xls            ← Q2 ปีงบ ๖๙ (Q ล่าสุดก่อนหน้า)
└── 260806_RabiesQ3.xls            ← Q3 ปีงบ ๖๙ (Q ปัจจุบันที่จะทำ)
```

**ถ้า user ส่งไฟล์ใหม่มา (Q4 หรือปีใหม่):**
1. อย่าเพิ่งรัน engine ด้วยไฟล์เดียว
2. หาไฟล์ history ย้อนหลัง 10 ปีใน `drive/hospital-uthai/RabiesVacc/`
3. ถ้าไม่ครบ → ขอ user export เพิ่ม
4. engine เตือน `⚠️ WARNING: history span < 1 year` ถ้าไม่พอ — **ห้าม ignore warning นี้**

### ขั้น 1-4: รัน engine + กรอก template

```bash
# 1. รวบ history ทั้งหมด (10 ปีย้อนหลัง + Q ที่ผ่านมา)
HISTORY=(
  "<drive>/RabiesVacc/2608010_Rabies_DB_2559.xls"
  "<drive>/RabiesVacc/2608010_Rabies_DB_2560.xls"
  # ... ครบถึง 2568
  "<drive>/RabiesVacc/251231_RabiesQ1.xls"
  "<drive>/RabiesVacc/260331_RabiesQ2.xls"
)

# 2. รัน engine ด้วย history เต็ม + Q ที่จะทำ
python scripts/hospital/classify_rabies.py \
  "<drive>/RabiesVacc/260806_RabiesQ3.xls" \
  --history "${HISTORY[@]}" \
  --period-start 2026-04-01 --period-end 2026-06-30

# 3. ตรวจ Mixed + REVIEW list (stderr)
#    - Mixed HN ทั้งหมด engine ตัดสินด้วย rule แล้ว — ดูเพื่อ audit
#    - REVIEW ควรเป็น 0; ถ้าไม่ใช่ แจ้ง user + ตรวจ data quality

# 4. กรอกตัวเลข 9-cell ลง template .doc
#    Template: <drive>/RabiesVacc/20260206_Template_RabiesReport.doc
#    Output:   <drive>/RabiesVacc/<yymmdd>_rabiesvac.<HOSPITAL>_Y<YY>.doc
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
- **A-Think**: confirmed 10-year history จำเป็น (booster detection)
- **Iron Laws**: #1 (test-first), #6 (privacy), #10 (registry), #11 (claim)
- **Related skills**: `a-doc` (สร้างเอกสารทั่วไป), `a-council` (review), `a-think` (reasoning)

## 🚀 Roadmap: Standalone Tool (PDPA-safe, ลด token, SaaS ในอนาคต)

> **เป้าหมาย**: แปลง engine + skill นี้เป็น **โปรแกรม** ที่ รพ. ใช้เอง
> ไม่ผ่าน AI Agent (ลด token) + ใช้ API ฟรีได้ + ขยายไป SaaS ได้

### ข้อกำหนด (Requirements)
- **PDPA-safe**: ข้อมูลคนไข้ไม่ออกจากเครื่อง รพ. (ไม่ส่งไป cloud LLM)
- **ลด token AI**: engine หลักทำงาน offline (pure Python) AI เข้ามาเฉพาะตอน
  generate report text / ตอบคำถาม user
- **Free AI API**: รองรับ OpenRouter free / Gemini Flash (ผ่าน cost-pyramid)
- **Data ingestion**: อัพโหลด xls/csv → บันทึก SQLite → dedup → query ได้
- **Report builder**: เลือก template + field mapping → generate .docx/.pdf
- **Extensible**: เพิ่ม report type ใหม่ได้ (ไม่ใช่แค่ rabies)

### Architecture (4 layers, MVP → SaaS)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: UI (FastAPI web + Jinja2 templates)                │
│   - อัพโหลดไฟล์ / เลือก template / ดูผล / export            │
│   - Local-only (http://localhost:8000) สำหรับ รพ.           │
│   - SaaS: deploy บน VPN/private cloud ถ้าขยาย               │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Report Engine (รวม classify_rabies.py + อนาคต)     │
│   - rabies-report (MVP — มีแล้ว)                             │
│   - vaccine-coverage (อนาคต)                                │
│   - adverse-event (อนาคต)                                   │
│   - custom-report-builder (อนาคต — เหมือน Jaspersoft)       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Data Store (SQLite — single file, PDPA-safe)       │
│   - tables: patients, doses, cases, reports, templates      │
│   - ingest() auto-detect schema + dedup by (hn,date,vac)    │
│   - query() SQL โดยตรง (เร็ว ไม่ต้องโหลดทั้งไฟล์)             │
│   - 10-year history อยู่ใน DB เดียว → prior lookup ทันที     │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: AI Adapter (optional — เรียกเมื่อต้องการ)           │
│   - Free API: OpenRouter free / Gemini Flash                │
│   - ใช้ตอน: สรุปรายงานเป็นภาษาไทย / ตอบคำถาม / QC          │
│   - ไม่ใช้ตอน: คำนวณตัวเลข (pure Python, ไม่ใช้ AI)         │
└─────────────────────────────────────────────────────────────┘
```

### MVP scope (ทำก่อน, 1-2 สัปดาห์)
- [ ] SQLite schema + `ingest.py` (dedup auto)
- [ ] `query.py` CLI (เลือก period → export 9-cell numbers)
- [ ] `fill_template.py` (map numbers → .docx template)
- [ ] ทดสอบ: อัพโหลด 10-year history ครั้งเดียว → query Q3 → ได้ report

### Phase 2 (1-2 เดือน)
- [ ] Web UI (FastAPI + Jinja2) — อัพโหลดผ่าน browser
- [ ] Multi-report (เพิ่ม report type อื่นที่ รพ. ทำประจำ)
- [ ] User auth (local, สำหรับเจ้าหน้าที่ รพ.)

### Phase 3 (SaaS — ถ้ามี รพ. อื่นสนใจ)
- [ ] Multi-tenant (แยก DB ต่อ รพ.)
- [ ] Deploy on private cloud (PDPA-compliant hosting)
- [ ] Billing / subscription

### 💡 ไอเดียเพิ่ม (เนื่องจากงาน รพ. ที่เห็น)
1. **OP-card/reimbursement report builder** — คล้าย rabies แต่เปลี่ยน table
2. **Auto-dedup + merge patient** — HN format เปลี่ยนข้ามปี (เห็นจริงใน 2559 vs 2560)
3. **Vaccine coverage heatmap** — เห็นพื้นที่/ช่วงเวลาที่ควรรณรงค์
4. **Adverse event tracker** — ติดตาม side effect หลังฉีด
5. **Drug inventory forecast** — คาดการใช้ ERIG/vaccine ต่อไตรมาส
6. **Thai form auto-fill** — เอกสาร สธ. อื่นๆ (เช่น รายงานโรค 506)
7. **PDPA audit log** — ใครเข้าถึงข้อมูลคนไข้เมื่อไหร่ (สำคัญสำหรับ compliance)
8. **Offline-first** — ทำงานได้แม้ HIS offline (สำคัญเพราะ HosXP มี downtime)

## 📝 Changelog

- **v1.0.0** (2026-08-07): initial — Q1+Q2+Q3 ปีงบ ๒๕๖๘-๖๙ ครบ, REVIEW=0, engine + template + skill
- **v1.1.0** (2026-08-10): bugfix prior=complete-series + 10-year lookback + FINAL numbers
- **v1.2.0** (2026-08-10): Roadmap section (standalone tool → SaaS)
- **v1.3.0** (2026-08-11): **5 bugfixes** (verified on Q3 + 4 specific HNs)
  - **#1 window 33d**: 28d → 33d (schedule 30d + CDC grace 3d); ก่อนหน้านี้ split Day-28 IM dose ที่มาสาย 1 วัน (HN 10217, 388351)
  - **#2 prior = ≥3 doses** (was IM≥5/ID≥4/mixed≥4): ตรงตาม DDC pre-exposure spec + screening app
  - **#3 screening merge**: รวมประวัติจาก screening app (คนไข้ที่ฉีดที่ รพ. อื่น)
  - **#4 abandoned-dose + restart detection**: HN 176434 — 1 เข็ม abandoned + 4 เข็ม clean restart (10/03→07/04 perfect ID schedule)
  - **#5 quarter straddle → defer to end_date quarter**: "ถ้าคาบเกี่ยวหรือข้ามไตรมาส ต้องยังไม่นับเคสนั้น ให้ขยับไป Q ถัดไป"
  - **Q3 v5 FINAL**: 337 cases (complete IM=23/ID=117, sub5 IM=16/ID=56, incomplete IM=18/ID=107, ERIG=110, HRIG=0)
  - **Files**: `drive/hospital-uthai/RabiesVacc/260811_rabiesvac.<HOSPITAL>_Y69_FINALv3.doc` + `.docx`
