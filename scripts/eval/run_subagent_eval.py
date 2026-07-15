#!/usr/bin/env python3
"""
run_subagent_eval.py — Subagent Eval Harness runner.

Runs eval suites (evals/subagents/<domain>.json) against candidate models
to produce data-driven model selection for the 28 specialized subagents.
The suites are simple required/forbidden keyword checks on the model's
response — no heavy LLM-as-judge (keeps it deterministic + cheap).

Usage:
  # Dry-run: print the plan, make ZERO API calls (default, safe)
  python scripts/eval/run_subagent_eval.py --all --dry-run
  python scripts/eval/run_subagent_eval.py --domain medical --dry-run

  # Real run: route each prompt through delegate.sh (free tier), compute pass@k
  python scripts/eval/run_subagent_eval.py --all --apply
  python scripts/eval/run_subagent_eval.py --domain medical --models deepseek-v4-flash,glm-5.2 --apply

  # Then apply the winning model back to the subagent frontmatters:
  python scripts/eval/apply_eval_results.py --results evals/subagents/results/

Eval suite schema (JSON, mirrors evals/awiki/ convention):
  {
    "suite": "<domain>",
    "description": "...",
    "cases": [
      {
        "id": "<case-id>",
        "subagent": "<subagent-name>",
        "prompt": "<the task prompt>",
        "required": ["keyword", ...],   # response must contain all (case-insensitive)
        "forbidden": ["keyword", ...]    # response must contain none
      }
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
RESULTS_DIR = SUITES_DIR / "results"
DEFAULT_MODELS = ["deepseek-v4-flash", "deepseek-v4-pro", "glm-5.2"]
DEFAULT_K = 3


# ---------------------------------------------------------------------------
# Suite loading
# ---------------------------------------------------------------------------
def load_suite(path: Path | str) -> dict | None:
    """Load + parse a JSON eval suite. Returns None if missing/invalid."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "suite" not in data or "cases" not in data:
            return None
        return data
    except Exception:
        return None


def discover_suites() -> list[Path]:
    """All *.json suite files under evals/subagents/ (excluding results/)."""
    if not SUITES_DIR.is_dir():
        return []
    return sorted(
        p for p in SUITES_DIR.glob("*.json")
        if p.parent.name != "results"
    )


# ---------------------------------------------------------------------------
# Case judging — required/forbidden keyword matching (case-insensitive)
# ---------------------------------------------------------------------------
def judge(case: dict, response: str) -> bool:
    """True if response satisfies the case's required + forbidden keywords."""
    r = (response or "").lower()
    for req in case.get("required", []):
        if str(req).lower() not in r:
            return False
    for forb in case.get("forbidden", []):
        if str(forb).lower() in r:
            return False
    return True


# ---------------------------------------------------------------------------
# pass@k
# ---------------------------------------------------------------------------
def pass_at_k(results: list[dict], k: int) -> float:
    """pass@k = 1 - C(n-c, k) / C(n, k), where c = #pass, n = total.

    Standard pass@k from the "Evaluating Large Language Models Trained on Code"
    paper. With n total samples and c passing, the probability that at least
    one of k samples passes (assuming uniform random sampling).
    """
    n = len(results)
    if n == 0 or k == 0:
        return 0.0
    c = sum(1 for r in results if r.get("pass"))
    if n - c < k:
        return 1.0  # not enough fails to fill k samples → at least one must pass
    # 1 - prod_{i=0}^{k-1} (n-c-i)/(n-i)
    num = denom = 1.0
    for i in range(k):
        num *= (n - c - i)
        denom *= (n - i)
    return 1.0 - (num / denom) if denom else 0.0


