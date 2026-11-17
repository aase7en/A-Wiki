#!/usr/bin/env python3
"""token-ab-measure.py — A/B token cost of Thai/English × verbose/compact.

WO-AWIKI-SKILLECO-14 / Issue #76: "Compare 10+ matched A/B fixtures in
Thai/English with auto-on/auto-off … explicitly disclose UNKNOWN billing
where unavailable."

Measures tests/fixtures/token_ab_pairs.json with the shared tokenizer
resolver (tiktoken -> anthropic key-gated -> char/4 proxy) and emits:

  --json   JSONL: one record per pair + a summary record
  default  human table + summary

The counts are OFFLINE tokenizer estimates. Actual provider
input/output/cache billing is UNKNOWN and never claimed here.

Usage:
  python3 scripts/token-ab-measure.py                 # human output
  python3 scripts/token-ab-measure.py --json          # JSONL
  python3 scripts/token-ab-measure.py --tokenizer proxy
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from tokenizer_cost import build_counter

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "token_ab_pairs.json"

BILLING = "UNKNOWN (offline tokenizer estimate; provider billing not measured)"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def _ratio(num: int, den: int) -> float:
    return round(num / den, 3) if den else 0.0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--tokenizer", default="auto",
                   choices=("auto", "tiktoken", "anthropic", "proxy"))
    p.add_argument("--json", action="store_true", help="machine-readable JSONL")
    args = p.parse_args()

    count, backend = build_counter(args.tokenizer)
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pairs = data["pairs"]

    records = []
    sums = {"thai_verbose_tokens": 0, "thai_compact_tokens": 0,
            "english_verbose_tokens": 0, "english_compact_tokens": 0}
    for pair in pairs:
        t, e = pair["thai"], pair["english"]
        rec = {
            "record": "pair", "id": pair["id"], "category": pair["category"],
            "thai_verbose_tokens": count(t["verbose"]),
            "thai_compact_tokens": count(t["compact"]),
            "english_verbose_tokens": count(e["verbose"]),
            "english_compact_tokens": count(e["compact"]),
        }
        rec["thai_ratio"] = _ratio(rec["thai_verbose_tokens"],
                                   rec["english_verbose_tokens"])
        rec["english_compact_ratio"] = _ratio(rec["english_compact_tokens"],
                                              rec["english_verbose_tokens"])
        rec["thai_compact_ratio"] = _ratio(rec["thai_compact_tokens"],
                                           rec["thai_verbose_tokens"])
        for k in sums:
            sums[k] += rec[k]
        records.append(rec)

    n = len(pairs)
    summary = {
        "record": "summary", "pairs": n, "tokenizer": backend,
        "billing": BILLING,
        "mean_thai_ratio": _ratio(sums["thai_verbose_tokens"],
                                  sums["english_verbose_tokens"]),
        "mean_english_compact_ratio": _ratio(sums["english_compact_tokens"],
                                             sums["english_verbose_tokens"]),
        "mean_thai_compact_ratio": _ratio(sums["thai_compact_tokens"],
                                          sums["thai_verbose_tokens"]),
    }

    if args.json:
        for rec in records + [summary]:
            print(json.dumps(rec, ensure_ascii=False))
        return 0

    print(f"tokenizer: {backend}")
    print(f"billing:   {BILLING}")
    print(f"{'id':<22}{'th v':>6}{'th c':>6}{'en v':>6}{'en c':>6}"
          f"{'th/en':>7}{'c/v en':>8}{'c/v th':>8}")
    for rec in records:
        print(f"{rec['id']:<22}{rec['thai_verbose_tokens']:>6}"
              f"{rec['thai_compact_tokens']:>6}{rec['english_verbose_tokens']:>6}"
              f"{rec['english_compact_tokens']:>6}{rec['thai_ratio']:>7}"
              f"{rec['english_compact_ratio']:>8}{rec['thai_compact_ratio']:>8}")
    print(f"mean thai/english: {summary['mean_thai_ratio']}  "
          f"compact/verbose en: {summary['mean_english_compact_ratio']}  "
          f"th: {summary['mean_thai_compact_ratio']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
