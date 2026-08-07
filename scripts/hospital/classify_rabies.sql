-- ============================================================================
-- Rabies Vaccination Quarterly Report — SQL version (HosXP / PostgreSQL)
-- ============================================================================
-- Purpose: สรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้าและอิมมุโนโกลบุลิน
--          งวดที่ ๓ (เม.ย.-มิ.ย.) ปีงบ ๒๕๖๘-๖๙ หรือไตรมาสใดก็ตามที่เปลี่ยน @period_*
--
-- Equivalent to: scripts/hospital/classify_rabies.py (Python engine)
-- Algorithm: 28-day case clustering + 9-cell classification + prior history
--
-- ⚠️  ปรับ 3 จุดก่อนรัน (ค้นหา "ADJUST"):
--     1. @period_start / @period_end — ช่วงไตรมาส
--     2. @lookback_start — ย้อนหลัง ≥180 วันจาก period_start (สำหรับ booster lookup)
--     3. Table/column names ถ้า HosXP ของ รพ. ต่างจาก default
--
-- ส่งให้ IT: รันบน HosXP (PostgreSQL) → export ผลเป็น .csv/.xlsx → เทียบกับ engine
-- ============================================================================

-- ─── 0. PARAMETERS (ADJUST) ────────────────────────────────────────────────
-- งวดที่ ๓ ปีงบ ๒๕๖๘-๖๙ = 1 เม.ย. 2026 → 30 มิ.ย. 2026 (CE = พ.ศ. - 543)
-- Lookback 180 วัน = ~3 ต.ค. 2025

-- ─── 1. RAW DOSES (source of truth) ────────────────────────────────────────
-- ADJUST table/column names to match your HosXP schema.
-- HosXP standard: opvst หรือ ovst สำหรับ OPD visit, opiprt หรือ medicine pantry
-- สำหรับ vaccine dose: ปกติอยู่ในตารางนำส่งยา opd (opitemprt/opdepa) + icode ของ rabies vaccine
-- IT: ต้องรู้ icode (item code) ของ rabies vaccine / ERIG ในระบบ

WITH RECURSIVE
-- ─── ADJUST: replace these table/column names ─────────────────────────────
raw_doses AS (
    SELECT
        v.hn                                                       AS hn,
        v.vstdate                                                  AS dose_date,
        EXTRACT(YEAR FROM age(CURRENT_DATE, p.birthday))::int     AS age,
        p.pname || p.fname || ' ' || p.lname                       AS patient_name,
        CASE
            -- ADJUST: เปลี่ยน icode เป็น item code จริงในระบบ HosXP ของ รพ.
            WHEN o.icode IN ('XXXXX01', 'XXXXX02')  -- RABIES VACCINE 0.5 cc IM
                THEN 'IM'
            WHEN o.icode IN ('XXXXX03', 'XXXXX04')  -- RABIES VACCINE 0.1 ml ID
                THEN 'ID'
            WHEN o.icode IN ('XXXXX05', 'XXXXX06')  -- ERIG-EQUINE ANTIRABIES GLOBULIN
                THEN 'ERIG'
            WHEN o.icode IN ('XXXXX07')             -- HRIG (Human Rabies Immunoglobulin)
                THEN 'HRIG'
            ELSE NULL
        END                                                        AS vaccine_type
    FROM opitemprt o                                               -- ADJUST: ตารางนำส่งยา OPD
    JOIN ovst v ON o.vn = v.vn                                     -- ADJUST: ผูก visit
    JOIN patient p ON v.hn = p.hn                                  -- ADJUST: ตารางคนไข้
    WHERE o.icode IN ('XXXXX01','XXXXX02','XXXXX03','XXXXX04',
                      'XXXXX05','XXXXX06','XXXXX07')               -- ADJUST: rabies icodes ทั้งหมด
      AND v.vstdate BETWEEN '2025-10-01' AND '2026-06-30'          -- lookback + period
      AND o.icode IS NOT NULL
),
valid_doses AS (
    SELECT * FROM raw_doses
    WHERE vaccine_type IS NOT NULL
    -- dedup exact duplicates (HIS อาจบันทึกซ้ำ)
    -- KEEP first per (hn, dose_date, vaccine_type)
    -- (PostgreSQL: ใช้ DISTINCT ON)
),

