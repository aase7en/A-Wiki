#!/usr/bin/env python3
"""cost_aware_recommend.py — Q5 Pareto model recommendation.

Instead of always picking the HIGHEST pass@k model (which may be expensive),
this recommends the CHEAPEST model that meets a "good enough" pass@k threshold
(Pareto frontier: quality >= threshold, then minimize cost).

The COST_MATRIX is imported from scripts/hermes/model-pool/cost-router.py
(USD per 1M tokens: input/output/cached/free). Pure functions — no I/O,
no network — so trivially testable with a passed-in cost matrix.

Usage (via CLI wrapper apply_cost_aware_routing.py):
  python scripts/eval/apply_cost_aware_routing.py \\
      --eval-results evals/subagents/results/ \\
      --min-pass-at-k 0.7
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

# Default cost matrix — imported from cost-router.py at runtime (avoids hard
# coupling for tests, which pass their own matrix). Falls back to empty if
# import fails (e.g. in CI without the hermes module path).
def _load_default_cost_matrix() -> dict[str, dict[str, Any]]:
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes" / "model-pool"))
        from cost_router import COST_MATRIX  # type: ignore
        return COST_MATRIX
    except Exception:
        return {}


DEFAULT_COST_MATRIX = _load_default_cost_matrix()

# Default token estimates for cost calculation (tunable).
DEFAULT_AVG_INPUT_TOKENS = 500
DEFAULT_AVG_OUTPUT_TOKENS = 200


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------

def cost_per_1k_calls(
    model: str,
    cost_matrix: dict[str, dict[str, Any]],
    avg_input_tokens: int = DEFAULT_AVG_INPUT_TOKENS,
    avg_output_tokens: int = DEFAULT_AVG_OUTPUT_TOKENS,
) -> float | None:
    """Estimate USD cost for 1000 calls at average token usage.

    Formula: 1000 × (input_per_1M × avg_in/1M + output_per_1M × avg_out/1M).
    Returns None if the model is not in the cost matrix.
    """
    entry = cost_matrix.get(model)
    if entry is None:
        # Try matching by suffix (cost-router uses provider-qualified ids like
        # "deepseek/deepseek-v4-flash"; eval suites use "deepseek-v4-flash").
        for key, val in cost_matrix.items():
            if key.endswith(model) or model in key:
                entry = val
                break
    if entry is None:
        return None
    input_rate = float(entry.get("input", 0))
    output_rate = float(entry.get("output", 0))
    cost = 1000 * (
        input_rate * avg_input_tokens / 1_000_000 +
        output_rate * avg_output_tokens / 1_000_000
    )
    return round(cost, 6)


# ---------------------------------------------------------------------------
# Pareto recommendation
# ---------------------------------------------------------------------------

def pareto_recommend(
    eval_by_model: dict[str, dict[str, Any]],
    cost_matrix: dict[str, dict[str, Any]],
    min_pass_at_k: float = 0.7,
    monthly_budget_usd: float | None = None,
    estimated_calls: int = 1000,
) -> dict[str, Any] | None:
    """Recommend the cheapest model with pass@k >= min_pass_at_k.

    Pareto frontier logic:
      1. Filter models to those with pass_at_k >= min_pass_at_k ("good enough").
      2. If monthly_budget_usd set, exclude models whose cost_per_1k_calls ×
         (estimated_calls / 1000) exceeds the budget.
      3. Among remaining, pick the one with lowest cost_per_1k_calls.
      4. Tie-break by pass@k (higher wins), then by name.

    Returns None if no model meets the threshold. Otherwise:
      {recommended, pass_at_k, cost_per_1k_calls, reason, excluded: [...]}
    """
    # Step 1: filter by pass@k threshold.
    candidates = []
    excluded = []
    for model, mr in eval_by_model.items():
        rate = float(mr.get("pass_at_k", 0.0))
        if rate < min_pass_at_k:
            excluded.append({"model": model, "pass_at_k": rate,
                             "reason": "below-threshold"})
            continue
        cost = cost_per_1k_calls(model, cost_matrix)
        # Step 2: budget filter.
        if monthly_budget_usd is not None and cost is not None:
            monthly_cost = cost * (estimated_calls / 1000)
            if monthly_cost > monthly_budget_usd:
                excluded.append({"model": model, "pass_at_k": rate,
                                 "cost_per_1k_calls": cost,
                                 "reason": "over-budget"})
                continue
        candidates.append({"model": model, "pass_at_k": rate,
                           "cost_per_1k_calls": cost})

    if not candidates:
        return None

    # Step 3: pick cheapest (None cost = unknown → treat as infinity so known
    # costs win; free models (0.0) win over paid).
    def sort_key(c):
        cost = c["cost_per_1k_calls"]
        # Unknown cost → push to end; otherwise sort ascending.
        return (1, 0) if cost is None else (0, cost)
    candidates.sort(key=lambda c: (sort_key(c), -c["pass_at_k"], c["model"]))

    best = candidates[0]
    return {
        "recommended": best["model"],
        "pass_at_k": best["pass_at_k"],
        "cost_per_1k_calls": best["cost_per_1k_calls"],
        "reason": "cheapest-above-threshold",
        "excluded": excluded,
        "candidates": candidates,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_cost_preview(
    eval_by_model: dict[str, dict[str, Any]],
    recommendation: dict[str, Any] | None,
    cost_matrix: dict[str, dict[str, Any]],
) -> str:
    """Human-readable preview of all candidates + the Pareto pick."""
    if not eval_by_model:
        return "No eval results to analyze."

    lines = ["Cost-Aware Model Recommendation (Pareto frontier):", ""]
    lines.append(f"{'model':<28} {'pass@k':>7} {'$/1k':>8} {'status'}")
    lines.append("-" * 70)

    recommended = recommendation["recommended"] if recommendation else None
    excluded_models = {e["model"] for e in (recommendation or {}).get("excluded", [])}

    for model in sorted(eval_by_model.keys()):
        rate = eval_by_model[model].get("pass_at_k", 0.0)
        cost = cost_per_1k_calls(model, cost_matrix)
        cost_str = f"${cost:.4f}" if cost is not None else "?"
        if model == recommended:
            status = "★ recommended"
        elif model in excluded_models:
            status = "✗ excluded"
        else:
            status = ""
        lines.append(f"{model:<28} {rate:>6.2f} {cost_str:>8} {status}")

    lines.append("")
    if recommendation:
        r = recommendation
        lines.append(f"→ Recommended: {r['recommended']} "
                     f"(pass@k={r['pass_at_k']:.2f}, "
                     f"${r['cost_per_1k_calls'] or 0:.4f}/1k calls)")
        if r.get("excluded"):
            lines.append(f"  Excluded: {len(r['excluded'])} model(s) "
                         f"(below threshold or over budget)")
    else:
        lines.append("→ No model meets the pass@k threshold. "
                     "Lower --min-pass-at-k or improve eval results.")
    return "\n".join(lines)


__all__ = ["cost_per_1k_calls", "pareto_recommend", "render_cost_preview",
           "DEFAULT_COST_MATRIX"]