# ---------------------------------------------------------------------------
# Model alias resolution — maps eval-suite shorthand to provider-qualified ids
# ---------------------------------------------------------------------------
# delegate.sh's AWIKI_FORCE_MODEL override must receive a provider-qualified
# model id (e.g. "deepseek/deepseek-chat-v3-0324:free") OR a custom:<uuid>:<id>
# triple — NOT a bare ZCode alias like "sonnet", because delegate.sh's tier
# machinery and provider_registry.py do not understand ZCode's alias table.
#
# Eval suites use shorthand ids that match the `model:` field values in
# agents/subagents/*.md frontmatter (e.g. "deepseek-v4-flash", "glm-5.2").
# This map expands those to the OpenRouter-qualified form delegate.sh expects.
MODEL_ALIAS_MAP = {
    # ZCode tier aliases → Anthropic via OpenRouter
    "sonnet": "anthropic/claude-sonnet-4",
    "opus": "anthropic/claude-opus-4.1",
    "haiku": "anthropic/claude-haiku-4.5",
    # DeepSeek (free tier on OpenRouter; matches delegate.sh TIER seeds)
    "deepseek-v4-flash": "deepseek/deepseek-chat-v3-0324:free",
    "deepseek-v4-pro": "deepseek/deepseek-r1:free",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
    # GLM via Z.ai
    "glm-5.2": "zai/glm-5.2",
    "glm-4.6": "zai/glm-4.6",
    # Gemini free tier
    "gemini-flash": "google/gemini-2.5-flash:free",
}


def resolve_model_for_eval(model: str) -> str:
    """Expand an eval-suite model shorthand to a provider-qualified id.

    Rules (in order):
      1. custom:<uuid>:<id> triples pass through unchanged (ZCode agent format).
      2. ids already containing '/' (provider-qualified) pass through unchanged.
      3. otherwise look up the shorthand in MODEL_ALIAS_MAP.
      4. unknown shorthands pass through verbatim (let delegate.sh reject it,
         so the user sees a clear error rather than eval silently testing the
         wrong model).
    Pure function — never makes an API call.
    """
    if not model:
        return model
    if model.startswith("custom:") or "/" in model:
        return model
    return MODEL_ALIAS_MAP.get(model, model)


# ---------------------------------------------------------------------------
# Model delegation (real path routes through delegate.sh; tests monkeypatch this)
# ---------------------------------------------------------------------------
def delegate_to_model(model: str, prompt: str) -> str:
    """Route a prompt to a model via scripts/swarm/delegate.sh.

    Returns the model's text response. Best-effort: on failure returns "".
    This is the ONE API-touching function; tests monkeypatch it.

    Implementation note (P1 fix): delegate.sh does NOT parse a --model flag —
    its declared interface is `<task_type> <prompt>` (positional). We pass the
    target model via the AWIKI_FORCE_MODEL env override (added to delegate.sh
    in the same P1 change) and use the "reason" task_type so delegate.sh picks
    tier 2 (DeepSeek / Anthropic low tier). The env override short-circuits
    the tier selection entirely, routing direct to the forced model.
    """
    import os
    import subprocess
    try:
        full_model = resolve_model_for_eval(model)
        env = {**os.environ, "AWIKI_FORCE_MODEL": full_model}
        proc = subprocess.run(
            ["bash", str(REPO_ROOT / "scripts" / "swarm" / "delegate.sh"),
             "reason", prompt],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
            env=env,
        )
        return proc.stdout or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Plan building (no API calls — pure)
# ---------------------------------------------------------------------------
def build_plan(
    suite_paths: list[Path],
    models: list[str],
    k: int,
    dry_run: bool,
) -> dict[str, Any]:
    """Build an eval plan: which suites, how many cases, estimated API calls.

    Pure function — never touches the network. estimated_calls is 0 in dry-run.
    """
    suites = []
    total_cases = 0
    for p in suite_paths:
        s = load_suite(p)
        if s is None:
            continue
        suites.append({"path": str(p), "suite": s["suite"], "cases": len(s["cases"])})
        total_cases += len(s["cases"])
    estimated = 0 if dry_run else total_cases * len(models) * k
    return {
        "suites": suites,
        "total_cases": total_cases,
        "models": models,
        "k": k,
        "dry_run": dry_run,
        "estimated_calls": estimated,
    }


