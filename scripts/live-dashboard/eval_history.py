"""Eval History — time-series aggregation over results-*.json files (R3).

Reads `evals/subagents/results/results-YYYYMMDD-HHMMSS.json` files (committed
by the subagent-eval CI workflow) and produces a time series of pass@k per
(suite, model), plus regression-point detection for the dashboard chart.

The results-file schema (from run_subagent_eval.py line 324) is:
  { <suite_name>: { "suite": <name>, "by_model": { <model>: {pass_at_k, ...} }, "by_case": {} } }

Each suite is a TOP-LEVEL key in the JSON object — there is no wrapping
"suites" container.

Used by:
  - the dashboard "/api/eval/history" route (server.py)
  - the "📊 Eval" tab (live-dashboard.html, Chart.js line chart)

All functions are pure (no I/O except collect_history, which reads files),
so they are trivially testable with tmp_path fixtures.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RESULTS_DIR = REPO_ROOT / "evals" / "subagents" / "results"

# Filename pattern: results-YYYYMMDD-HHMMSS.json
_FILENAME_RE = re.compile(r"^results-(\d{8}-\d{6})\.json$")


def collect_history(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> dict[str, Any]:
    """Scan results-*.json files, return a chronologically-sorted time series.

    Args:
      results_dir: directory containing results-YYYYMMDD-HHMMSS.json files.

    Returns:
      {
        runs: [ {date_tag, suites: {<suite>: {<model>: pass_at_k}}} ],
        series: [],        # populated by to_chart_series()
        regressions: [],   # populated by detect_regression_points()
      }
    Runs are sorted ascending by date_tag. Malformed/empty files are skipped.
    Missing directory → empty history (no exception).
    """
    rdir = Path(results_dir)
    if not rdir.is_dir():
        return {"runs": [], "series": [], "regressions": []}

    runs: list[dict[str, Any]] = []
    for path in sorted(rdir.glob("results-*.json")):
        m = _FILENAME_RE.match(path.name)
        if not m:
            continue  # not a timestamped results file
        date_tag = m.group(1)
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue  # malformed JSON — skip
        if not isinstance(data, dict):
            continue
        # Flatten: {suite: {model: pass_at_k}}
        suites_out: dict[str, dict[str, float]] = {}
        for suite_name, suite_obj in data.items():
            # Skip non-suite keys (e.g. a "generated_at" metadata field if present).
            if not isinstance(suite_obj, dict):
                continue
            by_model = suite_obj.get("by_model", {})
            if not isinstance(by_model, dict):
                continue
            models_out = {}
            for model, mstats in by_model.items():
                if isinstance(mstats, dict) and "pass_at_k" in mstats:
                    try:
                        models_out[model] = round(float(mstats["pass_at_k"]), 3)
                    except (TypeError, ValueError):
                        continue
            if models_out:
                suites_out[suite_name] = models_out
        if suites_out:
            runs.append({"date_tag": date_tag, "suites": suites_out})

    # Sort by date_tag (filename already sortable, but be explicit).
    runs.sort(key=lambda r: r["date_tag"])
    return {"runs": runs, "series": [], "regressions": []}


def to_chart_series(history: dict[str, Any]) -> dict[str, Any]:
    """Convert collected history into Chart.js line-chart-friendly structure.

    Returns:
      {
        labels: [date_tag, ...],   # x-axis (one per run)
        datasets: [
          { label: "<suite> / <model>", data: [pass_at_k_or_null, ...] },
          ...
        ]
      }
    Each (suite, model) pair that appears in ANY run gets its own line.
    Runs where the pair is absent → null (gap in the line).
    """
    runs = history.get("runs", [])
    if not runs:
        return {"labels": [], "datasets": []}

    labels = [r["date_tag"] for r in runs]

    # Discover all (suite, model) pairs across all runs.
    pair_keys: list[tuple[str, str]] = []
    seen = set()
    for r in runs:
        for suite, models in r["suites"].items():
            for model in models:
                key = (suite, model)
                if key not in seen:
                    seen.add(key)
                    pair_keys.append(key)

    # Sort pairs for stable output: by suite then model.
    pair_keys.sort()

    datasets = []
    for suite, model in pair_keys:
        data = []
        for r in runs:
            val = r["suites"].get(suite, {}).get(model)
            data.append(val if val is not None else None)
        datasets.append({
            "label": f"{suite} / {model}",
            "data": data,
        })

    return {"labels": labels, "datasets": datasets}


def detect_regression_points(
    history: dict[str, Any],
    threshold: float = 0.10,
) -> list[dict[str, Any]]:
    """Find points where pass@k dropped more than `threshold` vs the prior run.

    Compares each (suite, model) pair's pass@k in run N against run N-1.
    If delta < -threshold, emits a regression point.

    Args:
      history: output of collect_history().
      threshold: minimum drop magnitude to flag (default 0.10 = 10 points).

    Returns:
      [ {suite, model, prev_pass_at_k, new_pass_at_k, delta, date_tag}, ... ]
    """
    runs = history.get("runs", [])
    regressions: list[dict[str, Any]] = []
    if len(runs) < 2:
        return regressions

    for i in range(1, len(runs)):
        prev = runs[i - 1]["suites"]
        curr = runs[i]["suites"]
        date_tag = runs[i]["date_tag"]
        for suite, models in curr.items():
            for model, pak in models.items():
                prev_pak = prev.get(suite, {}).get(model)
                if prev_pak is None:
                    continue  # new pair — no baseline to compare
                delta = round(pak - prev_pak, 3)
                if delta < -threshold:
                    regressions.append({
                        "suite": suite,
                        "model": model,
                        "prev_pass_at_k": prev_pak,
                        "new_pass_at_k": pak,
                        "delta": delta,
                        "date_tag": date_tag,
                    })

    # Sort worst-first.
    regressions.sort(key=lambda r: r["delta"])
    return regressions


def build_dashboard_payload(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> dict[str, Any]:
    """One-call convenience: collect + chart series + regressions.

    Returns the full payload for the /api/eval/history route:
      { runs, series, regressions, run_count, suite_model_count }
    """
    history = collect_history(results_dir)
    series = to_chart_series(history)
    regressions = detect_regression_points(history)
    suite_model_count = len(series["datasets"])
    return {
        "runs": history["runs"],
        "series": series,
        "regressions": regressions,
        "run_count": len(history["runs"]),
        "suite_model_count": suite_model_count,
    }


__all__ = [
    "collect_history",
    "to_chart_series",
    "detect_regression_points",
    "build_dashboard_payload",
    "DEFAULT_RESULTS_DIR",
]
