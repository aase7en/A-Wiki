#!/usr/bin/env python3
"""
race_eval.py — Multi-model concurrent race eval (R2).

Fires N models × k samples at the SAME case concurrently (ThreadPoolExecutor),
collects ALL results (not first-past-the-post like delegate.sh's run_race),
and computes pass@k per model. Two verdicts:

  - **winner** (first-past-the-post): model whose FIRST sample completed
    earliest AND passed — useful for production latency-sensitive routing.
  - **best** (highest pass@k): model with the best quality — useful for
    cost-aware selection.

This complements run_subagent_eval.py (which tests models one at a time
sequentially). Race mode is for head-to-head comparison on the same prompt
under the same wall-clock budget.

Thread-safety: delegate_to_model() passes `env={**os.environ,
"AWIKI_FORCE_MODEL": ...}` per subprocess, so concurrent calls do not
collide on a shared env var.

Usage:
  # Dry-run: print the plan, make ZERO API calls (default, safe)
  python scripts/eval/race_eval.py --suite coding --models deepseek-v4-flash,glm-5.2 --dry-run

  # Real run: race 3 models on the coding suite, k=2, 4 concurrent
  python scripts/eval/race_eval.py --suite coding --models deepseek-v4-flash,deepseek-v4-pro,glm-5.2 --k 2 --max-workers 6

  # Race a single case by id
  python scripts/eval/race_eval.py --suite medical --models a,b --case case-1 --k 3

Cost note: race_eval makes len(models) * k calls per case — parallel makes
it FASTER but not CHEAPER. Use --dry-run first to see the call count.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

# DRY: reuse the canonical delegate + judge + pass@k from the single-model runner.
from run_subagent_eval import (
    DEFAULT_K,
    delegate_to_model,
    discover_suites,
    estimate_tokens,
    judge,
    load_suite,
    pass_at_k,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUITES_DIR = REPO_ROOT / "evals" / "subagents"


# ---------------------------------------------------------------------------
# Core: race a single case across models × k (concurrent)
# ---------------------------------------------------------------------------
def race_eval(
    models: list[str],
    case: dict,
    k: int,
    max_workers: int = 4,
    judge_fn: Callable[[dict, str], bool] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Race N models × k samples on ONE case concurrently.

    Each (model, sample_i) pair is a unit of work dispatched to a thread
    pool. Results are collected per-model; pass@k is computed per-model.

    Args:
      models: candidate model shorthand ids (resolved by delegate_to_model).
      case: eval case dict (id, prompt, required[], forbidden[]).
      k: samples per model.
      max_workers: thread pool size (caps concurrency).
      judge_fn: override the default keyword judge. Defaults to run_subagent_eval.judge.
      dry_run: if True, make ZERO delegate calls — return a plan skeleton.

    Returns:
      {
        case_id, by_model: {model: {pass_at_k, passed, total_samples,
                                     first_pass_sample, samples}},
        winner (first-past-the-post), best (highest pass@k), dry_run
      }
    """
    jfn = judge_fn or judge
    prompt = case.get("prompt", "")

    if dry_run:
        return {
            "case_id": case.get("id", "?"),
            "by_model": {m: {"pass_at_k": 0.0, "passed": 0, "total_samples": k,
                             "first_pass_sample": None, "samples": []}
                         for m in models},
            "winner": None,
            "best": None,
            "dry_run": True,
        }

    # Build the work units: (model, sample_index) for all models × k.
    work_units = [(m, i) for m in models for i in range(k)]

    # results[model] = list of (sample_index, passed, completion_order, response_preview)
    results: dict[str, list[dict]] = {m: [] for m in models}
    completion_counter = [0]  # mutable counter for ordering (thread-safe via GIL for ints)

    def _do_one(unit):
        model, sample_idx = unit
        try:
            resp = delegate_to_model(model, prompt)
            passed = jfn(case, resp)
        except Exception:
            resp = ""
            passed = False
        completion_counter[0] += 1
        order = completion_counter[0]
        # S6.0: estimate tokens for cost tracking
        tok_in = estimate_tokens(prompt)
        tok_out = estimate_tokens(resp)
        return model, sample_idx, passed, order, resp[:200], tok_in, tok_out

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_do_one, u) for u in work_units]
        for fut in concurrent.futures.as_completed(futures):
            model, sample_idx, passed, order, preview, tok_in, tok_out = fut.result()
            results[model].append({
                "sample_index": sample_idx,
                "pass": passed,
                "completion_order": order,
                "response_preview": preview,
                "tokens_in": tok_in,
                "tokens_out": tok_out,
            })

    # Finalize per-model stats.
    by_model: dict[str, Any] = {}
    for model, samples in results.items():
        # Sort by sample_index so pass_at_k sees them in generation order.
        samples.sort(key=lambda s: s["sample_index"])
        flat = [{"pass": s["pass"]} for s in samples]
        pak = pass_at_k(flat, k)
        passed = sum(1 for s in samples if s["pass"])
        # first_pass_sample = completion_order of the earliest sample that passed
        passing_orders = [s["completion_order"] for s in samples if s["pass"]]
        first_pass = min(passing_orders) if passing_orders else None
        # S6.0: aggregate tokens for cost tracking
        total_in = sum(s.get("tokens_in", 0) for s in samples)
        total_out = sum(s.get("tokens_out", 0) for s in samples)
        by_model[model] = {
            "pass_at_k": round(pak, 3),
            "passed": passed,
            "total_samples": len(samples),
            "first_pass_sample": first_pass,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "samples": samples,
        }

    # winner = first-past-the-post: lowest completion_order among passing models.
    winner = None
    best_order = None
    for model, stats in by_model.items():
        fp = stats["first_pass_sample"]
        if fp is not None and (best_order is None or fp < best_order):
            best_order = fp
            winner = model

    # best = highest pass@k (ties → most passed).
    best = None
    best_pak = -1.0
    best_passed = -1
    for model, stats in by_model.items():
        pak = stats["pass_at_k"]
        npass = stats["passed"]
        if pak > best_pak or (pak == best_pak and npass > best_passed):
            best_pak = pak
            best_passed = npass
            best = model

    return {
        "case_id": case.get("id", "?"),
        "by_model": by_model,
        "winner": winner,
        "best": best,
        "dry_run": False,
    }


