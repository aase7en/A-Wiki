#!/usr/bin/env python3
"""
cost_optimizer.py — Cost optimization recommender (T6).

วิเคราะห์ cost history (S6) + eval pass@k → recommend model ที่
"ดีพอ (pass@k ≥ threshold) + ถูกสุด" → คำนวณ savings เทียบ current model.

ผสม 3 modules:
  - cost_history.estimate_model_cost() — USD per model
  - pareto logic จาก cost_aware_recommend — cheapest above threshold
  - ab_routing.flip_subagent_model() — write frontmatter

Reuses pattern จาก adaptive_routing (guardrails: min_savings, never_downgrade).

Usage:
  python scripts/eval/cost_optimizer.py --analyze              # ดู recommendations
  python scripts/eval/cost_optimizer.py --apply --min-savings 0.5  # apply changes
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Reuse ab_routing.flip_subagent_model for frontmatter editing
import ab_routing  # noqa: E402


def analyze_suite(
    suite_name: str,
    eval_by_model: dict[str, dict[str, Any]],
    cost_by_model: dict[str, float],
    current_model: str,
    min_pass_at_k: float = 0.7,
    min_savings: float = 0.0,
) -> dict[str, Any] | None:
    """Analyze one suite — find cheapest "good enough" model + compute savings.

    Args:
      suite_name: suite name (e.g. "medical").
      eval_by_model: {model: {pass_at_k: float}} from eval results.
      cost_by_model: {model: usd_per_1k_calls} from cost_history.
      current_model: the suite's current default model.
      min_pass_at_k: minimum pass@k to be "good enough" (default 0.7).
      min_savings: minimum USD savings to recommend a swap (default 0 = any).

    Returns: recommendation dict or None ถ้า no model meets threshold.
      {suite, current_model, current_cost, recommended_model, recommended_cost,
       savings_usd, savings_pct, status, reason}
    """
    # Step 1: filter by pass@k threshold
    candidates = []
    for model, mr in eval_by_model.items():
        rate = float(mr.get("pass_at_k", 0.0))
        if rate >= min_pass_at_k:
            cost = cost_by_model.get(model, 0.0)
            candidates.append({"model": model, "pass_at_k": rate, "cost": cost})

    if not candidates:
        return None

    # Step 2: pick cheapest
    candidates.sort(key=lambda c: (c["cost"], -c["pass_at_k"]))
    best = candidates[0]

    current_cost = cost_by_model.get(current_model, 0.0)
    savings_usd = round(current_cost - best["cost"], 6)
    savings_pct = round(savings_usd / current_cost, 4) if current_cost > 0 else 0.0

    # Step 3: guardrail — skip if savings too small
    if savings_usd < min_savings:
        return {
            "suite": suite_name,
            "current_model": current_model,
            "current_cost": current_cost,
            "recommended_model": current_model,  # no change
            "recommended_cost": current_cost,
            "savings_usd": 0.0,
            "savings_pct": 0.0,
            "status": "no-action",
            "reason": f"savings {savings_usd} < min_savings {min_savings}",
        }

    status = "recommend" if best["model"] != current_model else "current-best"
    reason = (f"cheapest good-enough model (pass@k={best['pass_at_k']:.2f} ≥ {min_pass_at_k}, "
              f"cost=${best['cost']:.4f} vs current ${current_cost:.4f})")

    return {
        "suite": suite_name,
        "current_model": current_model,
        "current_cost": current_cost,
        "recommended_model": best["model"],
        "recommended_cost": best["cost"],
        "savings_usd": savings_usd,
        "savings_pct": savings_pct,
        "status": status,
        "reason": reason,
    }


def apply_recommendations(
    recs: list[dict[str, Any]],
    agents_dir: Path | str,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    """Apply cost optimization recommendations by writing frontmatter.

    Only applies recs with status=="recommend". Returns list of applied actions.

    Args:
      recs: list from analyze_suite().
      agents_dir: directory containing subagent .md files.
      dry_run: if True, don't write — just report what would change.
    """
    agents_dir = Path(agents_dir)
    applied = []
    for rec in recs:
        if rec.get("status") != "recommend":
            continue
        subagent = rec.get("subagent") or rec.get("suite", "")
        sa_path = agents_dir / "subagents" / f"{subagent}.md"
        if not sa_path.is_file():
            sa_path = agents_dir / f"{subagent}.md"
        if not sa_path.is_file():
            applied.append({**rec, "applied": False, "error": "subagent .md not found"})
            continue
        if dry_run:
            applied.append({**rec, "applied": False, "would_write": str(sa_path)})
            continue
        changed = ab_routing.flip_subagent_model(sa_path, rec["recommended_model"])
        applied.append({**rec, "applied": changed, "path": str(sa_path)})
    return applied


def render_optimizer_report(recs: list[dict[str, Any]]) -> str:
    """Render recommendations as a compact text table."""
    if not recs:
        return "(no recommendations — ยังไม่มี cost data หรือทุก model ดีพอแล้ว)"
    lines = ["💡 Cost Optimization Recommendations", ""]
    header = f"{'suite':<18} {'current':<18} {'recommended':<18} {'save $':>8} {'save %':>7} {'status'}"
    lines.append(header)
    lines.append("-" * len(header))
    for rec in recs:
        lines.append(
            f"{rec.get('suite','?'):<18} "
            f"{rec.get('current_model','?'):<18} "
            f"{rec.get('recommended_model','?'):<18} "
            f"{rec.get('savings_usd',0):>8.4f} "
            f"{rec.get('savings_pct',0)*100:>6.1f}% "
            f"{rec.get('status','?')}"
        )
    return "\n".join(lines)


__all__ = ["analyze_suite", "apply_recommendations", "render_optimizer_report"]
