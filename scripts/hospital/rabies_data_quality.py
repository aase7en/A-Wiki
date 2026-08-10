#!/usr/bin/env python3
"""Rabies data quality report — scan HIS export for issues before classification.

Run BEFORE classify_rabies.py to catch data problems that would distort the
final report. Issues found here should be resolved (or accepted) before filing.

Usage:
    python scripts/hospital/rabies_data_quality.py <xls> [<xls> ...]

Exit codes:
    0 = clean (no issues or only informational)
    1 = warnings (review before filing)
    2 = errors (data unusable — fix source)
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from collections import Counter

import pandas as pd


def load_raw(path: Path) -> pd.DataFrame:
    """Load xls without any normalization — raw inspection."""
    xl = pd.ExcelFile(path)
    sheet = xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    # find header
    hdr = None
    for i in range(min(10, len(raw))):
        if raw.iloc[i].astype(str).str.contains("ลำดับ", regex=False).any():
            hdr = i
            break
    if hdr is None:
        # legacy: synthetic header
        cols = ["ลำดับ", "HN", "วันที่ตรวจ", "ชื่อ - นามสกุล",
                "อายุ", "เบอร์โทรศัพท์", "สัญชาติ", "วัคซีน"]
        df = raw.copy()
        df.columns = cols[:df.shape[1]]
    else:
        df = pd.read_excel(path, sheet_name=sheet, header=hdr)
        df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def scan_file(path: Path) -> dict:
    """Scan one xls file for data quality issues. Returns dict of findings."""
    out = {"file": path.name, "issues": [], "stats": {}}
    try:
        df = load_raw(path)
    except Exception as e:
        out["issues"].append({"severity": "ERROR", "check": "load", "msg": str(e)})
        return out

    out["stats"]["rows"] = len(df)

    # ── 1. Required columns present ──
    hn_col = find_col(df, ["HN"])
    date_col = find_col(df, ["วันที่ตรวจ", "วันที่ฉีด"])
    vac_col = find_col(df, ["วัคซีน"])
    name_col = find_col(df, ["ชื่อ - นามสกุล", "ชื่อ-นามสกุล"])
    age_col = find_col(df, ["อายุ"])

    for label, col in [("HN", hn_col), ("วันที่ตรวจ", date_col),
                       ("วัคซีน", vac_col)]:
        if col is None:
            out["issues"].append({"severity": "ERROR", "check": "missing_column",
                                  "msg": f"{label} column not found"})

    if not all([hn_col, date_col, vac_col]):
        return out  # can't continue without these

    # ── 2. Empty rows ──
    empty = df[df[hn_col].isna() & df[date_col].isna() & df[vac_col].isna()]
    if len(empty):
        out["issues"].append({"severity": "INFO", "check": "empty_rows",
                              "msg": f"{len(empty)} empty rows (ignored)"})

    # Focus on non-empty rows
    df = df.dropna(subset=[hn_col, date_col, vac_col])
    out["stats"]["valid_rows"] = len(df)

    # ── 3. Duplicate doses (same HN + date + vaccine) ──
    df["HN_str"] = df[hn_col].astype(str).str.strip()
    df["vac_norm"] = df[vac_col].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    dup_mask = df.duplicated(subset=["HN_str", date_col, "vac_norm"], keep=False)
    n_dup = dup_mask.sum()
    if n_dup:
        out["issues"].append({"severity": "WARN", "check": "duplicate_doses",
                              "msg": f"{n_dup} duplicate rows (same HN+date+vaccine) — engine dedups automatically"})
    out["stats"]["duplicates"] = n_dup

    # ── 4. HN format consistency ──
    hn_lens = df["HN_str"].str.replace(r"[^\d]", "", regex=True).str.len()
    len_dist = hn_lens.value_counts().to_dict()
    out["stats"]["hn_lengths"] = len_dist
    if len(len_dist) > 1:
        out["issues"].append({"severity": "WARN", "check": "hn_format_mixed",
                              "msg": f"HN length varies: {len_dist} — cross-year matching may fail"})

    # ── 5. Missing age ──
    if age_col:
        missing_age = df[age_col].isna().sum()
        out["stats"]["missing_age"] = int(missing_age)
        if missing_age:
            pct = missing_age / len(df) * 100
            out["issues"].append({"severity": "WARN" if pct > 5 else "INFO",
                                  "check": "missing_age",
                                  "msg": f"{missing_age} rows ({pct:.1f}%) — Mixed age tiebreak will REVIEW"})

    # ── 6. Date parsing + range ──
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    bad_dates = df[date_col].isna().sum()
    out["stats"]["bad_dates"] = int(bad_dates)
    if bad_dates:
        out["issues"].append({"severity": "ERROR", "check": "bad_dates",
                              "msg": f"{bad_dates} rows with unparseable dates — will be dropped"})
    if df[date_col].notna().any():
        out["stats"]["date_range"] = f"{df[date_col].min().date()} → {df[date_col].max().date()}"

    # ── 7. Unknown vaccine names ──
    known_patterns = ["RABIES VACCINE", "0.5 cc IM", "0.1ml ID", "0.1 ml ID",
                      "ERIG", "EQUINE", "GLOBULIN", "HRIG"]
    def is_known(v):
        v = str(v).upper()
        return any(p.upper() in v for p in known_patterns)
    unknown = df[~df["vac_norm"].apply(is_known)]
    if len(unknown):
        unknown_names = unknown["vac_norm"].value_counts().to_dict()
        out["issues"].append({"severity": "WARN", "check": "unknown_vaccine",
                              "msg": f"{len(unknown)} rows with unrecognized vaccine names: {unknown_names}"})

    # ── 8. Out-of-range ages ──
    if age_col:
        ages = df[age_col].apply(lambda x: None if pd.isna(x) else x)
        # try parse
        import re
        def parse_age(v):
            if pd.isna(v): return None
            m = re.search(r"\d+", str(v))
            return int(m.group()) if m else None
        parsed = ages.apply(parse_age)
        bad_age = parsed[parsed.notna() & ((parsed < 0) | (parsed > 120))]
        if len(bad_age):
            out["issues"].append({"severity": "WARN", "check": "bad_age",
                                  "msg": f"{len(bad_age)} rows with age <0 or >120: {bad_age.tolist()[:5]}"})

    # ── 9. Future dates ──
    if df[date_col].notna().any():
        today = pd.Timestamp.now()
        future = df[df[date_col] > today]
        if len(future):
            out["issues"].append({"severity": "WARN", "check": "future_dates",
                                  "msg": f"{len(future)} rows with date > today"})

    return out


def print_report(results: list[dict]):
    print("=" * 70)
    print("RABIES DATA QUALITY REPORT")
    print("=" * 70)

    total_errors = total_warn = total_info = 0
    for r in results:
        print(f"\n📄 {r['file']}")
        print(f"   rows={r['stats'].get('rows','?')} valid={r['stats'].get('valid_rows','?')}")
        if "date_range" in r["stats"]:
            print(f"   dates: {r['stats']['date_range']}")
        if "hn_lengths" in r["stats"]:
            print(f"   HN lengths: {r['stats']['hn_lengths']}")

        for issue in r["issues"]:
            sev = issue["severity"]
            icon = {"ERROR": "🚨", "WARN": "⚠️ ", "INFO": "ℹ️ "}[sev]
            print(f"   {icon} [{issue['check']}] {issue['msg']}")
            if sev == "ERROR": total_errors += 1
            elif sev == "WARN": total_warn += 1
            else: total_info += 1

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {total_errors} errors, {total_warn} warnings, {total_info} info")
    if total_errors:
        print("❌ FIX ERRORS BEFORE FILING — data unusable as-is")
        return 2
    elif total_warn:
        print("⚠️  REVIEW WARNINGS — engine will handle most, but verify")
        return 1
    else:
        print("✅ CLEAN — safe to classify")
        return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path, help="xls files to scan")
    args = ap.parse_args()

    results = [scan_file(p) for p in args.files]
    sys.exit(print_report(results))


if __name__ == "__main__":
    main()
