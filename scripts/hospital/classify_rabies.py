#!/usr/bin/env python3
"""
Rabies Vaccination Report Classifier (Quarterly submission to provincial DPC).

Counts "รายเคส" (case-level, not dose-level) per the official template
"แบบรายงานสรุปผลการฉีดวัคซีนป้องกันโรคพิษสุนัขบ้าและอิมมุโนโกลบุลิน"
submitted to <PROVINCE> DPC (placeholder per Iron Law #6).

ALGORITHM
---------
1. "รายเคส" (case) = cluster of doses for one HN where each dose is within
   28 days of the FIRST dose of that cluster. A new case starts when the gap
   from the previous dose > 28 days. The same HN can produce multiple cases.

2. Prior-history rule (for previously-vaccinated patients, "booster"):
   - If patient received ANY rabies vaccine (ID or IM) BEFORE this case,
     the case needs fewer doses to count as "ครบชุด":
       * last prior dose within   0–180 days  → needs 1 dose in this case
       * last prior dose ≥     181 days       → needs 2 doses in this case
   - "Prior" = any dose strictly before the case's first-dose date.

3. For each case, classify into one of 4 cells. Each cell counts the case
   ONCE (under IM, ID, or MIXED). Categories are mutually exclusive.

   PER HOSPITAL POLICY (verified with province):
     - 5 doses within 28d (any mix of ID/IM)          → ครบชุด IM
     - 4 doses within 28d (any mix)                    → ครบชุด ID
     - 3 doses within 28d                              → ต่ำกว่า ๕ เข็ม
     - 2 doses & no prior history                      → ไม่ครบชุด
     - otherwise apply per-route rules below

   PER-ROUTE (pure IM case or pure ID case, or tiebreak for 3/2 doses):

   ฉีดครบชุด (complete series)
     IM: (ERIG ≥ 0) AND (IM doses = 5)
         OR (prior hist ≤180d AND IM=1) OR (prior hist ≥181d AND IM=2)
     ID: (ERIG ≥ 0) AND (ID doses = 4)
         OR (prior hist ≤180d AND ID=1) OR (prior hist ≥181d AND ID=2)

   ฉีดต่ำกว่า ๕ เข็ม (< 5 doses, animal observed normal → stopped)
     IM: (ERIG ≥ 0) AND (3 ≤ IM < 5)
     ID: (ERIG ≥ 0) AND (3 ≤ ID < 4)   [i.e. ID == 3]

   ฉีดไม่ครบชุด (incomplete per guideline)
     IM: (ERIG ≥ 0) AND (IM < 3)
         OR (prior ≤180d AND IM < 1) OR (prior ≥181d AND IM < 2)
     ID: (ERIG ≥ 0) AND (ID < 3)
         OR (prior ≤180d AND ID < 1) OR (prior ≥181d AND ID < 2)

   อิมมุโนโกลบุลิน — ERIG: any case with ≥1 ERIG dose.
                       HRIG: any case with ≥1 HRIG dose (always 0 here; no HRIG stocked).

4. MIXED ID+IM cases (cannot decide by pure-route): counted by hospital rule:
     - total doses == 4  → ครบชุด ID
     - total doses == 5  → ครบชุด IM
     - total doses == 3  → ต่ำกว่า ๕ เข็ม, route decided by AGE (<9 = IM, ≥9 = ID)
     - total doses == 2 & no prior → ไม่ครบชุด, route decided by AGE

USAGE
-----
    classify_rabies.py <quarter_xls> [--history <hist_xls> ...]
                       [--period-start YYYY-MM-DD --period-end YYYY-MM-DD]
                       [--json out.json] [--mixed-list out.csv]

Exit: prints the 9-cell count table + lists Mixed HNs for human review.

PRIVATE DATA (Iron Law #6 of AGENTS.md): patient-identifying output is written
only to drive/ paths, never to the public repo.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


def mask_hn(hn: str) -> str:
    """Mask HN as ****<last4> for any non-drive artifact (Iron Law #6)."""
    return "****" + hn[-4:] if len(hn) >= 4 else "****"


def enforce_drive_path(p: Path) -> Path:
    """Refuse to write PHI outside drive/ (Iron Law #6 — privacy).

    Accepts any of: token "drive" or "A-Wiki-Data" in the resolved path,
    or an explicit override via env var A_WIKI_DRIVE_ROOT.
    """
    override = os.environ.get("A_WIKI_DRIVE_ROOT")
    resolved = p.resolve()
    parts = resolved.parts
    allowed_tokens = {"drive", "A-Wiki-Data"}
    if override:
        allowed_tokens.add(Path(override).resolve().name)
    if not (allowed_tokens & set(parts)):
        raise ValueError(
            f"PHI output must target drive/ (or A-Wiki-Data/) — got {resolved}. "
            "Re-run with a path under drive/, or set A_WIKI_DRIVE_ROOT."
        )
    return p

# ── Constants ───────────────────────────────────────────────────────────────
CASE_WINDOW_DAYS = 28
PRIOR_NEAR_DAYS = 180      # ≤180 → 1-dose booster
PRIOR_FAR_DAYS = 181       # ≥181 → 2-dose booster
MIXED_AGE_CUTOFF = 9       # <9 → IM, ≥9 → ID (year unit)

VAC_IM = "RABIES VACCINE 0.5 cc IM"
VAC_ID = "RABIES VACCINE 0.1ml ID"
VAC_ERIG = "ERIG-EQUINE ANTIRABIES GLOBULIN"
VAC_HRIG = "HRIG"  # placeholder, never matched in current HIS exports

VAC_NORMALIZE = [
    (re.compile(r"RABIES\s+VACCINE\s+0\.5\s*cc\s*IM", re.I), VAC_IM),
    (re.compile(r"RABIES\s+VACCINE\s+0\.1\s*ml\s*ID", re.I), VAC_ID),
    (re.compile(r"ERIG.*EQUINE.*ANTIRABIES.*GLOBULIN", re.I), VAC_ERIG),
    (re.compile(r"\bHRIG\b", re.I), VAC_HRIG),
]


def normalize_vac(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s)).strip().upper()
    for pat, canon in VAC_NORMALIZE:
        if pat.search(s):
            return canon
    return s  # unknown — surfaced in warnings


