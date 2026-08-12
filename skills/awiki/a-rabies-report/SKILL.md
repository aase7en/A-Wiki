---
name: a-rabies-report
description: "รายงานไตรมาสพิษสุนัขบ้าส่ง สธ.จังหวัด — นับรายเคส, 9-cell, prior=complete-series (10y lookback), 33d first-dose-anchored window + abandoned-dose detection + quarter-straddle deferral. Engine: scripts/hospital/classify_rabies.py + .sql. Roadmap: standalone PDPA-safe tool"
version: 1.5.0
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

### 🆕 v1.5.0 (2026-08-12): Quarter assignment = START_DATE rule + lookahead required

> **กฎของโรงพยาบาล (user clarification):** "Q ใดๆ ถ้าเหตุการณ์นั้นถูกใช้ไปแล้ว จะไม่ถูกนำมารายงานใน Q ถัดไป"
> + "เหตุการณ์มันเริ่มต้นที่ Q3 เลยต้องรายงานในส่วนของ Q3"

- Case เริ่มใน Q ไหน นับ Q นั้น (no double-count)
- Case 25/06→05/07 (start Q3, end Q4) → นับ **Q3** (start quarter)
- Case 10/03→07/04 (start Q2, end Q3) → นับ **Q2** (start quarter, **reverts bugfix #5**)

⚠️ **Reverts bugfix #5 (v1.3.0)**: end_date rule ถูกแทนที่ด้วย start_date rule
เพราะ use case จริงคือ "คนไข้มาปลาย Q + continuation Q ถัดไป → รายงาน Q ที่เริ่ม"

⚠️ **Lookahead data REQUIRED**: ถ้าไม่มี `--lookahead FILE` (เดือนแรกของ Q ถัดไป)
engine จะมี false-positive incomplete ~40 cases/Q3 (cases ที่ continuation ใน Q ถัดไป
แต่ engine ไม่เห็น doses นั้น → classify เป็น incomplete)

⚠️ **Screening data REQUIRED**: ถ้าไม่มี `--screening FILE` engine จะมี false-positive
incomplete ~20 cases/Q3 (booster cases ที่ prior อยู่ใน screening file เท่านั้น)

**Implementation**: period filter ใช้ `start_date` (default); `--lookahead` + `--screening`
optional but engine warns loudly if missing

## 🎯 Algorithm (canonical, verified 2026-08-07 — 0 REVIEW across 916 cases)

### Prior history (booster) — v1.2.0+ bugfix #2
"Prior" = **complete rabies vaccination series** (≥3 doses ID+IM combined) ก่อน start_date ของ case ปัจจุบัน
- ≥3 doses = complete series (ตาม DDC pre-exposure 3-dose spec + screening app "เคยฉีด 3 เข็ม หรือมากกว่า")
- ≤180 วัน → booster ต้องการ **1 เข็ม** ใน case นี้
- ≥181 วัน → booster ต้องการ **2 เข็ม** ใน case นี้

**2 แหล่ง prior:**
1. HIS data (lookback 10 ปี จาก `--history`)
2. Screening app (ผู้ป่วยที่ฉีดที่โรงพยาบาลอื่น — `--screening` file) — บอก near/far ด้วย:
   - "ภายใน 6 เดือน" → near (≤180d, ต้องการ 1 เข็ม booster)
   - "เกิน 6 เดือน" → far (≥181d, ต้องการ 2 เข็ม booster)
3. HIS prior ชนะ screening เมื่อมีทั้งคู่ (รู้วันที่แน่ชัดกว่า)

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

## 🛡️ Anti-hallucination defenses (v1.4.0 — 5 layers)

> 10-year history (29,325 doses) ใหญ่เกินกว่า AI จะอ่านทั้งหมดแล้วไม่หลอน
> Audit 2026-08-12 เจอ hallucination vectors 13 ตัว → ใส่ layered defense

### Layer 1: In-engine assertions (always on)
```python
# classify_rabies.py มี asserts 5 ตัว (V1-V12):
# - V3 sum-of-cells: complete+sub5+incomplete+review == len(in_period)
# - V4 ERIG/HRIG ≤ total cases
# - V10 dose-conservation in refine_clusters_cross_window
# - V1+V2 dead-code removal + unreachability assertion
# - V12 empty-period alarm
# - V9 --strict-history flag (promotes <1y warning to SystemExit)
```

### Layer 2: Post-run output hook `check_rabies_report.py`
- Fires on Write/Edit to `**/rabiesvac*.json`
- Validates JSON schema + sum-of-cells + ERIG/HRIG + cat/route enum
- Catches AI hand-editing JSON (engine asserts don't fire if engine didn't run)
- Override: `HOOK_SKIP=check_rabies_report`

### Layer 3: Regression ground truth `scripts/hospital/regression_HNs.yaml`
5 pinned HNs (machine-loadable, single source of truth):
```yaml
- hn: 176434   # abandoned dose + clean restart (bugfix #4)
- hn: 142753   # multi-year scattered must NOT merge (bugfix #4 audit)
- hn: 10217    # Day-28 IM 1d late stays 1 case (bugfix #1)
- hn: 359258   # prior = complete series ≥3 doses (bugfix #2)
- hn: 388351   # quarter straddle → end_date quarter (bugfix #5)
```
Verify: `python scripts/hospital/verify_regression.py` (exit 0 = pass, 2 = regression)

### Layer 4: Durable bug memory (memory_ledger)
- 6 lesson entries with `tags=["rabies","rabies-engine","<bug-class>","regression"]`
- `recall_on_prompt.py` auto-injects when prompt mentions "rabies", "screening", "dtype"
- Verified: search "rabies screening dtype" → BM25 score 18.29 (≥5.0 threshold)
- After 3+ same-tagged failures, `a_loop_distill.py` auto-proposes `guard-rabies-*` skill

### Layer 5: Brain-gate medical amendment
- `docs/protocols/brain-improvement-gate.md` Medical/PHI-specific rules (M1-M5)
- Dual-file pattern for ground truth (public masked + drive raw)
- Brain Gate block for medical changes (PHI source / public surface / validation / regression)

### Principle (สำคัญ)
**AI invokes deterministic scripts; AI does NOT read 29,325 rows directly.**
Bug memory lives in files (YAML + ledger), not in AI session context.

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

### ขั้น 0.5: Verify regression HNs (anti-hallucination gate — ห้ามข้าม)

**ก่อกรัน engine ทุกครั้ง** ให้ verify ว่า engine ยังคลาสสิฟาย 5 pinned HNs ถูก:

```bash
python scripts/hospital/verify_regression.py
# exit 0 = pass, exit 2 = regression detected — ห้ามรัน engine จนกว่าจะแก้
# 5 pinned HNs: 176434, 142753, 10217, 359258, 388351
# Override (emergencies only): SKIP_REGRESSION=1
```

ถ้า regression → แก้ engine ก่อน อย่าแก้ YAML โดยไม่เข้าใจ root cause
(YAML = expected behavior; engine = actual behavior; ถ้าไม่ตรง = engine bug)

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

# 2. รัน engine ด้วย history เต็ม + screening + lookahead + Q ที่จะทำ
#    v1.5.0: --lookahead (เดือนแรกของ Q ถัดไป) และ --screening REQUIRED
#    ถ้าไม่มี engine จะ warn loudly (false-positive incomplete risk)
python scripts/hospital/classify_rabies.py \
  "<drive>/RabiesVacc/260806_RabiesQ3.xls" \
  --history "${HISTORY[@]}" \
  --screening "<drive>/RabiesVacc/260810_Rabies_Screening.xls" \
  --lookahead "<drive>/RabiesVacc/<next_Q_first_month>.xls" \
  --strict-history \
  --period-start 2026-04-01 --period-end 2026-06-30

# 3. ตรวจ Mixed + REVIEW list (stderr)
#    - Mixed HN ทั้งหมด engine ตัดสินด้วย rule แล้ว — ดูเพื่อ audit
#    - REVIEW ควรเป็น 0; ถ้าไม่ใช่ แจ้ง user + ตรวจ data quality

# 4. กรอกตัวเลข 9-cell ลง template .doc
#    Template: <drive>/RabiesVacc/20260206_Template_RabiesReport.doc
#    Output:   <drive>/RabiesVacc/<yymmdd>_rabiesvac.<HOSPITAL>_Y<YY>.doc

# 5. Post-run invariant validation (anti-hallucination Layer 2)
#    ใน Claude Code: hook ทำงานอัตโนมัติเวื่อ Write/Edit JSON
#    ตรวจสอบด้วยตนเอง (manual check นอก Claude):
python scripts/hooks/check_rabies_report.py < <json_file>
# exit 2 = invariant violated (sum-of-cells, schema, etc.) — ห้าม commit
```

### 🆕 Step 5b: Append bug memory (เมื่อเจอ bug ใหม่)

ถ้ารัน engine แล้วเจอ HN ที่คลาสสิฟายผิด ให้:
1. **Append YAML entry** — `scripts/hospital/regression_HNs.yaml` (timeline + expected)
2. **Run verify** — `python scripts/hospital/verify_regression.py` ต้อง exit 0
3. **Append ledger lesson** — บันทึก root cause + fix + HN + tags `["rabies","rabies-engine","<bug-class>","regression"]`
4. **Add unit test** — `tests/test_classify_rabies.py` (parametrize from YAML ถ้าทำได้)
5. **Commit** — "fix(rabies): bugfix #N — <1-line description>"

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
- **v1.5.0** (2026-08-12): **start_date rule + lookahead + screening required**
  - **Reverts bugfix #5 (v1.3.0)**: end_date rule → start_date rule
  - User clarification: "Q ใดๆ ถ้าเหตุการณ์นั้นถูกใช้ไปแล้ว จะไม่ถูกนำมารายงานใน Q ถัดไป"
  - Case 25/06→05/07 (start Q3, end Q4) → นับ Q3 (was Q4 under end_date rule)
  - Case 10/03→07/04 (start Q2, end Q3) → นับ Q2 (was Q3 — reverts HN 176434 assignment)
  - **`--lookahead FILE` ใหม่**: load เดือนแรกของ Q ถัดไป (e.g. Jul data เมื่อ report Q3)
    จำเป็นเพื่อ complete picture — ไม่มี → ~40 false-positive incomplete cases
  - **`--screening FILE` ใหม่ strongly recommended**: false-positive incomplete ~20 cases
  - Engine emits 🚨 loud warnings when lookahead or screening missing
  - **Q3 v7** (start_date rule, no lookahead yet): 295 cases
    - complete IM=16/ID=115, sub5 IM=15/ID=51, incomplete IM=16/ID=82, ERIG=95
    - 42 cases ที่ straddle Q2→Q3 ย้ายไป Q2 (was 337 under end_date rule)
    - **PENDING**: Jul lookahead data → reclassify at-risk cases → final numbers
  - 78 tests pass (77 + 1 new straddle test for start_date rule)
- **v1.4.0** (2026-08-12): **Anti-hallucination layer — 5 layers, 13 vectors mitigated**
  - Audit found 13 hallucination vectors in engine (V1-V13) when processing 10-year history
  - **Layer 1**: In-engine assertions — sum-of-cells invariant, ERIG/HRIG sanity, dose-conservation, dead-code removal (V1 `ig_only` + V2 `REVIEW/MIXED`), `--strict-history` flag (V9), `load_xls` dedupe (V7), empty-period alarm (V12)
  - **Layer 2**: `scripts/hooks/check_rabies_report.py` — post-run hook validates JSON output (V13)
  - **Layer 3**: `scripts/hospital/regression_HNs.yaml` — 5 pinned HNs (176434, 142753, 10217, 359258, 388351) as single source of truth + `verify_regression.py` post-flight verifier
  - **Layer 4**: 6 lesson entries in memory_ledger with `rabies-*` tags (auto-recall BM25=18.29 verified)
  - **Layer 5**: `docs/protocols/brain-improvement-gate.md` medical/PHI amendment (rules M1-M5)
  - Principle: AI invokes deterministic scripts; AI does NOT read 29k rows directly. Bug memory lives in files.
  - Tests: 77 pass (61 original + 14 hook + 2 regression wrapper)
- **v1.3.1** (2026-08-11): **2 more bugfixes** (incomplete was inflated by 21 cases)
  - **#6 `--screening` CLI flag was missing**: `annotate_prior()` had `screening_prior` parameter but no CLI/run/main() wiring → engine never read screening file in actual pipeline. Added `--screening FILE` flag + `load_screening()` helper.
  - **#7 HN dtype mismatch**: screening xls has HN as `float64` (175925.0); HIS HN is `str` ("175925"). Direct string comparison failed → 0 overlap. Fixed by `str(int(...))` normalization in `load_screening()`.
  - **Near/far split from screening**: screening file has 2 prior-status values:
    - "เคยฉีด 3 เข็ม หรือมากกว่า (ภายใน 6 เดือน)" → prior_days_ago=180 (near, 1-dose booster)
    - "เคยฉีด 3 เข็ม หรือมากกว่า (เกิน 6 เดือน)" → prior_days_ago=181 (far, 2-dose booster)
  - **Q3 v6 FINAL**: 337 cases (same total — screening reclassifies 21 incomplete→complete)
    - complete IM=24/ID=137 (+1/+20 vs v5)
    - sub5 IM=16/ID=56 (unchanged)
    - incomplete IM=17/ID=87 (−1/−20 vs v5) — **real** (69 cases = 1-dose lost-to-follow-up, 34 = 2-dose partial, 1 = IG-only)
  - **Files**: `drive/hospital-uthai/RabiesVacc/260812_rabiesvac.<HOSPITAL>_Y69_FINALv4.doc` + `.docx`
  - 61 unit tests pass (45 original + 11 v1.3.0 + 5 v1.3.1 screening)
