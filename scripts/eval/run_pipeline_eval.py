#!/usr/bin/env python3
"""run_pipeline_eval.py — Q4 end-to-end pipeline eval.

Evaluates cross-subagent pipelines (e.g. finance: data-fetcher → analyst →
debater) by chaining delegate_to_model calls: each stage's output is injected
into the next stage's prompt via the {prev_output} placeholder. Only the
FINAL stage's required/forbidden keywords are judged (pipeline passes iff
the final output is correct, regardless of intermediate stage quality).

Reuses delegate_to_model + pass_at_k + judge from run_subagent_eval (DRY).

Pipeline suite JSON schema (new format with 'stages'):
  {
    "suite": "pipeline-finance",
    "description": "...",
    "stages": [
      {
        "subagent": "finance-data-fetcher",
        "prompt": "Get current data for {symbol}",
        "required": [],          # intermediate stages: not judged
        "forbidden": []
      },
      {
        "subagent": "finance-analyst",
        "prompt": "Analyze: {prev_output}",
        "required": [],
        "forbidden": []
      },
      {
        "subagent": "finance-debater",
        "prompt": "Challenge this thesis: {prev_output}",
        "required": ["verdict"],    # FINAL stage: judged
        "forbidden": ["i don't know"]
      }
    ],
    "model_overrides": {            # optional: per-stage model (else uses --models)
      "finance-data-fetcher": "deepseek-v4-flash",
      "finance-analyst": "deepseek-v4-pro",
      "finance-debater": "sonnet"
    },
    "cases": [                      # optional: multiple scenarios
      {"id": "aapl", "symbol": "AAPL"},
      {"id": "tsla", "symbol": "TSLA"}
    ]
  }

Usage:
  python scripts/eval/run_pipeline_eval.py --domain pipeline-finance --dry-run
  python scripts/eval/run_pipeline_eval.py --all --apply --k 2
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

SUITES_DIR = REPO_ROOT / "evals" / "subagents"
RESULTS_DIR = SUITES_DIR / "results"

# Reuse single-subagent eval primitives (DRY).
from run_subagent_eval import (  # noqa: E402
    delegate_to_model, judge, pass_at_k, DEFAULT_MODELS, DEFAULT_K,
)


# ---------------------------------------------------------------------------
# Suite loading
# ---------------------------------------------------------------------------

def load_suite(path: Path | str) -> dict | None:
    """Load a pipeline suite JSON. Returns None if missing or not a pipeline."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "suite" not in data or "stages" not in data:
            return None  # not a pipeline suite (might be a regular one)
        return data
    except Exception:
        return None


def discover_pipeline_suites() -> list[Path]:
    """All pipeline-*.json suite files under evals/subagents/."""
    if not SUITES_DIR.is_dir():
        return []
    return sorted(p for p in SUITES_DIR.glob("pipeline-*.json")
                  if p.parent.name != "results")


# ---------------------------------------------------------------------------
# Handoff contract validation
# ---------------------------------------------------------------------------

def validate_handcheck_contract(output: str, contract: dict) -> bool:
    """Alias for validate_handoff (kept for test compatibility)."""
    return validate_handoff(output, contract)


def validate_handoff(output: str, contract: dict) -> bool:
    """Check if output contains all required_fields from the handoff contract.

    Tries to parse output as JSON; if it parses, checks each required field
    is a key. If output is not JSON, returns False (when required_fields
    non-empty) — the contract expects structured output. Empty contract → True.
    """
    required = contract.get("required_fields", [])
    if not required:
        return True
    try:
        parsed = json.loads(output)
    except Exception:
        return False
    if not isinstance(parsed, dict):
        return False
    return all(f in parsed for f in required)


# ---------------------------------------------------------------------------
# Stage chaining + pipeline execution
# ---------------------------------------------------------------------------

def run_pipeline(
    suite: dict,
    models: list[str],
    k: int,
) -> dict[str, Any]:
    """Run one pipeline suite across all models × k samples.

    For each model × sample: chain stages (stage1 → stage2 → ... → stageN),
    injecting each output into the next prompt via {prev_output}. Judge only
    the FINAL stage. Pipeline pass = final stage output satisfies required/
    forbidden.

    Returns {suite, by_model: {model: {pass_at_k, total_samples, passed}},
             by_case: {case_id: [{pass, response_preview}]}}.
    """
    stages = suite["stages"]
    final_stage = stages[-1]
    cases = suite.get("cases", [{"id": "default"}])
    overrides = suite.get("model_overrides", {})
    suite_name = suite["suite"]

    out: dict[str, Any] = {"suite": suite_name, "by_model": {}, "by_case": {}}

    for model in models:
        model_results: list[dict] = []
        per_case: dict[str, list[dict]] = {}
        for case in cases:
            cid = case.get("id", "default")
            samples = []
            for _ in range(k):
                response = _chain_stages(stages, model, case, overrides)
                passed = judge(final_stage, response)
                samples.append({"pass": passed, "response_preview": response[:200]})
                model_results.append({"pass": passed})
            per_case[cid] = samples
        out["by_model"][model] = {
            "pass_at_k": pass_at_k(model_results, k),
            "total_samples": len(model_results),
            "passed": sum(1 for r in model_results if r["pass"]),
        }
        out["by_case"].update(per_case)
    return out


