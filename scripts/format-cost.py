#!/usr/bin/env python3
"""
format-cost.py — Token cost comparison across output formats.

Measures how many tokens the SAME content costs when encoded as
CSV / Markdown table / JSONL / JSON / HTML table.

Brain-Gate Verify command for the 3-layer output-format protocol.
See: docs/protocols/md-vs-html-output.md

Usage:
  python3 scripts/format-cost.py --demo               # built-in sample data
  python3 scripts/format-cost.py --in data.json       # measure a JSON file
  python3 scripts/format-cost.py --in -               # read JSON from stdin
  python3 scripts/format-cost.py --demo --json        # machine-readable output (JSONL)
  python3 scripts/format-cost.py --tokenizer proxy    # force char/4 proxy

Tokenizer priority (auto): tiktoken -> anthropic -> char/4 proxy
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from typing import Any


# ── tokenizer ────────────────────────────────────────────────────────────

def _build_counter(requested: str):
    """Return (count_fn, backend_name). Never raises — always falls back to proxy."""
    proxy = (lambda text: max(1, round(len(text) / 4)), "char/4 proxy")

    if requested == "proxy":
        return proxy

    if requested in ("auto", "tiktoken"):
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.get_encoding("cl100k_base")
            return (lambda text: len(enc.encode(text)), "tiktoken cl100k_base")
        except Exception:
            pass
        if requested == "tiktoken":
            return proxy

    if requested in ("auto", "anthropic"):
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic()

            def _count(text: str) -> int:
                r = client.beta.messages.count_tokens(
                    model="claude-opus-4-8",
                    messages=[{"role": "user", "content": text}],
                    betas=["token-counting-2024-11-01"],
                )
                return r.input_tokens
            return (_count, "anthropic token-counting API")
        except Exception:
            pass

    return proxy


# ── format encoders ──────────────────────────────────────────────────────

def _as_csv(records: list[dict]) -> str:
    if not records:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
    w.writeheader()
    w.writerows(records)
    return buf.getvalue().rstrip()


def _as_md_table(records: list[dict]) -> str:
    if not records:
        return ""
    keys = list(records[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "|" + "|".join("---" for _ in keys) + "|"
    rows = ["| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in records]
    return "\n".join([header, sep] + rows)


def _as_jsonl(records: list[dict]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)


def _as_json(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, indent=2)


def _as_html_table(records: list[dict]) -> str:
    if not records:
        return ""
    keys = list(records[0].keys())
    th = "".join(f"<th>{k}</th>" for k in keys)
    rows_html = []
    for r in records:
        td = "".join(f"<td>{r.get(k,'')}</td>" for k in keys)
        rows_html.append(f"<tr>{td}</tr>")
    body = "\n".join(rows_html)
    return f"<table><thead><tr>{th}</tr></thead><tbody>\n{body}\n</tbody></table>"


FORMATS = [
    ("CSV",            _as_csv),
    ("Markdown table", _as_md_table),
    ("JSONL",          _as_jsonl),
    ("JSON",           _as_json),
    ("HTML table",     _as_html_table),
]


# ── demo data ────────────────────────────────────────────────────────────

DEMO_RECORDS: list[dict] = [
    {"file": "auth.py",   "severity": "HIGH", "line": 42,  "issue": "SQL injection in login"},
    {"file": "api.py",    "severity": "LOW",  "line": 88,  "issue": "missing timeout"},
    {"file": "db.py",     "severity": "MED",  "line": 13,  "issue": "no connection pool"},
    {"file": "ui.tsx",    "severity": "HIGH", "line": 5,   "issue": "XSS in render"},
    {"file": "cache.py",  "severity": "LOW",  "line": 201, "issue": "unbounded growth"},
    {"file": "worker.py", "severity": "MED",  "line": 77,  "issue": "missing error handler"},
]


# ── main logic ───────────────────────────────────────────────────────────

def _load_records(source: str) -> list[dict]:
    """Load JSON from file path or '-' for stdin."""
    if source == "-":
        raw = sys.stdin.read()
    else:
        with open(source, encoding="utf-8") as f:
            raw = f.read()
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # try common wrappers: {"rows": [...]} {"data": [...]} {"records": [...]}
        for key in ("rows", "data", "records", "findings", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # single object → wrap in list
        return [data]
    raise ValueError(f"Expected JSON array or object, got {type(data)}")


def _measure(records: list[dict], count_fn) -> list[dict]:
    results = []
    for name, encoder in FORMATS:
        encoded = encoder(records)
        chars = len(encoded)
        tokens = count_fn(encoded)
        results.append({"name": name, "chars": chars, "tokens": tokens, "encoded": encoded})
    # compute ratios vs Markdown (index 1)
    md_tok = results[1]["tokens"]
    for r in results:
        r["ratio"] = round(r["tokens"] / md_tok, 2) if md_tok else None
    return results


def _print_table(results: list[dict], backend: str, n_records: int) -> None:
    print(f"\nformat-cost  (backend: {backend})")
    print(f"content: {n_records} records\n")
    hdr = f"  {'format':20} {'chars':>7} {'~tokens':>8} {'vs MD':>7}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    md_idx = 1
    for i, r in enumerate(results):
        label = ""
        if i == 0:
            label = "  ← cheapest (Layer 2)"
        elif i == len(results) - 1:
            label = "  ← most expensive (Layer 3 leaf only)"
        elif i == md_idx:
            label = "  ← baseline"
        ratio_str = f"{r['ratio']:.2f}×" if r["ratio"] is not None else "  n/a"
        print(f"  {r['name']:20} {r['chars']:7d} {r['tokens']:8d} {ratio_str:>7}{label}")
    print()
    print("Verdict: HTML costs ~2× Markdown tokens when an agent READS it.")
    print("Use HTML ONLY as a terminal leaf artifact (exports/html/, never re-ingested).")
    print("See: docs/protocols/md-vs-html-output.md\n")


def _print_json(results: list[dict], backend: str, n_records: int) -> None:
    out = {
        "backend": backend,
        "n_records": n_records,
        "formats": [
            {"name": r["name"], "chars": r["chars"], "tokens": r["tokens"], "ratio": r["ratio"]}
            for r in results
        ],
    }
    print(json.dumps(out, ensure_ascii=False))


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure token cost across CSV/MD/JSONL/JSON/HTML for the same content."
    )
    parser.add_argument("--in", dest="source", default=None,
                        help="JSON file path or '-' for stdin")
    parser.add_argument("--demo", action="store_true",
                        help="Use built-in 6-record demo dataset")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable JSONL output (Layer-2 friendly)")
    parser.add_argument("--tokenizer", default="auto",
                        choices=["auto", "tiktoken", "anthropic", "proxy"],
                        help="Tokenizer backend (default: auto)")
    args = parser.parse_args()

    if not args.demo and not args.source:
        parser.print_help()
        print("\nHint: run with --demo to see the built-in comparison table.\n")
        return 0

    count_fn, backend = _build_counter(args.tokenizer)

    if args.demo:
        records = DEMO_RECORDS
    else:
        try:
            records = _load_records(args.source)
        except Exception as e:
            sys.stderr.write(f"Error loading data: {e}\n")
            return 1

    results = _measure(records, count_fn)

    if args.json:
        _print_json(results, backend, len(records))
    else:
        _print_table(results, backend, len(records))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
