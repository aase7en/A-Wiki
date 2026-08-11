"""Unit tests for scripts/hospital/classify_rabies.py.

Covers every rule in the Department of Disease Control (กรมควบคุมโรค) spec
for post-exposure rabies immunization, plus edge cases and the hospital-specific
extensions (over-dose, IG-only, Mixed ID+IM with age tiebreak).

Run:  python -m pytest tests/test_classify_rabies.py -v
Or:   python tests/test_classify_rabies.py
"""
from __future__ import annotations
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "hospital"))

import unittest
from classify_rabies import (
    Case, classify, age_route,
    VAC_IM, VAC_ID, VAC_ERIG, VAC_HRIG,
    PRIOR_NEAR_DAYS, PRIOR_FAR_DAYS, MIXED_AGE_CUTOFF,
)


def make_case(im=0, id=0, erig=0, hrig=0, age=30, prior=False, prior_days=None):
    """Build a Case with sensible defaults for testing."""
    c = Case(
        hn="0000001", case_idx=1,
        start_date=datetime(2026, 6, 1),
        end_date=datetime(2026, 6, 28),
        age=age,
    )
    c.doses_im = im
    c.doses_id = id
    c.doses_erig = erig
    c.doses_hrig = hrig
    c.has_prior = prior
    c.prior_days_ago = prior_days
    return c


class TestCompletePureRoute(unittest.TestCase):
    """① ฉีดครบชุด — never-vaccinated, full series."""

    def test_im_exactly_5_complete(self):
        """IM 5 เข็ม (วัน 0,3,7,14,30) = ครบชุด"""
        c = make_case(im=5)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_im_over_dose_complete(self):
        """IM 6+ เข็ม (over-dose) = ครบชุด"""
        c = make_case(im=6)
        self.assertEqual(classify(c), ("complete", "IM"))
        c2 = make_case(im=8)
        self.assertEqual(classify(c2), ("complete", "IM"))

    def test_id_exactly_4_complete(self):
        """ID 4 เข้ม (วัน 0,3,7,30) = ครบชุด"""
        c = make_case(id=4)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_id_over_dose_complete(self):
        """ID 5+ เข้ม (over-dose) = ครบชุด"""
        c = make_case(id=5)
        self.assertEqual(classify(c), ("complete", "ID"))


class TestCompleteBooster(unittest.TestCase):
    """① ฉีดครบชุด — previously vaccinated, booster doses."""

    def test_booster_im_within_6mo_1_dose(self):
        """เคยครบชุด, ภายใน 6 เดือน (≤180d), 1 เข้ม → complete"""
        c = make_case(im=1, prior=True, prior_days=90)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_booster_id_within_6mo_1_dose(self):
        c = make_case(id=1, prior=True, prior_days=150)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_booster_im_after_6mo_2_doses(self):
        """เคยครบชุด, เกิน 6 เดือน (≥181d), 2 เข้ม → complete"""
        c = make_case(im=2, prior=True, prior_days=200)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_booster_id_after_6mo_2_doses(self):
        c = make_case(id=2, prior=True, prior_days=365)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_booster_im_after_6mo_only_1_dose_incomplete(self):
        """เคยครบชุด, เกิน 6 เดือน, แค่ 1 เข้ม → incomplete (ต้อง 2)"""
        c = make_case(im=1, prior=True, prior_days=200)
        # Not >=5, not booster-1dose-near, not booster-2dose-far → falls to incomplete check
        # im=1 <3 and has_prior → first incomplete branch fails (has_prior=True)
        # second: prior>=181 AND im<2 → incomplete/IM
        self.assertEqual(classify(c), ("incomplete", "IM"))

    def test_booster_id_after_6mo_only_1_dose_incomplete(self):
        c = make_case(id=1, prior=True, prior_days=300)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_booster_boundary_exactly_180(self):
        """prior_days = 180 = within 6 months (≤180)"""
        c = make_case(id=1, prior=True, prior_days=180)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_booster_boundary_exactly_181(self):
        """prior_days = 181 = after 6 months (≥181) → needs 2 doses"""
        c = make_case(id=1, prior=True, prior_days=181)
        # id=1, prior=181 → not complete (needs 2), falls to incomplete
        self.assertEqual(classify(c), ("incomplete", "ID"))


