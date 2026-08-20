---
name: a-rabies-report
description: "รายงานไตรมาสวัคซีนพิษสุนัขบ้าส่ง สธ.จังหวัดจาก Rabies_DB + Screening column H — นับรายเคส, รองรับเข็มสุดท้ายผิดนัด, history 10 ปี, lookahead, HN audit และ Word รวม Q1-Q4 เพียงไฟล์เดียวต่อปีงบประมาณที่ overwrite เมื่ออัปเดต. ใช้เมื่อกล่าวถึง rabies report, Rabies_DB, Screening, HN ฉีดไม่ครบ, รายงานจังหวัด, cleanup ไฟล์งาน หรือโปรแกรมรายงานแบบ offline"
version: 1.9.2
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

⚠️ **Screening ต้องสัมพันธ์กับเวลา:** เลือกเฉพาะคำตอบที่มีผลไม่เกิน `case.start_date`
ห้ามนำคำตอบที่ซักภายหลังไปเปลี่ยนรายงานไตรมาสก่อนหน้า (future leakage)
engine ปัจจุบันยัง collapse screening เหลือ 1 status ต่อ HN จึงต้องใช้ไฟล์ screening
cutoff รายไตรมาสจาก `04_audit/reproducibility_inputs/` เมื่อต้อง rerun งวดเก่า

⚠️ ค่า `ไม่เคยฉีดหรือเคยฉีดน้อยกว่า 3 เข็ม` เป็น **ambiguous** — สรุปได้เพียง
"ไม่มีหลักฐานครบชุดจาก screening" ห้ามรายงานว่า "ไม่เคยฉีดแน่นอน"

⚠️ **ต้องมีข้อมูลย้อนหลัง ≥180 วัน** — รายไตรมาส (90 วัน) ไม่พอ ต้องส่ง `--history` Q ก่อนหน้า + DB files 10 ปี