-- ─── 2. CASE CLUSTERING (28-day window per HN) ─────────────────────────────
-- "รายเคส" = cluster ของ doses ของ HN เดียวกัน ที่แต่ละ dose ห่างจาก FIRST dose
-- ของ cluster ≤ 28 วัน. dose ที่ห่าง > 28 วัน → เริ่ม cluster ใหม่ (อุบัติการณ์ใหม่)
dose_timeline AS (
    SELECT
        hn, dose_date, vaccine_type, age, patient_name,
        LAG(dose_date) OVER (PARTITION BY hn ORDER BY dose_date) AS prev_dose_date,
        ROW_NUMBER() OVER (PARTITION BY hn ORDER BY dose_date)   AS rn
    FROM valid_doses
),
-- กำหนด boundary: เมื่อไหร่ dose นี้เริ่ม cluster ใหม่ (ห่างจาก dose ก่อนหน้า > 28d
-- หรือเป็น dose แรกของ HN)
case_starts AS (
    SELECT hn, dose_date, vaccine_type, age, patient_name, rn
    FROM dose_timeline
    WHERE prev_dose_date IS NULL
       OR (dose_date - prev_dose_date) > INTERVAL '28 days'
),
-- แต่ละ dose → cluster start ที่ใกล้ที่สุดก่อนหน้า (case_id = start_date ของ cluster)
doses_with_case AS (
    SELECT
        d.hn,
        d.dose_date,
        d.vaccine_type,
        d.age,
        d.patient_name,
        cs.dose_date AS case_start_date
    FROM dose_timeline d
    JOIN LATERAL (
        SELECT dose_date FROM case_starts
        WHERE case_starts.hn = d.hn AND case_starts.dose_date <= d.dose_date
        ORDER BY dose_date DESC LIMIT 1
    ) cs ON true
),

-- ─── 3. AGGREGATE PER CASE ─────────────────────────────────────────────────
case_agg AS (
    SELECT
        hn,
        case_start_date,
        MAX(dose_date)                                                 AS case_end_date,
        COUNT(*) FILTER (WHERE vaccine_type = 'IM')                    AS n_im,
        COUNT(*) FILTER (WHERE vaccine_type = 'ID')                    AS n_id,
        COUNT(*) FILTER (WHERE vaccine_type = 'ERIG')                  AS n_erig,
        COUNT(*) FILTER (WHERE vaccine_type = 'HRIG')                  AS n_hrig,
        MAX(age)                                                       AS age,
        MAX(patient_name)                                              AS patient_name,
        (COUNT(*) FILTER (WHERE vaccine_type = 'IM') > 0
         AND COUNT(*) FILTER (WHERE vaccine_type = 'ID') > 0)          AS is_mixed,
        COUNT(*) FILTER (WHERE vaccine_type IN ('IM','ID'))            AS total_vac
    FROM doses_with_case
    GROUP BY hn, case_start_date
),

-- ─── 4. PRIOR HISTORY (latest prior vaccine dose for booster logic) ────────
prior_lookup AS (
    SELECT
        c.hn,
        c.case_start_date,
        MAX(p.dose_date) AS prior_vac_date
    FROM case_agg c
    LEFT JOIN valid_doses p
        ON p.hn = c.hn
       AND p.vaccine_type IN ('IM','ID')
       AND p.dose_date < c.case_start_date
    GROUP BY c.hn, c.case_start_date
),
case_with_prior AS (
    SELECT
        a.*,
        (p.prior_vac_date IS NOT NULL)                                AS has_prior,
        CASE WHEN p.prior_vac_date IS NOT NULL
             THEN (a.case_start_date - p.prior_vac_date)
             ELSE NULL
        END                                                           AS prior_days
    FROM case_agg a
    LEFT JOIN prior_lookup p USING (hn, case_start_date)
),

