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
# Case window MUST cover BOTH post-exposure schedules end-to-end:
#   - IM (Essen): Day 0,3,7,14,28  → last dose on Day 28
#   - ID (IPC/Thai Red Cross): Day 0,3,7,28 (or 30) → last dose on Day 28-30
# 28 days is the schedule itself — the last dose can legitimately fall ON Day 28
# (or 1-3 days late per CDC guidance). A 28-day window would split every IM/ID
# series where the final dose landed on Day 29-30. 33d = 30d schedule + 3d CDC
# grace ("delays of a few days are unimportant"). 2026-08-11 fix (HN 10217/388351).
CASE_WINDOW_DAYS = 33
PRIOR_NEAR_DAYS = 180      # ≤180 → 1-dose booster
PRIOR_FAR_DAYS = 181       # ≥181 → 2-dose booster
MIXED_AGE_CUTOFF = 9       # <9 → IM, ≥9 → ID (year unit)

# Schedule templates for "abandoned dose + restart" detection (bugfix #4, 2026-08-11).
# A "clean PEP schedule" from a Day-0 anchor means each subsequent dose falls
# within ±SCHEDULE_TOL_DAYS of one of the expected schedule days.
SCHEDULE_TOL_DAYS = 2
IM_SCHEDULE_DAYS = (0, 3, 7, 14, 28)   # Essen (5 doses)
ID_SCHEDULE_DAYS = (0, 3, 7, 28)        # Thai Red Cross / IPC (4 doses)

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
    Falls back to synthetic headers for legacy exports that have no header row
    (e.g. 2016 HIS export starts data at row 0). Date parsing is day-first
    (dd/mm/yyyy) when the cell is a string matching that pattern; ISO datetimes
    pass through. NaT drops are counted and reported to stderr.
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
        # Legacy export without header row — assign canonical column names.
        # Column order observed across 2016-2025 HIS exports:
        # 0:ลำดับ 1:HN 2:วันที่ตรวจ 3:ชื่อ-นามสกุล 4:อายุ 5:เบอร์โทรศัพท์ 6:สัญชาติ 7:วัคซีน
        chosen_sheet = xl.sheet_names[0]
        chosen_hdr = None  # read with header=None, assign names manually
        raw = pd.read_excel(xl, sheet_name=chosen_sheet, header=None)
        canon_cols = ["ลำดับ", "HN", "วันที่ตรวจ", "ชื่อ - นามสกุล",
                      "อายุ", "เบอร์โทรศัพท์", "สัญชาติ", "วัคซีน"]
        n = min(len(canon_cols), raw.shape[1])
        df = raw.copy()
        df.columns = canon_cols[:n] + [f"col_{i}" for i in range(n, raw.shape[1])]
        print(f"WARN: {path.name}: no 'ลำดับ' header found — using synthetic column names "
              f"({n} cols)", file=sys.stderr)
    else:
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
    df["HN"] = df["HN"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    # Preserve HN as-is (don't force zfill — HIS legacy exports use 5-6 digits,
    # modern use 7). Just strip non-digits and warn if mixed lengths across files.
    df["HN"] = df["HN"].str.replace(r"[^\d]", "", regex=True)

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


def load_screening(path: Path) -> dict[str, str]:
    """Load the screening-app .xls and return {str(HN): "near"|"far"} prior map.

    Bugfix #6+#7 (2026-08-11): the screening file has NO header row — pandas
    was eating row 1 as headers. Reload with header=None.

    Expected schema (8 cols, no header):
      col 0 = row number (1-based)
      col 1 = HN (float — patient ID)
      col 2 = date
      col 3 = full name
      col 4 = age
      col 5 = phone
      col 6 = nationality
      col 7 = prior-status text — one of:
               "เคยฉีด 3 เข็ม หรือมากกว่า (ภายใน 6 เดือน)"   → near (≤180d)
               "เคยฉีด 3 เข็ม หรือมากกว่า (เกิน 6 เดือน)"     → far  (≥181d)
               "ไม่เคยฉีดหรือเคยฉีดน้อยกว่า 3 เข็ม"             → (skip)

    Returns:
      dict[str(str(int(HN)))] = "near" | "far"
      Only HNs with prior ≥3 doses are included.

    HN dtype normalization: HIS HN is str ("175925"); screening HN is float
    (175925.0). Caller must use str(int(...)) for matching.
    """
    df = pd.read_excel(path, header=None)
    if df.shape[1] < 8:
        print(f"WARN: {path.name}: expected ≥8 cols, got {df.shape[1]}",
              file=sys.stderr)
        return {}
    prior_map: dict[str, str] = {}
    for _, r in df.iterrows():
        try:
            hn_int = int(r[1])
        except (ValueError, TypeError):
            continue
        status = str(r[7])
        if "เคยฉีด 3 เข็ม" in status:
            if "ภายใน" in status:
                prior_map[str(hn_int)] = "near"
            elif "เกิน" in status:
                prior_map[str(hn_int)] = "far"
            # else: ambiguous "เคยฉีด 3 เข็ม" without near/far — assume far (conservative)
            else:
                prior_map[str(hn_int)] = "far"
    print(f"Loaded screening: {path.name}  →  {len(prior_map)} prior-complete HNs "
          f"(near={sum(1 for v in prior_map.values() if v == 'near')}, "
          f"far={sum(1 for v in prior_map.values() if v == 'far')})",
          file=sys.stderr)
    return prior_map


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
    # Per-dose log: list of (date, vac_code) — kept for schedule-fit analysis.
    # Bugfix #4 (2026-08-11): needed by split_abandoned_dose() to detect
    # "patient received 1 dose, disappeared, came back to start a clean new
    # series" pattern (HN 176434).
    dose_log: list = field(default_factory=list)

    @property
    def total_vac(self) -> int:
        return self.doses_im + self.doses_id

    @property
    def is_mixed(self) -> bool:
        return self.doses_im > 0 and self.doses_id > 0


def cluster_cases(per_hn: pd.DataFrame) -> list[Case]:
    """Split one HN's dose timeline into cases anchored on the first dose.

    Rule (hospital + DDC spec + CDC guidance, 2026-08-11):
      - A case starts at the first dose (Day 0).
      - Subsequent doses belong to the same case while they fall within
        CASE_WINDOW_DAYS (33) of the FIRST dose. This window covers the
        full length of BOTH post-exposure schedules (IM Day 0→28, ID Day
        0→30) plus a 3-day CDC-permitted grace period for "delays of a
        few days [that] are unimportant". A dose falling 34+ days after
        the first dose — i.e. roughly a month later, "หลักเดือน" per
        hospital policy — starts a new episode.
      - The window is anchored on the FIRST dose (not sliding). This means
        a patient who returns 2+ months later is correctly treated as a new
        incident even if each individual gap happens to be small. Pure
        sliding windows merged unrelated episodes; the fixed anchor does
        not.

    2026-08-11 history: this had three failed approaches in sequence:
      1. Strict 28d window → split the natural Day-28 IM dose when given
         1 day late (HN 10217, HN 388351). The schedule's own length WAS
         the cutoff.
      2. Sliding window (gap between consecutive doses ≤ 28d) → merged
         unrelated episodes months apart whenever each gap was small.
      3. Calendar-month-aware window → split HN 10217 and 388351 again
         because their Day-28 dose (given 1 day late) landed on the 1st
         of the next calendar month.
    The 33-day first-dose-anchored window below is the fourth and correct
    attempt: it is derived from the actual schedule lengths (28 for IM,
    30 for ID) plus CDC grace, not from arbitrary date arithmetic.

    Reference: CDC MMWR RR-5703 "delays of a few days are unimportant ...
    most interruptions do not require reinitiation."
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
        # Per-dose log (bugfix #4): record every dose with date + route for
        # later schedule-fit analysis by split_abandoned_dose().
        if v in (VAC_IM, VAC_ID):
            current.dose_log.append((d, v))
        if row.get("age") is not None and current.age is None:
            current.age = row["age"]
    return cases


def _schedule_offsets_match(actual_offsets: list[int],
                            schedule_days: tuple[int, ...],
                            tol: int = SCHEDULE_TOL_DAYS) -> bool:
    """Return True if `actual_offsets` (day numbers from a Day-0 anchor) fit
    the expected PEP schedule `schedule_days` within ±tol days per dose.

    STRICT fit: every actual dose must be accounted for by an expected schedule
    day within ±tol. NO stray doses (which would indicate multi-year merged
    history being misinterpreted as one schedule).
    """
    if len(actual_offsets) < len(schedule_days):
        return False
    # Every actual dose must match at least one expected day (no strays)
    for a in actual_offsets:
        if not any(abs(a - expected) <= tol for expected in schedule_days):
            return False
    # Every expected day must have at least one actual dose matching it
    for expected in schedule_days:
        if not any(abs(a - expected) <= tol for a in actual_offsets):
            return False
    return True


def _fits_any_schedule(offsets_from_anchor: list[int]) -> bool:
    """Does this dose pattern (days from a putative Day 0) match the IM or ID
    PEP schedule? Used to detect a 'clean restart'."""
    return (_schedule_offsets_match(offsets_from_anchor, IM_SCHEDULE_DAYS)
            or _schedule_offsets_match(offsets_from_anchor, ID_SCHEDULE_DAYS))


def refine_clusters_cross_window(cases: list[Case]) -> list[Case]:
    """Refine one HN's case list by detecting 'abandoned dose + clean restart'
    ACROSS time-windowed case boundaries.

    Bugfix #4 (2026-08-11, HN 176434): the 33-day time-window can split what
    is actually a single coherent schedule into two cases — OR merge an
    abandoned dose with the start of a new schedule. Examples:

      HN 176434 timeline (5 vaccine doses + ERIG):
        03/03  ID + ERIG       (1 dose, then patient disappears)
        10/03  ID              (new Day 0)
        13/03  ID              (Day +3)
        17/03  ID              (Day +7)
        07/04  ID              (Day +28 — perfect ID schedule from 10/03)
      Time-window clusters (33d from first dose): case A 03/03→17/03 (4 ID),
                                                  case B 07/04 (1 ID, incomplete).
      Both wrong! 03/03→17/03 doses [0,7,10,14] don't fit any standard schedule,
      and 10/03→07/04 doses [0,3,7,28] form a perfect ID schedule.
      Correct: case A' 03/03 (1 ID, abandoned, incomplete/ID),
               case B' 10/03→07/04 (4 ID, complete/ID).

    STRICT detection (avoids false merges of multi-year histories):
      1. Try every dose as a candidate Day-0 anchor.
      2. For each candidate, check forward doses (anchor + all later).
         STRICT schedule-fit: every dose must match an expected day, no strays.
      3. ALSO require: total forward dose count is in [4, 7] (one schedule's
         worth ± 2 over-dose, never 13 doses spanning years).
      4. ALSO require: total span of forward doses ≤ 35 days (one schedule's
         length + grace, never multi-year).
      5. If candidate anchor fits all 4 conditions AND it's not the first
         dose (meaning there's a true abandoned prefix), split.
      6. Otherwise return cases unchanged.

    Conditions 3+4 are the critical fixes after audit 2026-08-11: without
    them, HN 142753 (5 years of scattered doses) was wrongly merged into
    one "complete" case spanning 2016-2026.

    Reference: hospital policy on restarts — patient lost to follow-up + later
    re-presentation is treated as a new incident, not continuation.
    """
    if len(cases) <= 1:
        return cases
    # Flatten all vaccine doses across all cases, preserving order
    flat: list[tuple] = []  # (date, vac)
    for case in cases:
        for dose in case.dose_log:
            flat.append(dose)
    flat.sort(key=lambda x: x[0])
    if len(flat) < 4:
        return cases

    # Try each dose as a candidate Day-0 anchor for a "clean restart".
    # Apply ALL 4 conditions; take the earliest anchor that satisfies them.
    best_anchor_idx = None
    for i in range(len(flat)):
        anchor_date = flat[i][0]
        forward = flat[i:]
        # Condition 3: dose count
        if not (4 <= len(forward) <= 7):
            continue
        # Condition 4: total span (anchor → last dose)
        span_days = (forward[-1][0] - anchor_date).days
        if span_days > 35:
            continue
        offsets = sorted((d - anchor_date).days for d, _ in forward)
        # Conditions 2 (strict fit, no strays)
        if _fits_any_schedule(offsets):
            best_anchor_idx = i
            break
    if best_anchor_idx is None or best_anchor_idx == 0:
        # Either no anchor fits all conditions, or the first dose itself fits
        # (no abandoned prefix to split off).
        return cases

    # We have an abandoned prefix [0..best_anchor_idx) and a clean series
    # [best_anchor_idx..end). Rebuild cases.
    pre_doses = flat[:best_anchor_idx]
    post_doses = flat[best_anchor_idx:]
    # Source case for ERIG/HRIG allocation: the earliest original case whose
    # time window overlaps the pre-doses. ERIG/HRIG were given at first
    # presentation → stay with the abandoned case.
    pre_d0_date = pre_doses[0][0]
    source_case = None
    for c in cases:
        if c.start_date == pre_d0_date:
            source_case = c
            break
    erig_count = source_case.doses_erig if source_case else 0
    hrig_count = source_case.doses_hrig if source_case else 0

    # Build case A (abandoned, single case for all pre-anchor doses)
    all_names = set()
    for c in cases:
        all_names |= c.names
    case_a = Case(
        hn=cases[0].hn, case_idx=1,
        start_date=pre_doses[0][0],
        end_date=pre_doses[-1][0],
        doses_erig=erig_count,
        doses_hrig=hrig_count,
        age=cases[0].age,
        names=all_names,
        dose_log=list(pre_doses),
    )
    for _, v in pre_doses:
        if v == VAC_IM:
            case_a.doses_im += 1
        elif v == VAC_ID:
            case_a.doses_id += 1
    # Build case B (the clean restart series)
    case_b = Case(
        hn=cases[0].hn, case_idx=2,
        start_date=post_doses[0][0],
        end_date=post_doses[-1][0],
        age=cases[0].age,
        names=set(all_names),
        dose_log=list(post_doses),
    )
    for _, v in post_doses:
        if v == VAC_IM:
            case_b.doses_im += 1
        elif v == VAC_ID:
            case_b.doses_id += 1
    return [case_a, case_b]


def annotate_prior(all_cases_by_hn: dict[str, list[Case]],
                   all_doses_by_hn: dict[str, list[dict]],
                   screening_prior: dict[str, str] | None = None) -> None:
    """Set has_prior + prior_days_ago using the latest prior COMPLETE SERIES.

    CORRECT definition (2026-08-10 bugfix): "prior" = patient previously received
    a COMPLETE rabies vaccination series before this case's start_date. Per the
    Department of Disease Control spec and the hospital's screening app, a
    complete prior series is defined as **≥3 doses** (ID or IM combined) — this
    covers both pre-exposure (3 doses on Day 0,7,21/28) and post-exposure
    full series (IM 5 / ID 4).

    The "≥3 doses" threshold replaces the earlier strict "IM≥5 / ID≥4 / mixed≥4"
    because:
      1. The screening app records "เคยฉีด 3 เข็มหรือมากกว่า" as the prior-status
         field for patients with history at other hospitals
      2. DDC spec defines pre-exposure as 3 doses
      3. A patient who received 3 doses anywhere counts as previously vaccinated
         for booster purposes

    The 180/181-day split (≤180=1 dose, ≥181=2 doses) measures time since the
    COMPLETE series ended. Requires ~10-year lookback for accuracy.

    screening_prior (optional): dict mapping str(HN) → "near"|"far" if the
    screening app indicates prior complete series. Values:
      - "near" = "เคยฉีด 3 เข็ม หรือมากกว่า (ภายใน 6 เดือน)" → prior_days_ago=180
      - "far"  = "เคยฉีด 3 เข็ม หรือมากกว่า (เกิน 6 เดือน)"   → prior_days_ago=365
      - (other) = treat as no prior info

    Captures vaccinations at other hospitals that HIS doesn't record.

    Bugfix #6 (2026-08-11): added --screening CLI flag wires this through.
    Bugfix #7 (2026-08-11): HN dtype normalization (screening HN is float;
    HIS HN is str). Caller MUST convert screening HNs to str(int) for matching.
    """
    def is_complete_series(c: Case) -> bool:
        """A prior case counts as 'complete series' if total vaccine doses
        (IM + ID combined) ≥ 3."""
        return c.total_vac >= 3

    screening_prior = screening_prior or {}
    for hn, cases in all_cases_by_hn.items():
        for c in cases:
            # Source 1: HIS — find prior cases that ARE complete series
            prior_complete = [
                pc for pc in all_cases_by_hn.get(hn, [])
                if pc.start_date < c.start_date and is_complete_series(pc)
            ]
            # Source 2: Screening app — external hospital history
            scr = screening_prior.get(hn)

            if prior_complete:
                last = max(pc.end_date for pc in prior_complete)
                c.has_prior = True
                c.prior_days_ago = (c.start_date - last).days
            elif scr == "near":
                # Screening: "ภายใน 6 เดือน" → set prior_days_ago to a value
                # in the ≤180 range so the booster rule treats it as near
                # (needs 1 dose). Use exactly 180 (boundary).
                c.has_prior = True
                c.prior_days_ago = PRIOR_NEAR_DAYS
            elif scr == "far":
                # Screening: "เกิน 6 เดือน" → ≥181d → needs 2 doses
                c.has_prior = True
                c.prior_days_ago = PRIOR_FAR_DAYS
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
        if total <= 2 and c.has_prior:
            # prior_days_ago None = screening-sourced, unknown exact distance
            # → assume far (≥181d, conservative: needs 2 doses)
            if c.prior_days_ago is None:
                if total >= 2:
                    return ("complete", age_route(c.age) or "ID")
                r = age_route(c.age)
                return ("incomplete", r) if r else ("REVIEW", "NONE")
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
        if c.has_prior:
            # prior_days_ago None = screening-sourced → assume far (≥181d)
            if c.prior_days_ago is None and n >= 2:
                return ("complete", "IM")
            if c.prior_days_ago is not None:
                if c.prior_days_ago <= PRIOR_NEAR_DAYS and n >= 1:
                    return ("complete", "IM")
                if c.prior_days_ago >= PRIOR_FAR_DAYS and n >= 2:
                    return ("complete", "IM")
    else:  # ID
        if n >= 4:
            return ("complete", "ID")
        if c.has_prior:
            if c.prior_days_ago is None and n >= 2:
                return ("complete", "ID")
            if c.prior_days_ago is not None:
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
        # prior=None (screening) + n<2 → incomplete (booster needs 2)
        if c.has_prior and c.prior_days_ago is None and n < 2:
            return ("incomplete", "IM")
    else:
        if n < 3 and not c.has_prior:
            return ("incomplete", "ID")
        if c.has_prior and c.prior_days_ago is not None and c.prior_days_ago >= PRIOR_FAR_DAYS and n < 2:
            return ("incomplete", "ID")
        if c.has_prior and c.prior_days_ago is None and n < 2:
            return ("incomplete", "ID")

    # Should be unreachable for valid data — REVIEW flags a real algorithm gap
    return ("REVIEW", route)


# ── Main pipeline ───────────────────────────────────────────────────────────
def run(quarter_path: Path, history_paths: list[Path],
        period_start: datetime, period_end: datetime,
        screening_path: Optional[Path] = None):
    # Load history first (so prior annotation is correct), then current quarter
    frames = []
    for p in history_paths:
        frames.append(load_xls(p))
        print(f"Loaded history: {p.name}  →  {len(frames[-1])} doses", file=sys.stderr)
    if frames:
        hist_df = pd.concat(frames, ignore_index=True)
    else:
        hist_df = pd.DataFrame(columns=["HN", "date", "vac", "name", "age"])

    # Load screening prior map (bugfix #6+#7, 2026-08-11)
    screening_prior: dict[str, str] = {}
    if screening_path is not None:
        screening_prior = load_screening(screening_path)

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
        # Step 1: time-window clustering (33d first-dose-anchored)
        cases = cluster_cases(sub)
        # Step 2 (bugfix #4, 2026-08-11): cross-window refinement to detect
        # "abandoned dose + clean restart" pattern that the time-window split
        # incorrectly. Runs on the FULL dose timeline, not per-case.
        cases = refine_clusters_cross_window(cases)
        # Renumber case_idx after potential restructure
        for i, c in enumerate(cases, 1):
            c.case_idx = i
        cases_by_hn[hn] = cases
    annotate_prior(cases_by_hn, all_doses_by_hn, screening_prior)

    # Filter: case belongs to the quarter of its END_DATE.
    # Bugfix #5 (2026-08-11, HN 176434): "ถ้ารายการฉีดวัคซีน คาบเกี่ยวหรือข้าม
    # ไตรมาส ต้องยังไม่นับเคสนั้น ให้ถือว่าเคสนั้น ขยับไปอยู่อีก Q ไตรมาสถัดไปแทน"
    # — if a case straddles a quarter boundary, defer it to the quarter where
    # its end_date falls. This matches the hospital's reporting cycle: a case
    # is "done" only when its last dose is given, so it's counted in that
    # quarter. Using start_date double-counted or missed straddling cases.
    # Examples:
    #   - case 10/03→07/04 (start Q2, end Q3) → counted in Q3 (was Q2)
    #   - case entirely in Q3 → end in Q3 → counted in Q3 (unchanged)
    #   - case entirely in Q2 → end in Q2 → counted in Q2 (unchanged)
    in_period: list[Case] = []
    for hn, cases in cases_by_hn.items():
        for c in cases:
            if period_start <= c.end_date <= period_end:
                in_period.append(c)

    print(f"Cases in period: {len(in_period)}", file=sys.stderr)

    # Dose-reconciliation invariant (test-engineer finding #15):
    # With bugfix #5 (end_date-based period assignment), in-period cases may
    # START before period_start (a straddling case). Their early doses still
    # belong to the case. The reconciliation we keep is: every q_df dose whose
    # DATE falls in the report period should be attributable to SOME in-period
    # case OR to a case that straddles into this period from the previous one.
    # (Such doses are counted in THIS period because their case's end_date is
    # in this period — even if a particular dose date is before period_start,
    # the case is reported here.)
    in_period_hns = {c.hn for c in in_period}
    q_in = q_df[(q_df["date"] >= period_start) & (q_df["date"] <= period_end)]
    q_orphan = q_in[~q_in["HN"].isin(in_period_hns)]
    if len(q_orphan):
        print(f"WARN: {len(q_orphan)} in-period quarter doses belong to HNs with no "
              f"in-period case under end_date rule — likely the case ENDS after "
              f"period_end (deferred to next quarter per bugfix #5).",
              file=sys.stderr)
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
    ap.add_argument("--screening", type=Path, default=None,
                    help="Screening-app .xls (no header row; col 1=HN float, "
                         "col 7=prior-status text). Captures prior-complete "
                         "patients vaccinated at other hospitals. Bugfix #6+#7.")
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
    report, mixed, review, breakdown = run(
        args.quarter, args.history, ps, pe, screening_path=args.screening)

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
