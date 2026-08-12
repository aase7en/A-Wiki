#!/usr/bin/env python3
"""Rabies engine regression verifier.

Loads `regression_HNs.yaml` (single source of truth for pinned bug-HN cases)
and replays each through cluster_cases + refine_clusters_cross_window +
annotate_prior + classify. Compares actual output to expected.

Exit codes:
  0 = all HNs match expected classification
  1 = YAML parse error or schema problem (engine wasn't run)
  2 = at least one HN regression detected (engine output != expected)

Usage:
  python scripts/hospital/verify_regression.py             # default location
  python scripts/hospital/verify_regression.py --yaml path/to/custom.yaml
  SKIP_REGRESSION=1 python scripts/hospital/verify_regression.py  # emergency bypass

Why this exists (Layer 3 of v1.4.0 anti-hallucination):
  The engine has 61 unit tests for classify() with hand-built Case objects.
  But the FULL pipeline (load_xls → cluster_cases → refine_clusters → annotate
  → classify) is only exercised against real .xls files — no synthetic-timeline
  regression test exists. This verifier fills that gap: it builds synthetic
  timelines from YAML, runs them through the real pipeline, and asserts the
  expected classification.

  When a new bug is found + fixed in the future, ADD AN ENTRY to regression_HNs.yaml
  so the bug cannot silently reappear.
"""
from __future__ import annotations
import os
import sys
from datetime import datetime
from pathlib import Path

# Make scripts/hospital importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

# Lazy import of pyyaml — only needed here, not in classify_rabies
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

import classify_rabies as cr


# Vaccine name mapping (YAML uses short codes; engine uses full names)
_VAC_MAP = {
    "IM":   cr.VAC_IM,
    "ID":   cr.VAC_ID,
    "ERIG": cr.VAC_ERIG,
    "HRIG": cr.VAC_HRIG,
}


def build_dataframe(timeline: list[dict]) -> pd.DataFrame:
    """Build a per-HN DataFrame from a YAML timeline entry."""
    rows = []
    for entry in timeline:
        vac_code = entry["vac"]
        vac_full = _VAC_MAP.get(vac_code)
        if vac_full is None:
            raise ValueError(f"Unknown vac code {vac_code!r} in timeline")
        # Main vaccine dose
        d = datetime.fromisoformat(entry["date"])
        rows.append({
            "HN": "REGRESS", "date": d, "vac": vac_full,
            "name": "R", "age": entry.get("age", 30),
        })
        # Optional ERIG at same date (presentation dose)
        if entry.get("erig"):
            rows.append({
                "HN": "REGRESS", "date": d, "vac": cr.VAC_ERIG,
                "name": "R", "age": entry.get("age", 30),
            })
    return pd.DataFrame(rows)


def run_one(entry: dict) -> tuple[list[tuple[str, str]], list]:
    """Run the engine pipeline on one YAML entry.
    Returns (actual_classifications, case_objects).
    """
    df = build_dataframe(entry["timeline"])

    # Full pipeline
    cases = cr.cluster_cases(df)
    cases = cr.refine_clusters_cross_window(cases)
    for i, c in enumerate(cases, 1):
        c.case_idx = i

    # annotate_prior needs a cases_by_hn dict + all_doses_by_hn dict
    hn_str = str(df["HN"].iloc[0])
    cases_by_hn = {hn_str: cases}
    all_doses_by_hn = {hn_str: df[["date", "vac"]].to_dict("records")}
    cr.annotate_prior(cases_by_hn, all_doses_by_hn, screening_prior={})

    # Classify each case
    classifications = [cr.classify(c) for c in cases]
    return classifications, cases


def verify_entry(entry: dict) -> list[str]:
    """Verify one entry. Returns list of error strings (empty = pass)."""
    errors = []
    hn = entry.get("hn", "<unknown>")
    try:
        actual, cases = run_one(entry)
    except Exception as e:
        return [f"HN {hn}: engine crashed on timeline — {type(e).__name__}: {e}"]

    # Check case count
    expected_n = entry.get("expected_cases")
    if expected_n is not None and len(actual) != expected_n:
        errors.append(
            f"HN {hn}: case count mismatch — "
            f"expected {expected_n}, got {len(actual)}")

    # Check each case's classification
    expected_list = entry.get("expected", [])
    for i, (actual_cat_route, expected_dict) in enumerate(zip(actual, expected_list)):
        actual_cat, actual_route = actual_cat_route
        if actual_cat != expected_dict["category"]:
            errors.append(
                f"HN {hn} case#{i+1}: category mismatch — "
                f"expected {expected_dict['category']!r}, got {actual_cat!r}")
        if actual_route != expected_dict["route"]:
            errors.append(
                f"HN {hn} case#{i+1}: route mismatch — "
                f"expected {expected_dict['route']!r}, got {actual_route!r}")

    # If we have more actual cases than expected, flag extras
    if len(actual) > len(expected_list):
        for i in range(len(expected_list), len(actual)):
            errors.append(
                f"HN {hn} case#{i+1}: UNEXPECTED extra case "
                f"{actual[i]} (no expected entry in YAML)")

    return errors


def main() -> int:
    if os.environ.get("SKIP_REGRESSION"):
        print("SKIP_REGRESSION=1 — bypass", file=sys.stderr)
        return 0

    yaml_path = Path(__file__).resolve().parent / "regression_HNs.yaml"
    # Also check for drive-side raw-HN copy (prefers drive if present)
    drive_yaml = Path("drive/hospital-uthai/RabiesVacc/regression_HNs.yaml")
    if drive_yaml.exists():
        yaml_path = drive_yaml
        print(f"Using drive-side raw-HN copy: {yaml_path}", file=sys.stderr)

    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found", file=sys.stderr)
        return 1

    try:
        entries = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR: YAML parse failed: {e}", file=sys.stderr)
        return 1

    if not isinstance(entries, list):
        print(f"ERROR: YAML top-level must be a list, got {type(entries).__name__}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    n_pass = 0
    for entry in entries:
        if not isinstance(entry, dict):
            all_errors.append(f"Entry not a dict: {entry!r}")
            continue
        errs = verify_entry(entry)
        hn = entry.get("hn", "<unknown>")
        pattern = entry.get("pattern", "")
        if errs:
            all_errors.extend(errs)
            print(f"  ❌ HN {hn:<10} ({pattern})", file=sys.stderr)
            for e in errs:
                print(f"      {e}", file=sys.stderr)
        else:
            n_pass += 1
            print(f"  ✅ HN {hn:<10} ({pattern})")

    print()
    if all_errors:
        print(f"🚨 REGRESSION DETECTED: {len(all_errors)} error(s) across "
              f"{len(entries) - n_pass} HN(s). {n_pass}/{len(entries)} passed.",
              file=sys.stderr)
        print(f"\nOverride (emergencies only): SKIP_REGRESSION=1", file=sys.stderr)
        return 2

    print(f"✅ All {len(entries)} regression HNs match expected classification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