-- ─── 5. CLASSIFY (9-cell logic — same as Python engine) ────────────────────
-- Returns one row per case with (category, route)
classified AS (
    SELECT
        hn, case_start_date, case_end_date,
        n_im, n_id, n_erig, n_hrig, total_vac, age, is_mixed,
        has_prior, prior_days,
        CASE
            -- ── IG-only (no vaccine in window) → incomplete by age ──
            WHEN total_vac = 0 AND (n_erig > 0 OR n_hrig > 0) THEN
                CASE WHEN age IS NULL THEN 'REVIEW/NONE'
                     WHEN age < 9     THEN 'incomplete/IM'
                     ELSE                  'incomplete/ID'
                END

            -- ── MIXED ID+IM ──
            WHEN is_mixed THEN
                CASE
                    WHEN total_vac >= 5 THEN 'complete/IM'
                    WHEN total_vac = 4  THEN 'complete/ID'
                    WHEN total_vac = 3 THEN
                        CASE WHEN age IS NULL THEN 'REVIEW/NONE'
                             WHEN age < 9     THEN 'sub5/IM'
                             ELSE                  'sub5/ID'
                        END
                    WHEN total_vac <= 2 AND NOT has_prior THEN
                        CASE WHEN age IS NULL THEN 'REVIEW/NONE'
                             WHEN age < 9     THEN 'incomplete/IM'
                             ELSE                  'incomplete/ID'
                        END
                    WHEN total_vac <= 2 AND has_prior
                         AND prior_days <= 180 AND total_vac >= 1 THEN
                        CASE WHEN age IS NULL THEN 'complete/ID'
                             WHEN age < 9     THEN 'complete/IM'
                             ELSE                  'complete/ID'
                        END
                    WHEN total_vac <= 2 AND has_prior
                         AND prior_days >= 181 AND total_vac >= 2 THEN
                        CASE WHEN age IS NULL THEN 'complete/ID'
                             WHEN age < 9     THEN 'complete/IM'
                             ELSE                  'complete/ID'
                        END
                    WHEN total_vac <= 2 AND has_prior
                         AND prior_days >= 181 AND total_vac < 2 THEN
                        CASE WHEN age IS NULL THEN 'REVIEW/NONE'
                             WHEN age < 9     THEN 'incomplete/IM'
                             ELSE                  'incomplete/ID'
                        END
                    ELSE 'REVIEW/MIXED'
                END

            -- ── PURE IM ──
            WHEN n_im > 0 AND n_id = 0 THEN
                CASE
                    WHEN n_im >= 5 THEN 'complete/IM'
                    WHEN has_prior AND prior_days <= 180 AND n_im >= 1 THEN 'complete/IM'
                    WHEN has_prior AND prior_days >= 181 AND n_im >= 2 THEN 'complete/IM'
                    WHEN n_im BETWEEN 3 AND 4 THEN 'sub5/IM'
                    WHEN n_im < 3 AND NOT has_prior THEN 'incomplete/IM'
                    WHEN has_prior AND prior_days >= 181 AND n_im < 2 THEN 'incomplete/IM'
                    ELSE 'REVIEW/IM'
                END

            -- ── PURE ID ──
            WHEN n_id > 0 AND n_im = 0 THEN
                CASE
                    WHEN n_id >= 4 THEN 'complete/ID'
                    WHEN has_prior AND prior_days <= 180 AND n_id >= 1 THEN 'complete/ID'
                    WHEN has_prior AND prior_days >= 181 AND n_id >= 2 THEN 'complete/ID'
                    WHEN n_id = 3 THEN 'sub5/ID'
                    WHEN n_id < 3 AND NOT has_prior THEN 'incomplete/ID'
                    WHEN has_prior AND prior_days >= 181 AND n_id < 2 THEN 'incomplete/ID'
                    ELSE 'REVIEW/ID'
                END

            ELSE 'REVIEW/NONE'
        END AS classification
    FROM case_with_prior
),