def _chain_stages(
    stages: list[dict],
    model: str,
    case: dict,
    overrides: dict[str, str],
) -> str:
    """Chain stages for one sample: feed each output into the next prompt.

    Variable substitution in prompts:
      {prev_output} → previous stage's output text
      {<case_field>} → value from the case dict (e.g. {symbol} → "AAPL")
    Model selection: override map (per-subagent) > default model arg.
    """
    prev_output = ""
    for stage in stages:
        prompt = stage["prompt"]
        # Substitute case variables first (e.g. {symbol}).
        for key, val in case.items():
            if key != "id":
                prompt = prompt.replace("{" + key + "}", str(val))
        # Substitute previous output.
        prompt = prompt.replace("{prev_output}", prev_output)
        # Pick model: override > default.
        subagent = stage.get("subagent", "")
        use_model = overrides.get(subagent, model)
        prev_output = delegate_to_model(use_model, prompt)
    return prev_output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--all", action="store_true",
                   help="run all pipeline-*.json suites")
    p.add_argument("--domain", help="run a specific pipeline suite (e.g. pipeline-finance)")
    p.add_argument("--models", default=",".join(DEFAULT_MODELS),
                   help=f"comma-separated candidate models (default: {','.join(DEFAULT_MODELS)})")
    p.add_argument("--k", type=int, default=DEFAULT_K, help=f"samples per case (default {DEFAULT_K})")
    p.add_argument("--dry-run", action="store_true",
                   help="print the plan only; make ZERO API calls (default)")
    p.add_argument("--apply", action="store_true",
                   help="run the pipeline eval for real (uses free-tier quota)")
    p.add_argument("--json", action="store_true", help="emit raw JSON output")
    args = p.parse_args()

    dry_run = not args.apply
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    if args.all:
        suite_paths = discover_pipeline_suites()
    elif args.domain:
        suite_paths = [SUITES_DIR / f"{args.domain}.json"]
    else:
        p.error("specify --all or --domain <name>")

    suite_paths = [sp for sp in suite_paths if sp.is_file()]
    if not suite_paths:
        print(f"No pipeline suites found in {SUITES_DIR}", file=sys.stderr)
        return 1

    # Build + print plan.
    total_stages = 0
    total_cases = 0
    plan_suites = []
    for sp in suite_paths:
        s = load_suite(sp)
        if s is None:
            continue
        n_stages = len(s["stages"])
        n_cases = len(s.get("cases", [{"id": "default"}]))
        plan_suites.append({"path": str(sp), "suite": s["suite"],
                            "stages": n_stages, "cases": n_cases})
        total_stages += n_stages
        total_cases += n_cases
    estimated = 0 if dry_run else total_cases * total_stages * len(models)

    if args.json:
        print(json.dumps({"suites": plan_suites, "total_stages": total_stages,
                          "total_cases": total_cases, "models": models, "k": args.k,
                          "dry_run": dry_run, "estimated_calls": estimated}, indent=2))
    else:
        print(f"🔗 Pipeline Eval — {'DRY-RUN (no API)' if dry_run else 'APPLY (real API)'}")
        print(f"   {total_cases} case(s) × {total_stages} stage(s) × {len(models)} model(s) × k={args.k}")
        print(f"   estimated API calls: {estimated} (stages × cases × models × k)")
        for s in plan_suites:
            print(f"   - {s['suite']}: {s['stages']} stage(s), {s['cases']} case(s)")

    if dry_run:
        print("\n(dry-run complete — re-run with --apply to hit the API)")
        return 0

    # Apply: run each suite.
    print("\nRunning pipeline eval...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_tag = time.strftime("%Y%m%d-%H%M%S")
    all_results = {}
    for sp in suite_paths:
        suite = load_suite(sp)
        if not suite:
            continue
        print(f"  [{suite['suite']}] {len(suite.get('cases', [{}]))} cases × "
              f"{len(suite['stages'])} stages × {len(models)} models...")
        res = run_pipeline(suite, models, args.k)
        all_results[suite["suite"]] = res
    out_file = RESULTS_DIR / f"pipeline-results-{date_tag}.json"
    out_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Results written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