class TestSubFive(unittest.TestCase):
    """② ฉีดต่ำกว่า ๕ เข้ม — animal observed normal 10 days → stop."""

    def test_im_3_sub5(self):
        c = make_case(im=3)
        self.assertEqual(classify(c), ("sub5", "IM"))

    def test_im_4_sub5(self):
        c = make_case(im=4)
        self.assertEqual(classify(c), ("sub5", "IM"))

    def test_id_3_sub5(self):
        c = make_case(id=3)
        self.assertEqual(classify(c), ("sub5", "ID"))


class TestIncomplete(unittest.TestCase):
    """③ ฉีดไม่ครบชุด."""

    def test_im_1_no_prior_incomplete(self):
        c = make_case(im=1)
        self.assertEqual(classify(c), ("incomplete", "IM"))

    def test_im_2_no_prior_incomplete(self):
        c = make_case(im=2)
        self.assertEqual(classify(c), ("incomplete", "IM"))

    def test_id_1_no_prior_incomplete(self):
        c = make_case(id=1)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_id_2_no_prior_incomplete(self):
        c = make_case(id=2)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_im_0_no_doses_review(self):
        """No vaccine at all, no ERIG → REVIEW (data anomaly)"""
        c = make_case()
        self.assertEqual(classify(c), ("REVIEW", "NONE"))


class TestImmunoglobulinCells(unittest.TestCase):
    """④ ERIG / HRIG (parallel count, handled in main loop)."""

    def test_erig_only_with_vaccine(self):
        """Vaccine complete + ERIG → complete cell + ERIG cell (parallel)"""
        c = make_case(id=4, erig=1)
        cat, route = classify(c)
        self.assertEqual((cat, route), ("complete", "ID"))
        self.assertGreaterEqual(c.doses_erig, 1)  # main loop counts this separately

    def test_ig_only_erig_incomplete_by_age(self):
        """ERIG but no vaccine in 28-day window → incomplete by age"""
        c = make_case(erig=1, im=0, id=0, age=30)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_ig_only_erig_child_im(self):
        c = make_case(erig=1, im=0, id=0, age=5)
        self.assertEqual(classify(c), ("incomplete", "IM"))


class TestMixed(unittest.TestCase):
    """Mixed ID+IM — total doses decide + age tiebreak."""

    def test_mixed_total_5_complete_im(self):
        c = make_case(im=3, id=2, age=30)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_mixed_total_6_complete_im(self):
        c = make_case(im=4, id=2, age=30)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_mixed_total_4_complete_id(self):
        c = make_case(im=2, id=2, age=30)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_mixed_total_3_age_ge9_id(self):
        c = make_case(im=1, id=2, age=30)
        self.assertEqual(classify(c), ("sub5", "ID"))

    def test_mixed_total_3_age_lt9_im(self):
        c = make_case(im=1, id=2, age=5)
        self.assertEqual(classify(c), ("sub5", "IM"))

    def test_mixed_total_2_age_ge9_no_prior_incomplete_id(self):
        c = make_case(im=1, id=1, age=30, prior=False)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_mixed_total_2_age_lt9_no_prior_incomplete_im(self):
        c = make_case(im=1, id=1, age=5, prior=False)
        self.assertEqual(classify(c), ("incomplete", "IM"))

    def test_mixed_total_2_prior_near_complete(self):
        """Mixed total=2 + prior ≤180d → complete (booster rule, ≥1 dose)"""
        c = make_case(im=1, id=1, age=30, prior=True, prior_days=100)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_mixed_total_2_prior_far_complete(self):
        """Mixed total=2 + prior ≥181d → complete (booster needs 2, got 2)"""
        c = make_case(im=1, id=1, age=30, prior=True, prior_days=300)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_mixed_total_1_prior_far_incomplete(self):
        """Mixed total=1 + prior ≥181d → incomplete (needs 2, got 1)"""
        c = make_case(im=1, id=0, age=30, prior=True, prior_days=300)
        # total=1, mixed=False (only IM) → pure-route path
        # im=1, prior=300 → not complete, not sub5, incomplete check: im<3 AND not no_prior
        # → prior≥181 AND im<2 → incomplete
        self.assertEqual(classify(c), ("incomplete", "IM"))