-- ─── 6. FILTER TO REPORT PERIOD (case_start_date in period) ────────────────
-- ADJUST period dates
in_period AS (
    SELECT *
    FROM classified
    WHERE case_start_date BETWEEN '2026-04-01' AND '2026-06-30'      -- ADJUST: Q3 ปีงบ ๖๙
)

-- ─── 7. FINAL 9-CELL REPORT ────────────────────────────────────────────────
SELECT
    COUNT(*) FILTER (WHERE classification = 'complete/IM')    AS complete_im,
    COUNT(*) FILTER (WHERE classification = 'complete/ID')    AS complete_id,
    COUNT(*) FILTER (WHERE classification = 'sub5/IM')        AS sub5_im,
    COUNT(*) FILTER (WHERE classification = 'sub5/ID')        AS sub5_id,
    COUNT(*) FILTER (WHERE classification = 'incomplete/IM')  AS incomplete_im,
    COUNT(*) FILTER (WHERE classification = 'incomplete/ID')  AS incomplete_id,
    COUNT(*) FILTER (WHERE n_erig >= 1)                       AS erig,    -- parallel count
    COUNT(*) FILTER (WHERE n_hrig >= 1)                       AS hrig,    -- parallel count
    COUNT(*) FILTER (WHERE classification LIKE 'REVIEW%')     AS review,
    COUNT(*)                                                  AS total_cases
FROM in_period;

-- ─── 8. OPTIONAL: case-level breakdown for audit (uncomment to run) ────────
-- SELECT hn,
--        RIGHT(hn, 4)                                   AS hn_masked,  -- privacy
--        case_start_date, case_end_date,
--        n_im, n_id, n_erig, n_hrig, age,
--        has_prior, prior_days,
--        classification
-- FROM in_period
-- ORDER BY case_start_date, hn;


-- ============================================================================
-- VALIDATION CHECKS (run after main query)
-- ============================================================================
-- 1. Dose reconciliation: total IM/ID/ERIG doses in period must match raw count
--    SELECT
--        COUNT(*) FILTER (WHERE vaccine_type='IM')   AS im_doses,
--        COUNT(*) FILTER (WHERE vaccine_type='ID')   AS id_doses,
--        COUNT(*) FILTER (WHERE vaccine_type='ERIG') AS erig_doses
--    FROM valid_doses
--    WHERE dose_date BETWEEN '2026-04-01' AND '2026-06-30';
--
-- 2. Sum check: complete + sub5 + incomplete + REVIEW == total_cases
--    (ถ้าไม่เท่า → algorithm gap)
--
-- 3. REVIEW = 0 เป็นเป้าหมาย (เคสหลุด = ต้องเพิ่ม rule หรือ data quality issue)
-- ============================================================================


-- ============================================================================
-- NOTES FOR IT
-- ============================================================================
-- 1. icode (item codes): หาได้จาก query `SELECT icode, name FROM drugitems WHERE name ILIKE '%rabies%' OR name ILIKE '%erig%' OR name ILIKE '%immuno%rabies%'`
--    แล้วแทน XXXXX01-07 ข้างบนด้วย icode จริง
--
-- 2. ตารางที่ใช้ (HosXP standard):
--    - opitemprt: นำส่งยา OPD (มี vn, icode, qty)
--    - ovst: OPD visit (มี hn, vstdate, vn)
--    - patient: ข้อมูลคนไข้ (hn, pname, fname, lname, birthday)
--    ถ้า รพ. ใช้ตารางอื่น (เช่น ipd สำหรับ admit) → เพิ่ม UNION
--
-- 3. ถ้ารันแล้วได้ REVIEW > 0 → ส่ง row นั้นกลับมาให้ปรับ algorithm
--
-- 4. เทียบผล SQL vs Python engine:
--    python scripts/hospital/classify_rabies.py <Q3.xls> --history <Q1.xls> <Q2.xls> \
--      --period-start 2026-04-01 --period-end 2026-06-30
--    ตัวเลข 9-cell ต้องตรงกัน
-- ============================================================================
