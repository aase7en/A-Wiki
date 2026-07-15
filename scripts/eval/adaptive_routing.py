"""Adaptive model routing (P4) — data-driven subagent model swap.

Closes the feedback loop: observatory data (pass_rate per subagent) +
eval results (pass@k per model) → recommend model swaps with safety
guardrails:

  - min_samples:    ignore subagents with fewer observatory invocations
                    (statistically meaningless; would be noise).
  - min_delta:      recommend only when the candidate's eval pass@k
                    exceeds the current model's by at least this margin
                    (avoids churn for marginal wins).
  - never_downgrade: never recommend a model whose pass@k is LOWER than
                    the current model's observed pass_rate.
  - flap_window_days: if recent swap history (within this many days) shows
                    the subagent oscillated to the candidate model and back,
                    mark 'hold-flapping' instead of 'recommend' (prevents
                    endless back-and-forth).

All functions are pure (no I/O, no clock) except apply_changes which writes
files. The CLI wrapper (apply_adaptive_routing.py) loads the inputs and
calls these.

Stats dict shape (from subagent_stats.aggregate):
  {by_subagent: {name: {count, pass_rate, best_model, ...}}}
Eval results shape (from run_subagent_eval):
  {suite: {by_model: {model: {pass_at_k, ...}}, by_case: {}}}
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "min_samples": 10,        # need >= this many observatory invocations
    "min_delta": 0.15,        # candidate must beat current by >= this much
    "never_downgrade": True,  # never recommend a worse model
    "flap_window_days": 7,    # swap history lookback for flap detection
}

DAY_SECONDS = 86400


def recommend_model_changes(
    stats: dict[str, Any],
    eval_results: dict[str, Any],
    current_models: dict[str, str],
    suite_to_subagents: dict[str, list[str]],
    config: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    now: float | None = None,
) -> list[dict[str, Any]]:
    """Recommend model swaps for subagents whose data supports a change.

    Args:
      stats: observatory stats (by_subagent: {name: {count, pass_rate, ...}}).
      eval_results: {suite: {by_model: {model: {pass_at_k}}}}.
      current_models: {subagent_name: current_model_id}.
      suite_to_subagents: {suite: [subagent names covered]}.
      config: override DEFAULT_CONFIG keys.
      history: optional list of past swaps
               [{subagent, from, to, ts}] for flap detection.
      now: override current time for deterministic tests.

    Returns:
      List of recommendation dicts sorted recommend-first:
        [{
          "subagent", "current", "recommended",
          "current_pass_rate", "new_pass_rate", "delta", "samples",
          "status": "recommend"|"hold-flapping"|"insufficient-data"|"hold-current-better"|"hold-no-winner",
        }, ...]
      One entry per subagent in suite_to_subagents that has observatory data.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    min_samples = int(cfg["min_samples"])
    min_delta = float(cfg["min_delta"])
    flap_window = int(cfg["flap_window_days"]) * DAY_SECONDS
    now_ts = now if now is not None else time.time()

    by_subagent = stats.get("by_subagent", {}) or {}
    out: list[dict[str, Any]] = []

    # Build suite → best eval model (highest pass@k).
    suite_best: dict[str, tuple[str, float]] = {}
    for suite, suite_res in eval_results.items():
        by_model = (suite_res or {}).get("by_model", {}) or {}
        best_model = None
        best_rate = -1.0
        for m, mr in by_model.items():
            rate = float((mr or {}).get("pass_at_k", 0.0))
            if rate > best_rate or (rate == best_rate and best_model is None):
                best_rate = rate
                best_model = m
        if best_model is not None:
            suite_best[suite] = (best_model, best_rate)

    for suite, subagents in suite_to_subagents.items():
        best = suite_best.get(suite)
        for sa in subagents:
            current = current_models.get(sa)
            if current is None:
                continue  # unknown subagent — cannot recommend
            sa_stat = by_subagent.get(sa, {})
            samples = int(sa_stat.get("count", 0))
            current_pr = float(sa_stat.get("pass_rate", 0.0))

            entry = {
                "subagent": sa, "current": current,
                "current_pass_rate": current_pr,
                "samples": samples,
            }

            # Insufficient samples → hold.
            if samples < min_samples:
                entry.update({"recommended": current, "new_pass_rate": current_pr,
                              "delta": 0.0, "status": "insufficient-data"})
                out.append(entry)
                continue

            if best is None:
                entry.update({"recommended": current, "new_pass_rate": current_pr,
                              "delta": 0.0, "status": "hold-no-winner"})
                out.append(entry)
                continue

            recommended_model, recommended_rate = best

            # No change needed if current is already the winner.
            if recommended_model == current:
                entry.update({"recommended": current,
                              "new_pass_rate": recommended_rate,
                              "delta": 0.0, "status": "hold-current-better"})
                out.append(entry)
                continue

            delta = round(recommended_rate - current_pr, 6)

            # never-downgrade: skip if recommended is worse than current observed.
            if cfg["never_downgrade"] and delta < 0:
                entry.update({"recommended": recommended_model,
                              "new_pass_rate": recommended_rate,
                              "delta": delta, "status": "hold-current-better"})
                out.append(entry)
                continue

            # min_delta: skip if improvement is below threshold.
            if delta < min_delta:
                entry.update({"recommended": recommended_model,
                              "new_pass_rate": recommended_rate,
                              "delta": delta, "status": "hold-current-better"})
                out.append(entry)
                continue

            # Flap detection: did this subagent oscillate to the recommended
            # model and back within the window?
            if _is_flapping(sa, current, recommended_model, history or [],
                            flap_window, now_ts):
                entry.update({"recommended": recommended_model,
                              "new_pass_rate": recommended_rate,
                              "delta": delta, "status": "hold-flapping"})
                out.append(entry)
                continue

            entry.update({"recommended": recommended_model,
                          "new_pass_rate": recommended_rate,
                          "delta": delta, "status": "recommend"})
            out.append(entry)

    # Sort: recommend first, then by delta desc.
    status_order = {"recommend": 0, "hold-flapping": 1, "insufficient-data": 2,
                    "hold-current-better": 3, "hold-no-winner": 4}
    out.sort(key=lambda r: (status_order.get(r["status"], 9),
                            -r.get("delta", 0), r["subagent"]))
    return out