class TestAgeRoute(unittest.TestCase):
    """Age tiebreak for Mixed cases."""

    def test_age_below_cutoff_im(self):
        self.assertEqual(age_route(5), "IM")
        self.assertEqual(age_route(8), "IM")

    def test_age_at_cutoff_id(self):
        """≥9 = ID"""
        self.assertEqual(age_route(9), "ID")
        self.assertEqual(age_route(30), "ID")

    def test_age_none_returns_none(self):
        """Missing age → None (triggers REVIEW in Mixed)"""
        self.assertIsNone(age_route(None))


class TestReviewCases(unittest.TestCase):
    """Cases that legitimately fall to REVIEW (data quality gaps)."""

    def test_mixed_total_3_age_none_review(self):
        """Mixed 3 doses but age missing → REVIEW"""
        c = make_case(im=1, id=2, age=None)
        self.assertEqual(classify(c), ("REVIEW", "NONE"))

    def test_mixed_total_2_age_none_no_prior_review(self):
        c = make_case(im=1, id=1, age=None, prior=False)
        self.assertEqual(classify(c), ("REVIEW", "NONE"))

    def test_ig_only_age_none_review(self):
        c = make_case(erig=1, im=0, id=0, age=None)
        self.assertEqual(classify(c), ("REVIEW", "NONE"))


class TestRealWorldCases(unittest.TestCase):
    """Cases from real Q3 data (HN masked) — regression tests."""

    def test_q3_complete_im_pure_5(self):
        """HN****8370: IM=5, ERIG=1 → complete/IM"""
        c = make_case(im=5, erig=1, age=33)
        self.assertEqual(classify(c), ("complete", "IM"))

    def test_q3_complete_id_pure_4(self):
        """HN****9804: ID=4 → complete/ID"""
        c = make_case(id=4, age=68)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_q3_over_dose_id_5(self):
        """HN****6949: ID=5 (over-dose) → complete/ID"""
        c = make_case(id=5, erig=1, age=85)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_q3_mixed_total_4_complete_id(self):
        """HN****0217: IM=2, ID=2, ERIG=1, age=60 → complete/ID"""
        c = make_case(im=2, id=2, erig=1, age=60)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_q3_ig_only_age_34_incomplete_id(self):
        """HN****3888: ERIG=1 only, age=34 → incomplete/ID"""
        c = make_case(erig=1, im=0, id=0, age=34)
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_q3_mixed_total_2_child_incomplete_im(self):
        """HN****9258: IM=1, ID=1, age=3 → incomplete/IM"""
        c = make_case(im=1, id=1, age=3)
        self.assertEqual(classify(c), ("incomplete", "IM"))


class TestWindow33d(unittest.TestCase):
    """Bugfix #1 (v1.3.0): 33-day first-dose-anchored window.

    Verifies that cluster_cases() correctly keeps a Day-28 dose that lands
    1-3 days late within the same case (CDC "few days unimportant" grace).
    """

    def _build_df(self, dates_vacs):
        """Build a per-HN DataFrame for clustering tests."""
        import pandas as pd
        rows = []
        for d, v in dates_vacs:
            rows.append({"HN": "TEST", "date": d, "vac": v, "name": "T", "age": 30})
        return pd.DataFrame(rows)

    def test_day_28_dose_1d_late_stays_one_case(self):
        """IM Day 0,3,7,14,28+1 (Day 28 dose given 1 day late = Day 29)
        must stay as ONE case (regression for HN 10217 / 388351)."""
        from classify_rabies import cluster_cases, CASE_WINDOW_DAYS
        self.assertEqual(CASE_WINDOW_DAYS, 33, "v1.3.0 expects 33d window")
        d0 = datetime(2026, 4, 2)
        df = self._build_df([
            (d0,                          VAC_IM),
            (d0 + timedelta(days=3),      VAC_IM),
            (d0 + timedelta(days=7),      VAC_IM),
            (d0 + timedelta(days=14),     VAC_IM),
            (d0 + timedelta(days=29),     VAC_IM),  # Day 28 + 1 late
        ])
        cases = cluster_cases(df)
        self.assertEqual(len(cases), 1, "Day-29 dose must NOT split")
        self.assertEqual(cases[0].doses_im, 5)
        self.assertEqual(cases[0].total_vac, 5)

    def test_34d_gap_starts_new_case(self):
        """Dose 34d after first dose starts a new case ("หลักเดือน = รอบใหม่")."""
        from classify_rabies import cluster_cases
        d0 = datetime(2026, 4, 2)
        df = self._build_df([
            (d0,                          VAC_ID),
            (d0 + timedelta(days=34),     VAC_ID),  # >33d → new case
        ])
        cases = cluster_cases(df)
        self.assertEqual(len(cases), 2, "34d gap must split into 2 cases")

    def test_id_schedule_day_30_stays_one_case(self):
        """ID Day 0,3,7,30 (Thai Red Cross schedule) must stay as ONE case."""
        from classify_rabies import cluster_cases
        d0 = datetime(2026, 4, 2)
        df = self._build_df([
            (d0,                          VAC_ID),
            (d0 + timedelta(days=3),      VAC_ID),
            (d0 + timedelta(days=7),      VAC_ID),
            (d0 + timedelta(days=30),     VAC_ID),  # Day 30 within 33d
        ])
        cases = cluster_cases(df)
        self.assertEqual(len(cases), 1, "ID Day 30 must NOT split (within 33d)")
        self.assertEqual(cases[0].doses_id, 4)