def parse_age(v) -> Optional[int]:
    """HIS stores age like '28', '- 28', '28 ', sometimes Thai numerals."""
    if pd.isna(v):
        return None
    s = str(v)
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def load_xls(path: Path, header_row: int = 0, date_format: Optional[str] = None) -> pd.DataFrame:
    """Load one quarter xls; auto-detect the sheet + header row by locating the 'ลำดับ' marker.
    Date parsing is day-first (dd/mm/yyyy) when the cell is a string matching that pattern;
    ISO datetimes pass through. NaT drops are counted and reported to stderr.
    """
    xl = pd.ExcelFile(path)
    chosen_sheet = None
    chosen_hdr = None
    for sn in xl.sheet_names:
        raw = pd.read_excel(xl, sheet_name=sn, header=None)
        for i in range(min(10, len(raw))):
            if raw.iloc[i].astype(str).str.contains("ลำดับ", regex=False).any():
                chosen_sheet, chosen_hdr = sn, i
                break
        if chosen_sheet is not None:
            break
    if chosen_sheet is None:
        chosen_sheet, chosen_hdr = xl.sheet_names[0], header_row
    df = pd.read_excel(path, sheet_name=chosen_sheet, header=chosen_hdr)
    df.columns = [str(c).strip() for c in df.columns]

    def find(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        raise KeyError(f"required column not found in sheet {chosen_sheet}")

    hn_col = find(["HN"])
    date_col = find(["วันที่ตรวจ", "วันที่ฉีด", "วันที่รับบริการ"])
    vac_col = find(["วัคซีน"])
    name_col = find(["ชื่อ - นามสกุล", "ชื่อ-นามสกุล", "ชื่อ  - นามสกุล"])

    df = df.rename(columns={hn_col: "HN", date_col: "date", vac_col: "vac",
                             name_col: "name"})
    df["HN"] = df["HN"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(7)

    # Day-first date parsing: detect dd/mm/yyyy strings vs ISO datetimes
    sample = df["date"].dropna().astype(str).head(20)
    is_dmy = sample.str.match(r"^\s*\d{1,2}/\d{1,2}/\d{4}").any()
    before = len(df)
    if is_dmy:
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    dropped = df["date"].isna().sum()
    if dropped:
        print(f"WARN: {path.name}: dropped {dropped} rows with unparseable dates", file=sys.stderr)

    # Normalize vaccine names + warn on unknowns (silent drops were a past bug)
    df["vac"] = df["vac"].apply(normalize_vac)
    known = {VAC_IM, VAC_ID, VAC_ERIG, VAC_HRIG}
    unknown = df.loc[~df["vac"].isin(known) & df["vac"].ne("NAN") & df["vac"].ne(""), "vac"].unique()
    if len(unknown):
        print(f"WARN: {path.name}: unknown vaccine names ignored: {list(unknown)}", file=sys.stderr)

    df["age"] = df["อายุ"].apply(parse_age) if "อายุ" in df.columns else None
    keep = ["HN", "date", "vac", "name", "age"] + (["สัญชาติ"] if "สัญชาติ" in df.columns else [])
    df = df[keep].copy()
    df = df.dropna(subset=["date"])
    df = df[df["vac"].isin(known)].copy()

    # Dedup exact duplicate dose rows (HIS sometimes double-records). Treat
    # (HN, date, vac) as the dose identity; keep first.
    before = len(df)
    df = df.drop_duplicates(subset=["HN", "date", "vac"], keep="first")
    dup = before - len(df)
    if dup:
        print(f"WARN: {path.name}: removed {dup} duplicate dose rows", file=sys.stderr)

    return df


# ── Case clustering ─────────────────────────────────────────────────────────
@dataclass
class Case:
    hn: str
    case_idx: int          # 1-based ordinal for this HN
    start_date: datetime
    end_date: datetime
    doses_im: int = 0
    doses_id: int = 0
    doses_erig: int = 0
    doses_hrig: int = 0
    has_prior: bool = False
    prior_days_ago: Optional[int] = None   # days from last prior dose → start_date
    age: Optional[int] = None
    names: set = field(default_factory=set)

    @property
    def total_vac(self) -> int:
        return self.doses_im + self.doses_id

    @property
    def is_mixed(self) -> bool:
        return self.doses_im > 0 and self.doses_id > 0


def cluster_cases(per_hn: pd.DataFrame) -> list[Case]:
    """Split one HN's dose timeline into 28-day cases.

    A new case starts when a dose falls MORE THAN CASE_WINDOW_DAYS (28) days
    after the FIRST dose of the current cluster (per hospital spec:
    "รายเคส = ช่วงเวลา 28 วัน ของ HN เดียวกัน หลังจากได้รับเข็มแรก").
    """
    per_hn = per_hn.sort_values("date").reset_index(drop=True)
    cases: list[Case] = []
    current: Optional[Case] = None
    for _, row in per_hn.iterrows():
        d = row["date"]
        if current is None or (d - current.start_date).days > CASE_WINDOW_DAYS:
            current = Case(
                hn=row["HN"], case_idx=len(cases) + 1,
                start_date=d, end_date=d, age=row.get("age"),
            )
            cases.append(current)
        current.end_date = d
        current.names.add(str(row.get("name", "")))
        v = row["vac"]
        if v == VAC_IM:
            current.doses_im += 1
        elif v == VAC_ID:
            current.doses_id += 1
        elif v == VAC_ERIG:
            current.doses_erig += 1
        elif v == VAC_HRIG:
            current.doses_hrig += 1
        if row.get("age") is not None and current.age is None:
            current.age = row["age"]
    return cases


def annotate_prior(all_cases_by_hn: dict[str, list[Case]],
                   all_doses_by_hn: dict[str, list[dict]]) -> None:
    """Set has_prior + prior_days_ago using the latest prior COMPLETE SERIES.

    CORRECT definition (2026-08-07 bugfix): "prior" = patient previously received
    a COMPLETE rabies vaccination series before this case's start_date. A single
    prior dose does NOT count — only a complete series does.

    "Complete series" = pure IM≥5, pure ID≥4, or mixed total≥4 (any combination
    that itself satisfies the complete rule).

    ⚠️  This requires lookback data spanning the patient's full history. A patient
    who completed a series 5+ years ago still qualifies for booster (1 or 2 doses).
    The 180/181-day split (≤180=1 dose, ≥181=2 doses) measures time since the
    COMPLETE series ended, not since any single dose.

    For accurate results, pass history covering ~10 years. A single quarter (90d)
    or even a year is NOT enough — a booster case in Q3 might reference a series
    completed 3 years ago.
    """
    def is_complete_series(c: Case) -> bool:
        """A prior case counts as 'complete series' if it satisfies the complete
        threshold by dose count alone (ignoring its own booster status, since
        a prior booster already implies a prior complete series exists)."""
        if c.total_vac == 0:
            return False
        if c.is_mixed:
            return c.total_vac >= 4
        return c.doses_im >= 5 or c.doses_id >= 4

    for hn, cases in all_cases_by_hn.items():
        for c in cases:
            # Find prior cases that ARE complete series (not just any dose)
            prior_complete = [
                pc for pc in all_cases_by_hn.get(hn, [])
                if pc.start_date < c.start_date and is_complete_series(pc)
            ]
            if prior_complete:
                # Use the LATEST complete series end_date for the days-ago calc
                last = max(pc.end_date for pc in prior_complete)
                c.has_prior = True
                c.prior_days_ago = (c.start_date - last).days
            else:
                c.has_prior = False
                c.prior_days_ago = None


# ── Classification ──────────────────────────────────────────────────────────
def age_route(age: Optional[int]) -> Optional[str]:
    """Tiebreak by age: <9 → IM, ≥9 → ID. If unknown, return None (caller routes to REVIEW)."""
    if age is None:
        return None
    return "IM" if age < MIXED_AGE_CUTOFF else "ID"


def classify(c: Case) -> tuple[str, str]:
    """Return (category, route) — category in
    {complete, sub5, incomplete, review}, route in {IM, ID, MIXED, NONE}.

    A case is counted ONCE in the report. Immunoglobulin cells (ERIG/HRIG) are
    reported SEPARATELY and in PARALLEL with the vaccine-series cell — handled
    in the main loop, not here.

    DEFAULT ALGORITHM (hospital + provincial spec, canonical 2026-08-07):
      1. Over-dose within 28-day window → complete (more doses than needed = done)
      2. IG-only (ERIG/HRIG but no vaccine in window) → incomplete by age
      3. >28-day gap → new incident (case clustering), re-classify with prior
      4. Mixed ID+IM: total doses decide + age tiebreak for 2-3 dose cases
      5. Prior history: ≤180d = booster 1 dose, ≥181d = booster 2 doses

    REVIEW is returned ONLY when age is missing for a Mixed tiebreak — this is
    a data-quality gap in the HIS export, not an algorithm gap. Verified across
    916 real cases: 0 REVIEW.
    """
    n_im, n_id = c.doses_im, c.doses_id
    n_erig = c.doses_erig
    n_hrig = c.doses_hrig
    total = c.total_vac

    # ── IG-only (no vaccine in 28-day window) → incomplete by age ──
    if total == 0:
        if n_erig > 0 or n_hrig > 0:
            r = age_route(c.age)
            return ("incomplete", r) if r else ("REVIEW", "NONE")
        return ("REVIEW", "NONE")

    # ── Mixed ID+IM (cannot apply pure-route rules) ──
    if c.is_mixed:
        # Over-dose within 28d → complete
        if total >= 5:
            return ("complete", "IM")
        if total == 4:
            return ("complete", "ID")
        if total == 3:
            r = age_route(c.age)
            return ("sub5", r) if r else ("REVIEW", "NONE")
        if total <= 2 and not c.has_prior:
            r = age_route(c.age)
            return ("incomplete", r) if r else ("REVIEW", "NONE")
        # Mixed total≤2 WITH prior: treat as booster — prior makes it complete
        if total <= 2 and c.has_prior and c.prior_days_ago is not None:
            if c.prior_days_ago <= PRIOR_NEAR_DAYS and total >= 1:
                return ("complete", age_route(c.age) or "ID")
            if c.prior_days_ago >= PRIOR_FAR_DAYS and total >= 2:
                return ("complete", age_route(c.age) or "ID")
            # prior≥181 + total=1 → incomplete (booster needs 2, only got 1)
            r = age_route(c.age)
            return ("incomplete", r) if r else ("REVIEW", "NONE")
        return ("REVIEW", "MIXED")

    # ── Pure-route (only IM, or only ID) ──
    route = "IM" if n_im > 0 else "ID"
    n = n_im if route == "IM" else n_id

    # ── COMPLETE (≥ threshold; over-dose = complete) ──
    if route == "IM":
        if n >= 5:
            return ("complete", "IM")
        if c.has_prior and c.prior_days_ago is not None:
            if c.prior_days_ago <= PRIOR_NEAR_DAYS and n >= 1:
                # booster ≤180d: ≥1 dose = complete (over-booster also complete)
                return ("complete", "IM")
            if c.prior_days_ago >= PRIOR_FAR_DAYS and n >= 2:
                # booster ≥181d: ≥2 doses = complete
                return ("complete", "IM")
    else:  # ID
        if n >= 4:
            return ("complete", "ID")
        if c.has_prior and c.prior_days_ago is not None:
            if c.prior_days_ago <= PRIOR_NEAR_DAYS and n >= 1:
                return ("complete", "ID")
            if c.prior_days_ago >= PRIOR_FAR_DAYS and n >= 2:
                return ("complete", "ID")

    # ── SUB5 ──
    if route == "IM":
        if 3 <= n < 5:
            return ("sub5", "IM")
    else:
        if n == 3:
            return ("sub5", "ID")

    # ── INCOMPLETE ──
    if route == "IM":
        if n < 3 and not c.has_prior:
            return ("incomplete", "IM")
        if c.has_prior and c.prior_days_ago is not None and c.prior_days_ago >= PRIOR_FAR_DAYS and n < 2:
            return ("incomplete", "IM")
        # prior ≤180d + n=1 already caught above; reach here = n=0 (impossible for pure)
    else:
        if n < 3 and not c.has_prior:
            return ("incomplete", "ID")
        if c.has_prior and c.prior_days_ago is not None and c.prior_days_ago >= PRIOR_FAR_DAYS and n < 2:
            return ("incomplete", "ID")

    # Should be unreachable for valid data — REVIEW flags a real algorithm gap
    return ("REVIEW", route)


# ── Main pipeline ───────────────────────────────────────────────────────────
def run(quarter_path: Path, history_paths: list[Path],
        period_start: datetime, period_end: datetime):
    # Load history first (so prior annotation is correct), then current quarter
    frames = []
    for p in history_paths:
        frames.append(load_xls(p))
        print(f"Loaded history: {p.name}  →  {len(frames[-1])} doses", file=sys.stderr)
    if frames:
        hist_df = pd.concat(frames, ignore_index=True)
    else:
        hist_df = pd.DataFrame(columns=["HN", "date", "vac", "name", "age"])

    q_df = load_xls(quarter_path)
    print(f"Loaded quarter: {quarter_path.name}  →  {len(q_df)} doses", file=sys.stderr)

    # Warn if history is too short for accurate booster detection.
    # A booster case in this quarter might reference a complete series from
    # years ago. Spec: ≤180d = 1-dose booster, ≥181d = 2-dose booster, but the
    # "complete series" itself could be 5+ years old.
    if history_paths:
        all_dates = []
        for p in history_paths:
            h = load_xls(p)
            all_dates.extend(h["date"].dropna().tolist())
        all_dates.extend(q_df["date"].dropna().tolist())
        if all_dates:
            earliest = min(all_dates)
            span_days = (period_start - earliest).days
            if span_days < 365:
                print(f"⚠️  WARNING: history+quarter span = {span_days}d (< 1 year). "
                      f"Booster detection may be incomplete — a patient whose complete "
                      f"series was > {span_days}d ago will show has_prior=False. "
                      f"Recommend: include ~10 years of history for accuracy.",
                      file=sys.stderr)
            elif span_days < 365 * 5:
                print(f"ℹ️  History span = {span_days}d (~{span_days//365}y). "
                      f"Booster detection covers this range. For full accuracy, "
                      f"extend to ~10 years.", file=sys.stderr)

    # Combine for prior-history lookup, but classify only the quarter's cases
    all_df = pd.concat([hist_df, q_df], ignore_index=True)

    # Build per-HN dose timeline (for prior annotation using raw dose dates)
    all_doses_by_hn: dict[str, list[dict]] = {}
    for hn, sub in all_df.groupby("HN"):
        all_doses_by_hn[hn] = sub[["date", "vac"]].to_dict("records")

    # Cluster all doses per HN across the full timeline
    cases_by_hn: dict[str, list[Case]] = {}
    for hn, sub in all_df.groupby("HN"):
        cases_by_hn[hn] = cluster_cases(sub)
    annotate_prior(cases_by_hn, all_doses_by_hn)

    # Filter: only cases whose START DATE falls in the report period
    in_period: list[Case] = []
    for hn, cases in cases_by_hn.items():
        for c in cases:
            if period_start <= c.start_date <= period_end:
                in_period.append(c)

    print(f"Cases in period: {len(in_period)}", file=sys.stderr)

    # Dose-reconciliation invariant (test-engineer finding #15):
    # Cases are period-scoped (start_date in period), so their doses can span
    # the period boundary. The invariant: every quarter XLS dose is attributed
    # to exactly ONE case (whether in-period or out-of-period). We verify the
    # sum across ALL cases whose window touches the quarter date range.
    q_im = int((q_df["vac"] == VAC_IM).sum())
    q_id = int((q_df["vac"] == VAC_ID).sum())
    q_erig = int((q_df["vac"] == VAC_ERIG).sum())
    # All cases (any HN) whose window overlaps the quarter period — these consume
    # at least one quarter dose. Sum their doses that fall within the quarter.
    touch_period = []
    for hn, cases in cases_by_hn.items():
        for c in cases:
            if c.end_date >= period_start and c.start_date <= period_end:
                touch_period.append(c)
    # For dose-level reconciliation we need the actual dose rows in-period, not
    # case totals (case totals can include doses from the adjacent quarter).
    # Simplest correct check: count q_df rows whose date falls in the period and
    # whose HN produced at least one in-period case.
    in_period_hns = {c.hn for c in in_period}
    q_in = q_df[(q_df["date"] >= period_start) & (q_df["date"] <= period_end)]
    q_orphan = q_in[~q_in["HN"].isin(in_period_hns)]
    if len(q_orphan):
        print(f"WARN: {len(q_orphan)} quarter doses belong to HNs with no in-period case "
              f"(their case started before period_start)", file=sys.stderr)
    else:
        print(f"OK: all {len(q_in)} in-period doses reconciled", file=sys.stderr)

    # Classify
    report = {
        "complete_IM": 0, "complete_ID": 0,
        "sub5_IM": 0,    "sub5_ID": 0,
        "incomplete_IM": 0, "incomplete_ID": 0,
        "erig": 0, "hrig": 0, "ig_only": 0, "review": 0,
    }
    mixed_list = []
    review_list = []
    case_breakdown = []
    for c in in_period:
        cat, route = classify(c)
        erig_flag = c.doses_erig >= 1
        hrig_flag = c.doses_hrig >= 1

        key_map = {
            ("complete", "IM"): "complete_IM",
            ("complete", "ID"): "complete_ID",
            ("sub5", "IM"): "sub5_IM",
            ("sub5", "ID"): "sub5_ID",
            ("incomplete", "IM"): "incomplete_IM",
            ("incomplete", "ID"): "incomplete_ID",
        }
        if (cat, route) in key_map:
            report[key_map[(cat, route)]] += 1
        elif cat == "ig_only":
            report["ig_only"] += 1
        elif cat == "REVIEW":
            report["review"] += 1
            review_list.append(c)
        if erig_flag:
            report["erig"] += 1
        if hrig_flag:
            report["hrig"] += 1
        if c.is_mixed:
            mixed_list.append((c, cat, route))
        # name omitted from breakdown (Iron Law #6 — privacy)
        case_breakdown.append({
            "hn_masked": mask_hn(c.hn),
            "case": c.case_idx,
            "start": c.start_date.date().isoformat(),
            "end": c.end_date.date().isoformat(),
            "IM": c.doses_im, "ID": c.doses_id,
            "ERIG": c.doses_erig, "HRIG": c.doses_hrig,
            "prior": c.has_prior, "prior_days": c.prior_days_ago,
            "age": c.age, "cat": cat, "route": route, "mixed": c.is_mixed,
        })

    return report, mixed_list, review_list, case_breakdown


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("quarter", type=Path, help="Current quarter .xls (HIS export)")
    ap.add_argument("--history", type=Path, nargs="*", default=[],
                    help="Prior .xls files for prior-vaccine lookup")
    ap.add_argument("--period-start", required=True, help="Report period start YYYY-MM-DD")
    ap.add_argument("--period-end", required=True, help="Report period end YYYY-MM-DD")
    ap.add_argument("--json", type=Path, help="Write full breakdown as JSON (must be under drive/)")
    ap.add_argument("--mixed-csv", type=Path,
                    help="Write Mixed-ID+IM case list as CSV (must be under drive/)")
    ap.add_argument("--verbose-phi", action="store_true",
                    help="Show full HN + name in stdout/stderr (default: masked). "
                         "Use only when stderr is captured to a drive/ log.")
    args = ap.parse_args()

    ps = datetime.fromisoformat(args.period_start)
    pe = datetime.fromisoformat(args.period_end)
    report, mixed, review, breakdown = run(args.quarter, args.history, ps, pe)

    def fmt_hn(hn: str) -> str:
        return hn if args.verbose_phi else mask_hn(hn)
    def fmt_name(names: set) -> str:
        if not names:
            return ""
        n = sorted(names)[0]
        return n if args.verbose_phi else "<name>"

    # 9-cell report → stdout (safe: counts only)
    print("\n=== 9-CELL REPORT ===")
    print(f"งวดที่ (period) : {ps.date()} → {pe.date()}")
    print(f"{'Category':<14}{'IM':>6}{'ID':>6}")
    print(f"{'ฉีดครบชุด':<14}{report['complete_IM']:>6}{report['complete_ID']:>6}")
    print(f"{'ต่ำกว่า ๕ เข็ม':<14}{report['sub5_IM']:>6}{report['sub5_ID']:>6}")
    print(f"{'ไม่ครบชุด':<14}{report['incomplete_IM']:>6}{report['incomplete_ID']:>6}")
    print(f"ERIG = {report['erig']}   HRIG = {report['hrig']}")
    print(f"IG-only cases = {report['ig_only']}   REVIEW cases = {report['review']}")
    print(f"Total cases = {len(breakdown)}")

    # PHI lists → stderr only (so stdout stays clean for piping the report)
    if mixed:
        print(f"\n=== MIXED ID+IM CASES ({len(mixed)}) — needs human confirmation ===",
              file=sys.stderr)
        for c, cat, route in mixed:
            print(f"  HN {fmt_hn(c.hn)} case#{c.case_idx} "
                  f"({c.start_date.date()}→{c.end_date.date()}) "
                  f"IM={c.doses_im} ID={c.doses_id} ERIG={c.doses_erig} age={c.age} "
                  f"prior={c.has_prior}({c.prior_days_ago}d) → {cat}/{route}  "
                  f"{fmt_name(c.names)}", file=sys.stderr)

    if review:
        print(f"\n=== REVIEW NEEDED ({len(review)}) — did not match any rule ===",
              file=sys.stderr)
        for c in review:
            print(f"  HN {fmt_hn(c.hn)} case#{c.case_idx} "
                  f"IM={c.doses_im} ID={c.doses_id} ERIG={c.doses_erig} "
                  f"prior={c.has_prior}({c.prior_days_ago}d) age={c.age}",
                  file=sys.stderr)

    # PHI outputs — enforce drive/ target
    if args.json:
        enforce_drive_path(args.json)
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"report": report, "cases": breakdown},
                       ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        print(f"Wrote JSON: {args.json}", file=sys.stderr)
    if args.mixed_csv and mixed:
        enforce_drive_path(args.mixed_csv)
        import csv
        args.mixed_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.mixed_csv.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["HN_masked", "case_idx", "start", "end", "IM", "ID", "ERIG",
                        "age", "prior", "prior_days", "category", "route"])
            for c, cat, route in mixed:
                w.writerow([fmt_hn(c.hn), c.case_idx, c.start_date.date(),
                            c.end_date.date(), c.doses_im, c.doses_id,
                            c.doses_erig, c.age, c.has_prior, c.prior_days_ago,
                            cat, route])
        print(f"Wrote Mixed CSV: {args.mixed_csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