# ---------------------------------------------------------------------------
# Race multiple cases (a suite or subset)
# ---------------------------------------------------------------------------
def run_race(
    models: list[str],
    cases: list[dict],
    k: int,
    max_workers: int = 4,
    judge_fn: Callable[[dict, str], bool] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run race_eval across multiple cases. Returns per-case + overall results.

    For each case, runs race_eval(models, case, k, ...). Aggregates a
    per-model pass@k across all cases (mean).
    """
    by_case: dict[str, Any] = {}
    model_paks: dict[str, list[float]] = {m: [] for m in models}
    model_wins: dict[str, int] = {m: 0 for m in models}

    for case in cases:
        r = race_eval(models, case, k, max_workers, judge_fn, dry_run)
        by_case[r["case_id"]] = r
        if r["winner"]:
            model_wins[r["winner"]] = model_wins.get(r["winner"], 0) + 1
        for m, stats in r["by_model"].items():
            model_paks.setdefault(m, []).append(stats["pass_at_k"])

    overall = {}
    for m, paks in model_paks.items():
        overall[m] = {
            "mean_pass_at_k": round(sum(paks) / len(paks), 3) if paks else 0.0,
            "wins": model_wins.get(m, 0),
            "cases": len(paks),
        }

    return {"by_case": by_case, "overall": overall, "dry_run": dry_run}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def render_race_report(race_result: dict[str, Any]) -> str:
    """Render a compact single-case race result as a text table."""
    lines = []
    cid = race_result.get("case_id", "?")
    lines.append(f"🏁 Race — case: {cid}")
    lines.append("")
    if race_result.get("dry_run"):
        lines.append("  (dry-run — zero API calls)")
        return "\n".join(lines)
    by_model = race_result.get("by_model", {})
    if not by_model:
        lines.append("  (no models)")
        return "\n".join(lines)
    header = f"{'model':<28} {'pass@k':>7} {'passed':>7} {'1st_pass':>9} {'verdict'}"
    lines.append(header)
    lines.append("-" * len(header))
    winner = race_result.get("winner")
    best = race_result.get("best")
    for model in sorted(by_model.keys(), key=lambda m: -by_model[m]["pass_at_k"]):
        s = by_model[model]
        verdicts = []
        if model == winner:
            verdicts.append("🏆winner")
        if model == best and model != winner:
            verdicts.append("⭐best")
        if model != winner and model != best:
            verdicts.append("-")
        fp = str(s["first_pass_sample"]) if s["first_pass_sample"] is not None else "-"
        lines.append(
            f"{model:<28} {s['pass_at_k']:>7.2f} {s['passed']:>4}/{s['total_samples']:<2} "
            f"{fp:>9} {' '.join(verdicts)}"
        )
    return "\n".join(lines)


def render_multi_case_report(run_result: dict[str, Any]) -> str:
    """Render run_race() output (multiple cases) as a summary table."""
    lines = []
    overall = run_result.get("overall", {})
    if not overall:
        return "(no models or no cases)"
    lines.append("🏁 Race summary (across all cases)")
    lines.append("")
    if run_result.get("dry_run"):
        lines.append("  (dry-run — zero API calls)")
    header = f"{'model':<28} {'mean pass@k':>12} {'wins':>5} {'cases':>6}"
    lines.append(header)
    lines.append("-" * len(header))
    for model in sorted(overall.keys(), key=lambda m: -overall[m]["mean_pass_at_k"]):
        s = overall[model]
        lines.append(
            f"{model:<28} {s['mean_pass_at_k']:>12.3f} {s['wins']:>5} {s['cases']:>6}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--suite", required=True, help="suite name (e.g. medical)")
    p.add_argument("--models", required=True,
                   help="comma-separated model shorthand ids (e.g. deepseek-v4-flash,glm-5.2)")
    p.add_argument("--k", type=int, default=DEFAULT_K, help="samples per model per case")
    p.add_argument("--max-workers", type=int, default=4,
                   help="max concurrent delegate calls (thread pool size)")
    p.add_argument("--case", default=None,
                   help="race only this case id (default: all cases in suite)")
    p.add_argument("--dry-run", action="store_true",
                   help="print plan, make ZERO API calls")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = p.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        print("❌ no models given", file=sys.stderr)
        return 1

    suite_path = SUITES_DIR / f"{args.suite}.json"
    suite = load_suite(suite_path)
    if suite is None:
        print(f"❌ suite not found or invalid: {suite_path}", file=sys.stderr)
        return 1

    cases = suite["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            print(f"❌ case '{args.case}' not found in suite '{args.suite}'", file=sys.stderr)
            return 1

    total_calls = 0 if args.dry_run else len(cases) * len(models) * args.k
    plan = {
        "suite": args.suite, "models": models, "k": args.k,
        "max_workers": args.max_workers, "cases": len(cases),
        "estimated_calls": total_calls, "dry_run": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return 0

    if args.json:
        result = run_race(models, cases, args.k, args.max_workers)
        print(json.dumps(result, indent=2, default=str))
        return 0

    print(f"🏁 Racing {len(models)} models on {len(cases)} case(s) × k={args.k} "
          f"(~{total_calls} calls, max {args.max_workers} concurrent)\n")
    result = run_race(models, cases, args.k, args.max_workers)
    for cid, race in result["by_case"].items():
        print(render_race_report(race))
        print()
    print(render_multi_case_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