# ---------------------------------------------------------------------------
# Execution (apply mode only)
# ---------------------------------------------------------------------------
def run_suite(
    suite: dict,
    models: list[str],
    k: int,
) -> dict[str, Any]:
    """Run one suite across all models × cases × k samples. Returns results."""
    suite_name = suite["suite"]
    out: dict[str, Any] = {"suite": suite_name, "by_model": {}, "by_case": {}}
    for model in models:
        model_results: list[dict] = []
        per_case: dict[str, list[dict]] = {}
        for case in suite["cases"]:
            cid = case["id"]
            samples = []
            for _ in range(k):
                resp = delegate_to_model(model, case["prompt"])
                passed = judge(case, resp)
                samples.append({"pass": passed, "response_preview": resp[:200]})
                model_results.append({"pass": passed})
            per_case[cid] = samples
        out["by_model"][model] = {
            "pass_at_k": pass_at_k(model_results, k),
            "total_samples": len(model_results),
            "passed": sum(1 for r in model_results if r["pass"]),
        }
        out["by_case"].update(per_case)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--all", action="store_true", help="run all suites in evals/subagents/")
    p.add_argument("--domain", help="run a specific domain suite (e.g. medical)")
    p.add_argument("--models", default=",".join(DEFAULT_MODELS),
                   help=f"comma-separated candidate models (default: {','.join(DEFAULT_MODELS)})")
    p.add_argument("--k", type=int, default=DEFAULT_K, help=f"samples per case (default {DEFAULT_K})")
    p.add_argument("--dry-run", action="store_true",
                   help="print the plan only; make ZERO API calls (default if neither --apply given)")
    p.add_argument("--apply", action="store_true",
                   help="run the eval for real (routes through delegate.sh — uses free-tier quota)")
    p.add_argument("--json", action="store_true", help="emit raw JSON output")
    args = p.parse_args()

    dry_run = not args.apply  # dry-run is the default (safe)
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    # Resolve suite paths.
    if args.all:
        suite_paths = discover_suites()
    elif args.domain:
        suite_paths = [SUITES_DIR / f"{args.domain}.json"]
    else:
        p.error("specify --all or --domain <name>")

    suite_paths = [sp for sp in suite_paths if sp.is_file()]
    if not suite_paths:
        print(f"No eval suites found in {SUITES_DIR}", file=sys.stderr)
        if args.domain:
            print(f"  (looked for {SUITES_DIR / (args.domain + '.json')})", file=sys.stderr)
        return 1

    plan = build_plan(suite_paths, models, args.k, dry_run)

    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print(f"🔬 Subagent Eval — {'DRY-RUN (no API)' if dry_run else 'APPLY (real API)'}")
        print(f"   {plan['total_cases']} case(s) × {len(models)} model(s) × k={args.k}")
        print(f"   estimated API calls: {plan['estimated_calls']}")
        for s in plan["suites"]:
            print(f"   - {s['suite']}: {s['cases']} case(s)")

    if dry_run:
        print("\n(dry-run complete — re-run with --apply to hit the API)")
        return 0

    # Apply mode: run each suite, write results.
    print("\nRunning eval...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_tag = time.strftime("%Y%m%d-%H%M%S")
    all_results = {}
    for sp in suite_paths:
        suite = load_suite(sp)
        if not suite:
            continue
        print(f"  [{suite['suite']}] {len(suite['cases'])} cases × {len(models)} models...")
        res = run_suite(suite, models, args.k)
        all_results[suite["suite"]] = res
    out_file = RESULTS_DIR / f"results-{date_tag}.json"
    out_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Results written to {out_file}")
    print("   Next: python scripts/eval/apply_eval_results.py --results " + str(out_file.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
