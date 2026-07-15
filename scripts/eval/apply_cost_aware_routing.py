#!/usr/bin/env python3
"""apply_cost_aware_routing.py — Q5 CLI for cost-aware Pareto model selection.

Loads eval results, applies the Pareto recommendation (cheapest model above
pass@k threshold) per suite, and optionally applies to subagent frontmatter.

Usage:
  # Preview only (default — no writes)
  python scripts/eval/apply_cost_aware_routing.py \\
      --eval-results evals/subagents/results/ \\
      --min-pass-at-k 0.7

  # With monthly budget cap
  python scripts/eval/apply_cost_aware_routing.py --eval-results ... \\
      --min-pass-at-k 0.7 --cost-budget 5.0 --estimated-calls 10000

  # Apply to frontmatter
  python scripts/eval/apply_cost_aware_routing.py --eval-results ... --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import cost_aware_recommend as ca  # noqa: E402
from apply_eval_results import build_suite_to_subagents  # noqa: E402

SUBAGENTS_DIR = REPO_ROOT / "agents" / "subagents"
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
RESULTS_DIR = SUITES_DIR / "results"


def _load_results(results_path: Path) -> dict:
    rpath = Path(results_path)
    if rpath.is_dir():
        files = sorted(rpath.glob("results-*.json"))
    elif rpath.is_file():
        files = [rpath]
    else:
        return {}
    merged: dict = {}
    for f in files:
        try:
            merged.update(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return merged


def _apply_to_frontmatter(suite: str, recommended: str,
                          suite_to_subagents: dict) -> int:
    """Write the recommended model to each subagent in the suite."""
    applied = 0
    for sa in suite_to_subagents.get(suite, []):
        sa_path = SUBAGENTS_DIR / f"{sa}.md"
        if not sa_path.is_file():
            continue
        text = sa_path.read_text(encoding="utf-8")
        new_text = re.sub(r"^model:\s*.+$", f"model: {recommended}",
                          text, count=1, flags=re.MULTILINE)
        if new_text != text:
            sa_path.write_text(new_text, encoding="utf-8")
            applied += 1
            print(f"  ✓ {sa}: → {recommended}", file=sys.stderr)
    return applied


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--eval-results", default=str(RESULTS_DIR),
                   help="dir or file of eval results (default: evals/subagents/results/)")
    p.add_argument("--min-pass-at-k", type=float, default=0.7,
                   help="pass@k threshold for 'good enough' (default 0.7)")
    p.add_argument("--cost-budget", type=float, default=None,
                   help="monthly USD budget cap (optional)")
    p.add_argument("--estimated-calls", type=int, default=1000,
                   help="estimated monthly calls per subagent (for budget calc)")
    p.add_argument("--apply", action="store_true",
                   help="write recommendations to subagent frontmatter (default: preview)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    eval_results = _load_results(Path(args.eval_results))
    if not eval_results:
        print(f"No eval results found at {args.eval_results}.", file=sys.stderr)
        print("Run scripts/eval/run_subagent_eval.py --all --apply first.",
              file=sys.stderr)
        return 1

    cost_matrix = ca.DEFAULT_COST_MATRIX
    suite_to_subagents = build_suite_to_subagents(SUITES_DIR)

    recommendations = {}
    for suite, suite_res in eval_results.items():
        by_model = suite_res.get("by_model", {})
        if not by_model:
            continue
        rec = ca.pareto_recommend(
            by_model, cost_matrix,
            min_pass_at_k=args.min_pass_at_k,
            monthly_budget_usd=args.cost_budget,
            estimated_calls=args.estimated_calls,
        )
        recommendations[suite] = rec
        if not args.json:
            print(f"\n{'='*60}")
            print(f"Suite: {suite}")
            print(ca.render_cost_preview(by_model, rec, cost_matrix))

    if args.json:
        # Serialize None as null; convert dataclass-like dicts as-is.
        print(json.dumps({"recommendations": recommendations},
                         indent=2, ensure_ascii=False, default=str))

    if args.apply:
        print("\n--apply: writing recommendations to frontmatter...",
              file=sys.stderr)
        total_applied = 0
        for suite, rec in recommendations.items():
            if rec is None:
                continue
            total_applied += _apply_to_frontmatter(
                suite, rec["recommended"], suite_to_subagents)
        print(f"\n{total_applied} file(s) updated.", file=sys.stderr)
    else:
        print("\n(preview only — re-run with --apply to write frontmatter)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
