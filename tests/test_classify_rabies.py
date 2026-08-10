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


if __name__ == "__main__":
    unittest.main(verbosity=2)