### Default rules (v1.7.0 — รวม delayed-dose, 33d window, abandoned-dose, straddle)
1. **Over-dose within 33d → complete** (เข็มเกิน = ครบ)
2. **IG-only** (ERIG/HRIG ไม่มี vaccine ใน 33d) → incomplete by age
3. **>33d gap → initial split, not final truth**: ถ้า case แรกขาดเข็มสุดท้ายเพียง 1 เข็ม และ case ถัดไปมีวัคซีน 1 เข็ม route เดียว ไม่มี ERIG/HRIG ใหม่ และห่างจากเข็มก่อน ≤31 วัน ให้ merge เป็นชุดเดิมที่ผิดนัด (เช่น IM 0,3,7,15,36 หรือ ID 0,3,28,38)
4. **Long/ambiguous delayed dose** → ห้าม restart อัตโนมัติ แต่ HIS ไม่มี exposure ID จึงต้อง screening/manual review; ห้าม merge ข้ามเดือน/ปีแบบเดา
5. **Abandoned dose + clean restart** → split (v1.3.0 bugfix #4)
6. **Quarter straddle** → case belongs to quarter of `start_date`; ต้องมี lookahead เพื่อเห็น continuation
7. **Mixed ID+IM**: total doses decide + age tiebreak for 2-3 dose cases
8. **Prior history** = complete series (≥3 doses) within 10y lookback: ≤180d = booster 1 dose, ≥181d = booster 2 doses

### ERIG/HRIG timing and episode identity (v1.7.0)

- ERIG/HRIG **ไม่ใช่ vaccine dose** และไม่ใช้ตัดสิน complete/sub5 ด้วยจำนวนเข็ม
- RIG อาจให้พร้อมเข็มแรกหรือไม่เกิน day 7 หลัง vaccine dose แรก จึงไม่จำเป็นต้องอยู่แถวแรกของ episode
- การพบ RIG ในวันหลัง vaccine dose แรกไม่ใช่เหตุผลให้ split case
- แต่ RIG ใหม่ที่อยู่กับ one-dose tail หลัง series เดิม เป็นหลักฐานเตือนว่าอาจเป็น exposure ใหม่ จึงไม่ auto-merge; ส่ง manual review
- อ้างอิง: WHO rabies position summary ระบุ delayed PEP ให้ resume ไม่ restart และให้ RIG ได้ถึง day 7 หลัง vaccine dose แรก

### Optional optimistic estimate — ต้องติดป้ายกำกับ (hospital decision 2026-08-14)

ใช้เฉพาะเมื่อผู้จัดทำรายงานสั่งชัดเจนว่าเป้าหมายคือค่าประมาณเชิงบวก:

- P1 = vaccine 1 dose, ไม่พบ prior complete ใน HIS/Screening
- ถ้ามี ERIG/HRIG → คง `incomplete`
- ถ้าไม่มี ERIG/HRIG → สมมติว่าเป็น booster หลังเคยครบชุดจากสถานบริการอื่น และนับ `complete`
- ต้องบันทึกเป็น `assumed external-history booster`; **ห้ามเขียนว่าเป็นประวัติยืนยันแล้ว** เพราะ absence of RIG ไม่ได้พิสูจน์ prior vaccination
- รายงาน Word/Excel/JSON ต้องมีคำว่า `ค่าประมาณ` หรือ `OPTIMISTIC` และเก็บ HN audit แยกใน private Drive

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
- hn: 388351   # Day-29 dose stays in one 33-day case; Q uses start_date
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
<drive>/hospital-<site>/RabiesVacc/02_templates/<template>.doc[x]
```
(resolve ผ่าน drive/junction ของเครื่องนั้น — อย่า hardcode drive letter หรือชื่อสถานพยาบาล)
ไฟล์นี้คือ template ว่างของ "แบบรายงานสรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้าและอิมมุโนโกลบุลิน"
มีตาราง 4 งวด × 9 ช่องนับ (ครบชุด/<5/ไม่ครบ × IM-ID + ERIG-HRIG)

### Output policy: one fiscal-year file only

- สร้าง Word เพียง **1 ไฟล์ต่อปีงบประมาณ** และให้มีแถว Q1-Q4 ครบในไฟล์เดียว
- ห้ามสร้าง Word แยก Q1, Q2, Q3 หรือ Q4
- ถ้ายังไม่มีข้อมูลบาง Q ให้คงแถวนั้นใน template และปล่อยช่องตัวเลขว่าง
- เมื่อมี Q ใหม่หรือแก้ตัวเลขของปีงบประมาณเดิม ให้ **overwrite ไฟล์ชื่อเดิม**
- ห้ามใส่วันที่, Q ล่าสุด, `v2`, `FINAL2` หรือ suffix แบบ versioned ในชื่อ Word หลัก
- เก็บ audit JSON/XLSX แยกได้ แต่ไม่ให้สร้าง Word รายงานเพิ่ม

### Stable output filename
```
<drive>/hospital-<site>/RabiesVacc/03_reports/current/rabiesvac. <HOSPITAL>_Y<YY>.docx
```
- `Y<YY>` = ปีงบประมาณ (พ.ศ. 2 หลักสุดท้าย, เช่น `Y69` = ปีงบ ๒๕๖๙)

### Numeric cell formatting

- ตัวเลขผลรายงานทุกช่องในแถว Q1-Q4 ให้ใช้ฟอนต์ **`THSarabunIT๙` ขนาด 16 pt**
- ใช้ชื่อ family ภายในของ Windows/Word ว่า `THSarabunIT๙` **ไม่มีช่องว่างหลัง TH**; ห้ามใช้ `TH SarabunIT๙` เพราะ Word จะ fallback
- กำหนด run font ให้ครบ `ascii`, `hAnsi`, `eastAsia` และ `cs` เพื่อไม่ให้ Word fallback ไปใช้ฟอนต์อื่น
- ตรวจจาก OOXML ว่า `w:rFonts` เป็น `THSarabunIT๙` และ `w:sz`/`w:szCs` เท่ากับ `32` half-points

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

**ไฟล์ที่ต้องหาใน private drive:**
```
<drive>/hospital-<site>/RabiesVacc/
├── 01_source/annual/              ← HIS รายปี 10 ปีย้อนหลัง (source of truth)
├── 01_source/quarterly/           ← Q ปัจจุบัน/fixture ที่ต้องเก็บเพื่อ rerun
├── 01_source/screening/           ← ประวัติจากการซัก รวมสถานบริการอื่น
└── 04_audit/reproducibility_inputs/ ← lookahead + screening cutoff ของแต่ละงวด
```

**ถ้า user ส่งไฟล์ใหม่มา (Q4 หรือปีใหม่):**
1. อย่าเพิ่งรัน engine ด้วยไฟล์เดียว
2. หาไฟล์ history ย้อนหลัง 10 ปีใน `01_source/annual/`
3. ถ้าไม่ครบ → ขอ user export เพิ่ม
4. engine เตือน `⚠️ WARNING: history span < 1 year` ถ้าไม่พอ — **ห้าม ignore warning นี้**

### ขั้น 0.5: Verify regression HNs (anti-hallucination gate — ห้ามข้าม)

**ก่อนรัน engine ทุกครั้ง** ให้ verify ว่า engine ยังคลาสสิฟาย 5 pinned HNs ถูก:

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
  "<drive>/hospital-<site>/RabiesVacc/01_source/annual/<Rabies_DB_2559>.xls"
  "<drive>/hospital-<site>/RabiesVacc/01_source/annual/<Rabies_DB_2560>.xls"
  # ... ครบถึง 2568
)

# 2. รัน engine ด้วย history เต็ม + screening + lookahead + Q ที่จะทำ
#    v1.5.0: --lookahead (เดือนแรกของ Q ถัดไป) และ --screening REQUIRED
#    ถ้าไม่มี engine จะ warn loudly (false-positive incomplete risk)
python scripts/hospital/classify_rabies.py \
  "<drive>/hospital-<site>/RabiesVacc/01_source/quarterly/<current_Q>.xls" \
  --history "${HISTORY[@]}" \
  --screening "<drive>/hospital-<site>/RabiesVacc/04_audit/reproducibility_inputs/<screening_cutoff>.xlsx" \
  --lookahead "<drive>/hospital-<site>/RabiesVacc/04_audit/reproducibility_inputs/<next_Q_first_month>.xlsx" \
  --strict-history \
  --period-start 2026-04-01 --period-end 2026-06-30

# 3. ตรวจ Mixed + REVIEW list (stderr)
#    - Mixed HN ทั้งหมด engine ตัดสินด้วย rule แล้ว — ดูเพื่อ audit
#    - REVIEW ควรเป็น 0; ถ้าไม่ใช่ แจ้ง user + ตรวจ data quality

# 4. กรอกตัวเลขลงแถว Q ที่เกี่ยวข้องใน Word รวม Q1-Q4 ของปีงบประมาณนั้น
#    Template: <drive>/hospital-<site>/RabiesVacc/02_templates/<template>.doc[x]
#    Output:   <drive>/hospital-<site>/RabiesVacc/03_reports/current/rabiesvac. <HOSPITAL>_Y<YY>.docx
#    ถ้าไฟล์มีอยู่แล้วให้ overwrite; ห้ามสร้างไฟล์แยกราย Q

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

## 🧹 Workspace + token-efficient operation

- ใช้โครงสร้างและขั้นตอน cleanup ใน `references/workspace-layout.md`
- อ่าน `README.md` + manifest ก่อน; ไม่ scan `_archive/` ทั้งหมดโดยไม่จำเป็น
- ให้ deterministic scripts อ่านข้อมูลเต็ม แล้วส่งเฉพาะ aggregate/รายการ audit ที่เล็กที่สุดให้ AI
- HN จริงอยู่ใน private drive เท่านั้น; evals และเอกสารใน repo ใช้ synthetic/masked data

## 📁 ไฟล์ในงานนี้

| ไฟล์ | หน้าที่ | ที่อยู่ |
|---|---|---|
| `scripts/hospital/classify_rabies.py` | classification engine | repo (public-safe) |
| `<drive>/hospital-<site>/RabiesVacc/01_source/` | HIS + screening sources | private drive |
| `<drive>/hospital-<site>/RabiesVacc/02_templates/` | template ราชการว่าง | private drive |
| `<drive>/hospital-<site>/RabiesVacc/03_reports/` | pending + final reports | private drive |
| `<drive>/hospital-<site>/RabiesVacc/04_audit/current/` | breakdown, Mixed, HN audit | private drive |
| `<drive>/hospital-<site>/RabiesVacc/04_audit/reproducibility_inputs/` | cutoff + lookahead สำหรับ rerun | private drive |

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

## 🚀 Standalone tool

เป้าหมายคือโปรแกรม local/offline ที่คำนวณด้วย deterministic engine, เก็บ lineage
ใน SQLite และใช้ AI เฉพาะงานภาษา/ช่วยเหลือแบบ optional ดู data model, temporal
screening rule, MVP และ acceptance gates ที่ `references/standalone-blueprint.md`

## 📝 Changelog

- **v1.9.2** (2026-08-14): fix Word font-family fallback
  - แก้ชื่อ family จาก `TH SarabunIT๙` เป็นชื่อที่ Windows ลงทะเบียนจริง `THSarabunIT๙` เพื่อไม่ให้ Word fallback
- **v1.9.1** (2026-08-14): stable hospital filename
  - ใช้ `rabiesvac. <HOSPITAL>_Y<YY>.docx` เป็นชื่อ Word คงที่ของปีงบประมาณ
- **v1.9.0** (2026-08-14): report-number typography
  - กำหนดตัวเลขทุกช่อง Q1-Q4 เป็น `TH SarabunIT๙` 16 pt ทั้ง Latin, East Asian และ complex-script font attributes
- **v1.8.0** (2026-08-14): annual single-file overwrite policy
  - หนึ่งปีงบประมาณมี Word รายงานหลักเพียงไฟล์เดียว และต้องมีแถว Q1-Q4 ครบ
  - อัปเดตปีเดิมโดย overwrite stable filename; ห้าม Word แยก Q หรือ versioned filename
- **v1.7.0** (2026-08-14): delayed final dose + ERIG timing + optimistic P1 mode
  - merge IM4+late IM1 / ID3+late ID1 เมื่อ route เดียว ไม่มี RIG ใหม่ และ gap จากเข็มก่อน ≤31 วัน
  - แก้ double-count ของชุดผิดนัดที่ถูก 33-day window แยกเป็น sub5 + booster case
  - บันทึกว่า delayed PEP ให้ resume ไม่ restart; ERIG ไม่จำเป็นต้องอยู่วันแรก แต่ให้ได้ถึง day 7 หลัง vaccine dose แรก
  - เพิ่ม optional optimistic P1 rule: no ERIG one-dose → assumed external-history booster; ต้องติดป้าย assumption และเก็บ audit
  - 82 focused tests pass; 5 pinned regression HNs pass
- **v1.6.0** (2026-08-13): private workspace + standalone readiness
  - เพิ่ม canonical workspace, SHA-256 inventory และ recoverable archive procedure
  - บันทึก screening temporal rule; ห้าม future leakage และห้ามตีความ `none_or_lt3` ว่าไม่เคยฉีดแน่นอน
  - เพิ่ม standalone blueprint และ evals สำหรับ missing inputs, HN audit, HIS-only, cleanup และ temporal screening
  - แก้ default quarter rule ให้ตรง v1.5.0: นับด้วย `start_date` + lookahead
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
  - **Files**: `<private-drive>/hospital-<site>/RabiesVacc/<report-v3>.doc[x]`
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
  - **Files**: `<private-drive>/hospital-<site>/RabiesVacc/<report-v4>.doc[x]`
  - 61 unit tests pass (45 original + 11 v1.3.0 + 5 v1.3.1 screening)
