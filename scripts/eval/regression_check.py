"""Subagent eval regression detection (P3).

Compares two eval results files (baseline vs new) produced by
run_subagent_eval.py and flags any (suite, model) pair whose pass@k
dropped by more than a configurable threshold. Used by the weekly CI
workflow (.github/workflows/subagent-eval.yml) to detect quality
regressions before they ship to production subagent frontmatter.

Pure functions — no I/O, no clock — so trivially testable.

Results dict shape (from run_subagent_eval.py):
  {suite: {by_model: {model: {pass_at_k, total_samples, passed}}, by_case: {}}}
"""
from __future__ import annotations

from typing import Any

DEFAULT_THRESHOLD = 0.10  # flag when pass@k drops by more than 10 points

# Severity ranking for sorting (worst first).
_SEVERITY_ORDER = {"regression": 0, "removed": 1, "improvement": 2, "flat": 3}


def detect_regression(
    baseline: dict[str, Any],
    new: dict[str, Any],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Compare baseline vs new eval results; flag pass@k regressions.

    For each (suite, model) pair present in BOTH baseline and new:
      - delta = new_pass_at_k - baseline_pass_at_k
      - severity = "regression" if delta < -threshold
                   "improvement" if delta > threshold
                   "flat" otherwise
    Pairs only in baseline → "removed" (model dropped from results).
    Pairs only in new → "flat" with baseline_pass_at_k=0 (first run).

    Returns a list of dicts sorted worst-first:
      [{suite, model, baseline_pass_at_k, new_pass_at_k, delta, severity}, ...]
    """
    out: list[dict[str, Any]] = []

    baseline_pairs = _flatten(baseline)
    new_pairs = _flatten(new)
    new_keys = set(new_pairs.keys())

    # Pairs in both → regression / improvement / flat
    for (suite, model), base_rate in baseline_pairs.items():
        if (suite, model) in new_keys:
            new_rate = new_pairs[(suite, model)]
            delta = round(new_rate - base_rate, 6)
            if delta < -threshold:
                severity = "regression"
            elif delta > threshold:
                severity = "improvement"
            else:
                severity = "flat"
            out.append({
                "suite": suite, "model": model,
                "baseline_pass_at_k": base_rate,
                "new_pass_at_k": new_rate,
                "delta": delta, "severity": severity,
            })
        else:
            # In baseline but not new → removed.
            out.append({
                "suite": suite, "model": model,
                "baseline_pass_at_k": base_rate,
                "new_pass_at_k": 0.0,
                "delta": -base_rate, "severity": "removed",
            })

    # Pairs only in new → first run, no baseline (flat with baseline=0).
    for (suite, model), new_rate in new_pairs.items():
        if (suite, model) not in baseline_pairs:
            out.append({
                "suite": suite, "model": model,
                "baseline_pass_at_k": 0.0,
                "new_pass_at_k": new_rate,
                "delta": new_rate, "severity": "flat",
            })

    out.sort(key=lambda r: (_SEVERITY_ORDER.get(r["severity"], 9),
                            r["delta"], r["suite"], r["model"]))
    return out


def _flatten(results: dict[str, Any]) -> dict[tuple[str, str], float]:
    """Flatten {suite: {by_model: {model: {pass_at_k}}}} → {(suite, model): rate}."""
    flat: dict[tuple[str, str], float] = {}
    for suite, suite_res in (results or {}).items():
        by_model = (suite_res or {}).get("by_model", {}) or {}
        for model, mr in by_model.items():
            rate = float((mr or {}).get("pass_at_k", 0.0))
            flat[(suite, model)] = rate
    return flat


def render_regression_report(rows: list[dict[str, Any]]) -> str:
    """Render a markdown report for a GitHub issue body.

    Lists regressions first (with deltas), then removed, then a summary line.
    Returns a short "all green" message when there are no regressions or
    removals.
    """
    regressions = [r for r in rows if r["severity"] == "regression"]
    removed = [r for r in rows if r["severity"] == "removed"]
    improvements = [r for r in rows if r["severity"] == "improvement"]
    flat = [r for r in rows if r["severity"] == "flat"]

    if not regressions and not removed:
        summary = (f"✅ No regressions detected "
                   f"({len(improvements)} improvement(s), {len(flat)} stable).")
        if not improvements:
            return f"## Subagent Eval — All Green\n\n{summary}\n"
        return f"## Subagent Eval — All Green\n\n{summary}\n"

    lines = ["## 🚨 Subagent Eval Regression Report", ""]
    lines.append(
        f"**Summary:** {len(regressions)} regression(s) · "
        f"{len(removed)} removed · {len(improvements)} improvement(s) · "
        f"{len(flat)} stable"
    )
    lines.append("")

    if regressions:
        lines.append("### 📉 Regressions (pass@k dropped > threshold)")
        lines.append("")
        lines.append("| Suite | Model | Baseline | New | Δ |")
        lines.append("|-------|-------|----------|-----|---|")
        for r in regressions:
            lines.append(
                f"| {r['suite']} | `{r['model']}` | "
                f"{r['baseline_pass_at_k']:.2f} | {r['new_pass_at_k']:.2f} | "
                f"**{r['delta']:+.2f}** |"
            )
        lines.append("")

    if removed:
        lines.append("### ❓ Removed (in baseline, absent from new run)")
        lines.append("")
        for r in removed:
            lines.append(f"- `{r['suite']}/{r['model']}` "
                         f"(was {r['baseline_pass_at_k']:.2f})")
        lines.append("")

    if improvements:
        lines.append("### 📈 Improvements")
        lines.append("")
        for r in improvements:
            lines.append(f"- `{r['suite']}/{r['model']}` "
                         f"{r['baseline_pass_at_k']:.2f} → {r['new_pass_at_k']:.2f} "
                         f"({r['delta']:+.2f})")
        lines.append("")

    lines.append("---")
    lines.append("_Threshold: pass@k drop > 0.10 flagged as regression._")
    return "\n".join(lines)


__all__ = ["detect_regression", "render_regression_report", "DEFAULT_THRESHOLD"]