class TestAbandonedDoseDetection(unittest.TestCase):
    """Bugfix #4 (v1.3.0): abandoned dose + clean restart split.

    Verifies refine_clusters_cross_window() correctly splits HN 176434-style
    pattern (1 dose abandoned, then clean ID/IM schedule from later anchor)
    AND does NOT wrongly merge multi-year scattered histories (HN 142753).
    """

    def _build_df(self, dates_vacs):
        import pandas as pd
        rows = []
        for d, v in dates_vacs:
            rows.append({"HN": "TEST", "date": d, "vac": v, "name": "T", "age": 30})
        return pd.DataFrame(rows)

    def test_hn_176434_pattern_splits_correctly(self):
        """1 dose on Day 0 + 4-dose clean ID schedule from Day 7 → 2 cases."""
        from classify_rabies import cluster_cases, refine_clusters_cross_window, classify
        d0 = datetime(2026, 3, 3)
        df = self._build_df([
            (d0,                          VAC_ERIG),
            (d0,                          VAC_ID),    # abandoned dose 1
            (d0 + timedelta(days=7),      VAC_ID),    # Day 0 of new series
            (d0 + timedelta(days=10),     VAC_ID),    # Day +3
            (d0 + timedelta(days=14),     VAC_ID),    # Day +7
            (d0 + timedelta(days=35),     VAC_ID),    # Day +28 — perfect ID schedule
        ])
        tw = cluster_cases(df)
        refined = refine_clusters_cross_window(tw)
        self.assertEqual(len(refined), 2, "Must split into 2 cases")
        # Case A: abandoned (03/03 only)
        case_a = refined[0]
        self.assertEqual(case_a.doses_id, 1)
        self.assertEqual(case_a.doses_erig, 1)
        self.assertEqual(classify(case_a), ("incomplete", "ID"))
        # Case B: clean restart 10/03→07/04 (4 ID doses)
        case_b = refined[1]
        self.assertEqual(case_b.doses_id, 4)
        self.assertEqual(case_b.start_date, d0 + timedelta(days=7))
        self.assertEqual(classify(case_b), ("complete", "ID"))

    def test_multi_year_scattered_NOT_merged(self):
        """HN 142753 regression: 13 doses across 5 years must NOT merge into 1."""
        from classify_rabies import cluster_cases, refine_clusters_cross_window
        # 6 doses spread across 3 years (subset of HN 142753 pattern)
        df = self._build_df([
            (datetime(2020, 1, 1),  VAC_ID),
            (datetime(2020, 1, 4),  VAC_ID),
            (datetime(2022, 6, 1),  VAC_ID),
            (datetime(2022, 6, 4),  VAC_ID),
            (datetime(2024, 3, 1),  VAC_ID),
            (datetime(2024, 3, 4),  VAC_ID),
        ])
        tw = cluster_cases(df)
        refined = refine_clusters_cross_window(tw)
        # Each year's pair should stay separate — refine MUST NOT merge them
        self.assertEqual(len(refined), len(tw),
                         "Multi-year doses must NOT be merged by refine")

    def test_normal_complete_series_not_split(self):
        """A normal 5-dose IM schedule must NOT be touched by refine."""
        from classify_rabies import cluster_cases, refine_clusters_cross_window
        d0 = datetime(2026, 4, 1)
        df = self._build_df([
            (d0,                       VAC_IM),
            (d0 + timedelta(days=3),   VAC_IM),
            (d0 + timedelta(days=7),   VAC_IM),
            (d0 + timedelta(days=14),  VAC_IM),
            (d0 + timedelta(days=28),  VAC_IM),
        ])
        tw = cluster_cases(df)
        refined = refine_clusters_cross_window(tw)
        self.assertEqual(len(refined), len(tw), "Normal series: refine = no-op")


