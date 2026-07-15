#!/usr/bin/env python3
"""MC benchmark harness — accuracy + wall-time across N for pseudo/Sobol/Halton.

M2: per AGENTS.md rule 7 (render, don't dump), emit compact JSON → (optionally)
render to gitignored leaf HTML in exports/html/. The JSON is the durable
artifact; HTML is a presentation leaf that agents never re-ingest.

For each N in --n-levels, runs three MC methods on a chosen integrand:
  - pseudo: numpy default_rng uniform → inverse-CDF
  - sobol:  scipy.stats.qmc.Sobol (N=2^k preferred for balance property)
  - halton: scipy.stats.qmc.Halton (arbitrary N)

Records (estimate, abs_error, se, wall_time_s) per (N, method) so downstream
can plot accuracy-vs-cost (the benchmark's two axes).

Iron Law #8: all integrands are synthetic with known closed-form answers
(normal_mean: E[N(0,1)]=0). No real market data, no advice.

Integrand registry (extensible):
  - normal_mean: E[N(0,1)]=0 via Φ⁻¹(U); 1-D effective per sample

Usage:
    python scripts/benchmark_mc.py \\
        --integrand normal_mean --n-levels 1000,4096,16384,65536 \\
        --d 5 --out exports/bench/mc-bench.json

[verified 2026-07-15]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

# scipy is required (declared in requirements-optional.txt). Import lazily so
# `python scripts/benchmark_mc.py --help` works even without scipy installed.
def _import_qmc():
    from scipy.stats import qmc, norm
    return qmc, norm


# ---------------------------------------------------------------------------
# Integrand registry — each entry: (description, closed_form_answer, evaluator)
# Evaluators take (points_uniform_Nxd) and return per-sample scalar values.
# ---------------------------------------------------------------------------

def _eval_normal_mean(pts_uniform, norm):
    """E[N(0,1)] = 0 via inverse-CDF identity Φ⁻¹(U) ~ N(0,1)."""
    return norm.ppf(pts_uniform)


INTEGRANDS = {
    "normal_mean": {
        "description": "E[N(0,1)] = 0 via Φ⁻¹(U); standard inverse-CDF identity",
        "closed_form": 0.0,
        "eval": _eval_normal_mean,
    },
}


# ---------------------------------------------------------------------------
# Core harness
# ---------------------------------------------------------------------------

def _sample(method: str, N: int, d: int, seed: int, qmc):
    """Return (N, d) uniform point set for the requested method."""
    if method == "pseudo":
        return np.random.default_rng(seed).uniform(size=(N, d))
    if method == "sobol":
        return qmc.Sobol(d=d, scramble=True, seed=seed).random(N)
    if method == "halton":
        return qmc.Halton(d=d, scramble=True, seed=seed).random(N)
    raise ValueError(f"unknown method: {method}")


def run_benchmark(integrand: str = "normal_mean",
                  n_levels=(1000, 4096, 16384, 65536),
                  d: int = 5,
                  seed: int = 42) -> dict:
    """Run pseudo + Sobol + Halton at each N level; return result dict.

    Contract (pinned by tests/test_benchmark_mc.py):
        {
          "title": str, "subtitle": str, "non_advisory_banner": str,
          "integrand": str, "d": int, "seed": int,
          "levels": [{"N": int, "results": {
              "pseudo": {"estimate","abs_error","se","wall_time_s"},
              "sobol":  {...},
              "halton": {...},
          }}, ...]
        }
    """
    if integrand not in INTEGRANDS:
        raise ValueError(f"unknown integrand {integrand!r}; choose from {list(INTEGRANDS)}")
    spec = INTEGRANDS[integrand]
    qmc, norm = _import_qmc()

    levels = []
    for N in n_levels:
        row = {"N": int(N), "results": {}}
        for method in ("pseudo", "sobol", "halton"):
            t0 = time.perf_counter()
            pts = _sample(method, N, d, seed, qmc)
            vals = spec["eval"](pts, norm)
            estimate = float(vals.mean())
            wall = time.perf_counter() - t0
            row["results"][method] = {
                "estimate": estimate,
                "abs_error": float(abs(estimate - spec["closed_form"])),
                "se": float(vals.std() / np.sqrt(N)),
                "wall_time_s": float(wall),
            }
        levels.append(row)

    return {
        "title": f"MC Benchmark — {integrand}",
        "subtitle": f"pseudo vs Sobol vs Halton, d={d}, seed={seed}",
        "non_advisory_banner": "PAPER-ONLY · NON-ADVISORY · synthetic integrand with closed-form answer",
        "integrand": integrand,
        "closed_form": spec["closed_form"],
        "d": d,
        "seed": seed,
        "levels": levels,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--integrand", default="normal_mean",
                   choices=list(INTEGRANDS),
                   help="integrand to benchmark (default: normal_mean)")
    p.add_argument("--n-levels", default="1000,4096,16384,65536",
                   help="comma-separated N levels (default: 1000,4096,16384,65536)")
    p.add_argument("--d", type=int, default=5, help="dimension (default: 5)")
    p.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    p.add_argument("--out", default="exports/bench/mc-bench.json",
                   help="output JSON path (default: exports/bench/mc-bench.json)")
    p.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = p.parse_args()

    n_levels = [int(x) for x in args.n_levels.split(",")]
    result = run_benchmark(args.integrand, n_levels, args.d, args.seed)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    out.write_text(json.dumps(result, indent=indent), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"  integrand={args.integrand}  d={args.d}  levels={n_levels}")
    # Brief stdout summary
    for lvl in result["levels"]:
        line = f"  N={lvl['N']:<6} "
        for m in ("pseudo", "sobol", "halton"):
            r = lvl["results"][m]
            line += f"{m}:err={r['abs_error']:.5f},t={r['wall_time_s']*1000:.1f}ms  "
        print(line)


if __name__ == "__main__":
    main()