def _is_flapping(
    subagent: str,
    current: str,
    candidate: str,
    history: list[dict[str, Any]],
    window_seconds: int,
    now_ts: float,
) -> bool:
    """True if history shows subagent swapped current→candidate AND
    candidate→current within the last window_seconds (an oscillation)."""
    cutoff = now_ts - window_seconds
    saw_to_candidate = False
    saw_back_to_current = False
    for h in history:
        if h.get("subagent") != subagent:
            continue
        ts = float(h.get("ts", 0))
        if ts < cutoff:
            continue
        frm = h.get("from", "")
        to = h.get("to", "")
        if frm == current and to == candidate:
            saw_to_candidate = True
        elif frm == candidate and to == current:
            saw_back_to_current = True
    return saw_to_candidate and saw_back_to_current


def apply_changes(
    changes: list[dict[str, Any]],
    agents_dir: Path | str,
) -> int:
    """Apply 'recommend' changes to subagent frontmatter files.

    Only entries with status == 'recommend' are written. Other statuses
    (hold-flapping, insufficient-data, hold-current-better, hold-no-winner)
    are skipped. Returns the count of files actually edited.
    """
    agents_path = Path(agents_dir)
    applied = 0
    for c in changes:
        if c.get("status") != "recommend":
            continue
        sa_path = agents_path / f"{c['subagent']}.md"
        if not sa_path.is_file():
            continue
        text = sa_path.read_text(encoding="utf-8")
        new_text = re.sub(
            r"^model:\s*.+$",
            f"model: {c['recommended']}",
            text, count=1, flags=re.MULTILINE,
        )
        if new_text != text:
            sa_path.write_text(new_text, encoding="utf-8")
            applied += 1
    return applied


def render_preview(changes: list[dict[str, Any]]) -> str:
    """Human-readable preview of recommendations (mirrors apply_eval_results)."""
    if not changes:
        return "No subagents to evaluate."
    recommend = [c for c in changes if c["status"] == "recommend"]
    if not recommend:
        return (f"No changes recommended — {len(changes)} subagent(s) reviewed, "
                f"0 actionable (held by guardrails).")
    lines = ["Adaptive routing recommendations (review before --apply):", ""]
    lines.append(f"{'subagent':<30} {'current':<22} → {'recommended':<22} "
                 f"{'Δpass':>6} {'samples':>7} {'status'}")
    lines.append("-" * 110)
    for c in changes:
        cur = c["current"].split(":")[-1] if c["current"].startswith("custom:") else c["current"]
        rec = c["recommended"].split(":")[-1] if c["recommended"].startswith("custom:") else c["recommended"]
        lines.append(f"{c['subagent']:<30} {cur:<22} → {rec:<22} "
                     f"{c.get('delta', 0):>+6.2f} {c.get('samples', 0):>7} {c['status']}")
    return "\n".join(lines)


__all__ = ["recommend_model_changes", "apply_changes", "render_preview",
           "DEFAULT_CONFIG"]