class TestQuarterStraddle(unittest.TestCase):
    """Bugfix #5 (v1.3.0): case belongs to quarter of end_date.

    Verifies that run() correctly includes a case whose start_date is in Q(N)
    but end_date is in Q(N+1) — counted in Q(N+1) per hospital policy.
    """

    def test_straddle_case_counted_in_end_quarter(self):
        """Case start=29/03 (Q2), end=07/04 (Q3) → counted in Q3."""
        from classify_rabies import Case
        from datetime import datetime
        # Construct a case that straddles Q2/Q3 boundary
        c = Case(
            hn="TEST", case_idx=1,
            start_date=datetime(2026, 3, 10),  # Q2 (Jan-Mar)
            end_date=datetime(2026, 4, 7),     # Q3 (Apr-Jun)
        )
        ps, pe = datetime(2026, 4, 1), datetime(2026, 6, 30)
        # End_date rule: in_period iff ps <= end <= pe
        self.assertTrue(ps <= c.end_date <= pe, "Straddle case must be IN Q3 by end_date")
        # And start_date rule (old) would have excluded it
        self.assertFalse(ps <= c.start_date <= pe, "Old start_date rule would have excluded it")

    def test_pure_q3_case_still_in_q3(self):
        """Case entirely in Q3 → still in Q3 under both rules."""
        from classify_rabies import Case
        from datetime import datetime
        c = Case(
            hn="TEST", case_idx=1,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 28),
        )
        ps, pe = datetime(2026, 4, 1), datetime(2026, 6, 30)
        self.assertTrue(ps <= c.end_date <= pe)

    def test_pure_q2_case_not_in_q3(self):
        """Case entirely in Q2 → NOT in Q3 under end_date rule."""
        from classify_rabies import Case
        from datetime import datetime
        c = Case(
            hn="TEST", case_idx=1,
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 2, 28),
        )
        ps, pe = datetime(2026, 4, 1), datetime(2026, 6, 30)
        self.assertFalse(ps <= c.end_date <= pe)


class TestPriorCompleteSeries(unittest.TestCase):
    """Bugfix #2 (v1.2.0+): 'prior' = ≥3 doses (complete series), not any dose."""

    def test_single_prior_dose_does_not_count(self):
        """A patient with 1 prior dose (NOT a complete series) → has_prior=False."""
        # Direct test of annotate_prior logic: build 2 cases, first has 1 dose
        from classify_rabies import Case, annotate_prior
        from datetime import datetime
        prior_case = Case(
            hn="TEST", case_idx=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1),
        )
        prior_case.doses_id = 1  # only 1 dose — NOT complete series
        current_case = Case(
            hn="TEST", case_idx=2,
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 4, 28),
        )
        current_case.doses_id = 4
        cases_by_hn = {"TEST": [prior_case, current_case]}
        annotate_prior(cases_by_hn, {})
        self.assertFalse(current_case.has_prior,
                         "Single prior dose must NOT trigger booster rule")

    def test_three_prior_doses_count_as_complete(self):
        """A patient with 3 prior doses (complete series per DDC pre-exposure)
        → has_prior=True."""
        from classify_rabies import Case, annotate_prior
        from datetime import datetime
        prior_case = Case(
            hn="TEST", case_idx=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 21),
        )
        prior_case.doses_id = 3  # 3 doses = complete series (DDC pre-exposure)
        current_case = Case(
            hn="TEST", case_idx=2,
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 4, 28),
        )
        current_case.doses_id = 2
        cases_by_hn = {"TEST": [prior_case, current_case]}
        annotate_prior(cases_by_hn, {})
        self.assertTrue(current_case.has_prior,
                        "3 prior doses = complete series → booster rule applies")
        self.assertGreater(current_case.prior_days_ago, 181,
                           "≥2 years ago → far booster (needs 2 doses)")


