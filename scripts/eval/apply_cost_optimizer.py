#!/usr/bin/env python3
"""
apply_cost_optimizer.py — CLI สำหรับ cost optimization (T6).

อ่าน eval results + cost history → recommend model swaps → optionally apply.

Usage:
  python scripts/eval/apply_cost_optimizer.py --analyze          # ดู recommendations (dry-run)
  python scripts/eval/apply_cost_optimizer.py --apply --min-savings 0.5
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = REPO_ROOT / "agents"

import cost_optimizer  # noqa: E402
import cost_aware_recommend  # noqa: E402  -- for cost_per_1k_calls


def _load_latest_results(results_dir: Path) -> dict:
    """Load the most recent results-*.json file."""
    files = sorted(glob.glob(str(results_dir / "results-*.json")))
    if not files:
        return {}
    return json.loads(Path(files[-1]).read_text(encoding="utf-8"))


def _suite_to_subagent(results: dict) -> dict[str, str]:
    """Map suite name → subagent name (from eval suite files)."""
    suites_dir = REPO_ROOT / "evals" / "subagents"
    mapping = {}
    for path in suites_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if "cases" in data and data["cases"]:
                mapping[data.get("suite", path.stem)] = data["cases"][0].get("subagent", "")
        except Exception:
            continue
    return mapping


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--analyze", action="store_true", help="show recommendations (dry-run, default)")
    g.add_argument("--apply", action="store_true", help="apply recommendations (write frontmatter)")
    p.add_argument("--min-pass-at-k", type=float, default=0.7)
    p.add_argument("--min-savings", type=float, default=0.0, help="minimum USD savings to recommend")
    p.add_argument("--results-dir", default=str(REPO_ROOT / "evals" / "subagents" / "results"))
    args = p.parse_args()

    results = _load_latest_results(Path(args.results_dir))
    if not results:
        print("❌ ยังไม่มี eval results — รัน CI eval ก่อน")
        return 1

    cost_matrix = cost_aware_recommend._load_default_cost_matrix()
    suite_to_sub = _suite_to_subagent(results)

    recs = []
    for suite_name, suite_data in results.items():
        if not isinstance(suite_data, dict):
            continue
        by_model = suite_data.get("by_model", {})
        if not by_model:
            continue
        # Build cost_by_model from COST_MATRIX (via alias map)
        cost_by_model = {}
        for model in by_model:
            cost_by_model[model] = cost_aware_recommend.cost_per_1k_calls(model, cost_matrix) or 0.0
        # Current model = first in by_model (or lookup subagent frontmatter)
        current = list(by_model.keys())[0] if by_model else ""
        rec = cost_optimizer.analyze_suite(
            suite_name, by_model, cost_by_model, current,
            min_pass_at_k=args.min_pass_at_k, min_savings=args.min_savings,
        )
        if rec:
            rec["subagent"] = suite_to_sub.get(suite_name, "")
            recs.append(rec)

    print(cost_optimizer.render_optimizer_report(recs))

    if args.apply and recs:
        print("\nApplying recommendations...")
        applied = cost_optimizer.apply_recommendations(recs, AGENTS_DIR, dry_run=False)
        # U2: append audit trail to cost-optimization-log.jsonl (เหมือน adaptive-routing-log)
        import time as _time
        log_path = REPO_ROOT / ".tmp" / "cost-optimization-log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        for a in applied:
            status = "✓" if a.get("applied") else "⚠️"
            print(f"  {status} {a.get('suite')}: {a.get('current_model')} → {a.get('recommended_model')}")
            if a.get("applied"):
                entry = {
                    "ts": round(_time.time(), 3),
                    "suite": a.get("suite"),
                    "subagent": a.get("subagent"),
                    "from": a.get("current_model"),
                    "to": a.get("recommended_model"),
                    "savings_usd": a.get("savings_usd"),
                    "savings_pct": a.get("savings_pct"),
                    "reason": a.get("reason"),
                }
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(json.dumps(entry) + "\n")
    elif args.analyze:
        print(f"\n(dry-run — {len([r for r in recs if r.get('status')=='recommend'])} would apply)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