class TestScreeningMerge(unittest.TestCase):
    """Bugfix #6+#7 (v1.3.1): --screening CLI + HN dtype + near/far split.

    The screening file has prior-status values that distinguish:
      - "ภายใน 6 เดือน" (within 6 months) → near, needs 1 booster dose
      - "เกิน 6 เดือน" (over 6 months)  → far, needs 2 booster doses
    """

    def test_screening_near_marks_prior_at_180d(self):
        """Screening 'near' → has_prior=True, prior_days_ago=180 (≤180 boundary)."""
        from classify_rabies import Case, annotate_prior, PRIOR_NEAR_DAYS
        from datetime import datetime
        c = Case(
            hn="12345", case_idx=1,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 3),
        )
        c.doses_id = 1  # only 1 dose — would be incomplete without prior
        cases_by_hn = {"12345": [c]}
        annotate_prior(cases_by_hn, {}, screening_prior={"12345": "near"})
        self.assertTrue(c.has_prior)
        self.assertEqual(c.prior_days_ago, PRIOR_NEAR_DAYS)
        # 1 ID dose + near prior → complete/ID (booster rule)
        from classify_rabies import classify
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_screening_far_marks_prior_at_181d(self):
        """Screening 'far' → has_prior=True, prior_days_ago=181 (≥181 boundary)."""
        from classify_rabies import Case, annotate_prior, PRIOR_FAR_DAYS, classify
        from datetime import datetime
        c = Case(
            hn="12345", case_idx=1,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 28),
        )
        c.doses_id = 2  # 2 doses — would need ≥3 if no prior
        cases_by_hn = {"12345": [c]}
        annotate_prior(cases_by_hn, {}, screening_prior={"12345": "far"})
        self.assertTrue(c.has_prior)
        self.assertEqual(c.prior_days_ago, PRIOR_FAR_DAYS)
        # 2 ID doses + far prior → complete/ID (booster rule)
        self.assertEqual(classify(c), ("complete", "ID"))

    def test_screening_far_only_1_dose_still_incomplete(self):
        """Far prior needs 2 doses — only 1 dose → incomplete (booster rule)."""
        from classify_rabies import Case, annotate_prior, classify
        from datetime import datetime
        c = Case(
            hn="12345", case_idx=1,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 1),
        )
        c.doses_id = 1
        c.age = 30
        cases_by_hn = {"12345": [c]}
        annotate_prior(cases_by_hn, {}, screening_prior={"12345": "far"})
        self.assertTrue(c.has_prior)
        # Far prior needs ≥2 doses; only 1 → incomplete
        self.assertEqual(classify(c), ("incomplete", "ID"))

    def test_screening_no_prior_value_unchanged(self):
        """HN not in screening_prior dict → has_prior=False (default)."""
        from classify_rabies import Case, annotate_prior
        from datetime import datetime
        c = Case(
            hn="99999", case_idx=1,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 1),
        )
        c.doses_id = 1
        cases_by_hn = {"99999": [c]}
        annotate_prior(cases_by_hn, {}, screening_prior={"12345": "far"})
        self.assertFalse(c.has_prior)

    def test_his_prior_overrides_screening_when_both_present(self):
        """If HIS has actual prior case with date, that wins over screening
        (more precise — knows exact days_ago)."""
        from classify_rabies import Case, annotate_prior
        from datetime import datetime
        prior_case = Case(
            hn="12345", case_idx=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 28),
        )
        prior_case.doses_id = 4  # complete series
        current_case = Case(
            hn="12345", case_idx=2,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 28),
        )
        current_case.doses_id = 2
        cases_by_hn = {"12345": [prior_case, current_case]}
        # Both HIS and screening say prior — HIS wins (precise date)
        annotate_prior(cases_by_hn, {}, screening_prior={"12345": "far"})
        self.assertTrue(current_case.has_prior)
        # Days should be from HIS actual date (2024-01-28 → 2026-05-01)
        expected_days = (datetime(2026, 5, 1) - datetime(2024, 1, 28)).days
        self.assertEqual(current_case.prior_days_ago, expected_days)


if __name__ == "__main__":
    unittest.main(verbosity=2)
