"""Cost History — USD estimation from eval results token counts (S6).

อ่าน `evals/subagents/results/results-*.json` (ที่มี tokens_in/tokens_out
จาก S6.0) + คูณกับ COST_MATRIX pricing → ได้ USD estimate per run per model.

ใช้สำหรับ "💰 Cost" dashboard tab:
  - line chart: USD per run per (suite, model)
  - bar chart: total USD per model (ใครแพงที่สุด?)

หมายเหตุ: cost = ESTIMATE (token counts จาก len//4 approximation × published
pricing) ไม่ใช่ exact API billing. Acceptable สำหรับ trend/comparison.

All functions pure (no I/O except collect_cost_history ที่อ่าน files).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RESULTS_DIR = REPO_ROOT / "evals" / "subagents" / "results"

# Import COST_MATRIX จาก cost-router.py (single source of truth)
# ชื่อไฟล์มี hyphen → ใช้ importlib (Python module name ต้องเป็น valid identifier)
import importlib.util  # noqa: E402
_COST_ROUTER_PATH = REPO_ROOT / "scripts" / "hermes" / "model-pool" / "cost-router.py"
_COST_ROUTER_OK = False
COST_MATRIX: dict = {}
try:
    _spec = importlib.util.spec_from_file_location("cost_router", str(_COST_ROUTER_PATH))
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        COST_MATRIX = _mod.COST_MATRIX
        _COST_ROUTER_OK = True
except Exception:
    pass

# Filename pattern: results-YYYYMMDD-HHMMSS.json
_FILENAME_RE = re.compile(r"^results-(\d{8}-\d{6})\.json$")

# Map eval shorthand model ids → COST_MATRIX keys (provider-qualified).
# คล้าย MODEL_ALIAS_MAP ใน run_subagent_eval.py แต่ map ไปยัง cost-router keys.
_MODEL_ALIAS_TO_COST_KEY = {
    "deepseek-v4-flash": "deepseek/deepseek-v4-flash",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "deepseek-v4-flash-lite": "deepseek/deepseek-v4-flash-lite",
    "glm-5.2": "zai-codeplan/glm-5.2",  # subscription (Codeplan) = $0
    "glm-5-turbo": "zai-codeplan/glm-5-turbo",
    "glm-4.7": "zai/glm-4.7",
    "glm-4.7-flash": "zai/glm-4.7-flash",
    "gemini-flash": "gemini/gemini-2.5-flash-lite",
    "sonnet": "anthropic/claude-sonnet-4",  # not in COST_MATRIX → $0 (subscription)
    "haiku": "anthropic/claude-haiku-4.5",
    "opus": "anthropic/claude-opus-4.1",
}


def estimate_model_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost สำหรับ model + token counts.

    Args:
      model_id: eval shorthand (e.g. "deepseek-v4-flash") OR provider-qualified
                (e.g. "deepseek/deepseek-v4-flash").
      tokens_in: input tokens (estimated).
      tokens_out: output tokens (estimated).

    Returns: USD cost (float). 0.0 สำหรับ unknown/free/subscription models.
    """
    # Resolve shorthand → COST_MATRIX key
    cost_key = _MODEL_ALIAS_TO_COST_KEY.get(model_id, model_id)
    if not _COST_ROUTER_OK:
        return 0.0
    prices = COST_MATRIX.get(cost_key)
    if not prices:
        return 0.0  # unknown model → $0 (ไม่ crash)
    input_cost = (tokens_in / 1_000_000) * prices.get("input", 0)
    output_cost = (tokens_out / 1_000_000) * prices.get("output", 0)
    return round(input_cost + output_cost, 6)


def collect_cost_history(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> dict[str, Any]:
    """Scan results-*.json, return USD cost time series per (suite, model).

    Returns:
      {
        runs: [ {date_tag, suites: {<suite>: {<model>: {usd, tokens_in, tokens_out}}}} ],
        total_usd: float,  # รวมทุก run ทุก model
        series: [],        # populated by to_cost_chart_series()
        summary: [],       # populated by model_cost_summary()
      }
    Runs sorted ascending by date_tag. Missing tokens → $0 (legacy compat).
    Missing dir → empty history (no exception).
    """
    rdir = Path(results_dir)
    if not rdir.is_dir():
        return {"runs": [], "total_usd": 0.0, "series": [], "summary": []}

    runs: list[dict[str, Any]] = []
    total_usd = 0.0

    for path in sorted(rdir.glob("results-*.json")):
        m = _FILENAME_RE.match(path.name)
        if not m:
            continue
        date_tag = m.group(1)
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue

        suites_out: dict[str, dict[str, dict]] = {}
        run_usd = 0.0
        for suite_name, suite_obj in data.items():
            if not isinstance(suite_obj, dict):
                continue
            by_model = suite_obj.get("by_model", {})
            if not isinstance(by_model, dict):
                continue
            models_out = {}
            for model, mstats in by_model.items():
                if not isinstance(mstats, dict):
                    continue
                tok_in = int(mstats.get("tokens_in", 0) or 0)
                tok_out = int(mstats.get("tokens_out", 0) or 0)
                usd = estimate_model_cost(model, tok_in, tok_out)
                run_usd += usd
                models_out[model] = {
                    "usd": usd,
                    "tokens_in": tok_in,
                    "tokens_out": tok_out,
                }
            if models_out:
                suites_out[suite_name] = models_out

        if suites_out:
            runs.append({"date_tag": date_tag, "suites": suites_out, "run_usd": round(run_usd, 6)})
            total_usd += run_usd

    runs.sort(key=lambda r: r["date_tag"])
    return {
        "runs": runs,
        "total_usd": round(total_usd, 6),
        "series": [],
        "summary": [],
    }


def to_cost_chart_series(history: dict[str, Any]) -> dict[str, Any]:
    """Convert history → Chart.js line-chart structure (USD per run per suite/model).

    Returns: {labels: [date_tag], datasets: [{label, data: [usd_or_null]}]}
    """
    runs = history.get("runs", [])
    if not runs:
        return {"labels": [], "datasets": []}

    labels = [r["date_tag"] for r in runs]
    # Discover all (suite, model) pairs
    pair_keys: list[tuple[str, str]] = []
    seen = set()
    for r in runs:
        for suite, models in r["suites"].items():
            for model in models:
                key = (suite, model)
                if key not in seen:
                    seen.add(key)
                    pair_keys.append(key)
    pair_keys.sort()

    datasets = []
    for suite, model in pair_keys:
        data = []
        for r in runs:
            info = r["suites"].get(suite, {}).get(model)
            data.append(info["usd"] if info else None)
        datasets.append({"label": f"{suite} / {model}", "data": data})

    return {"labels": labels, "datasets": datasets}


def model_cost_summary(history: dict[str, Any]) -> list[dict[str, Any]]:
    """Aggregate total USD per model across all runs (bar chart data).

    Returns: [ {model, total_usd, total_tokens_in, total_tokens_out, runs}, ... ]
    sorted descending by total_usd (most expensive first).
    """
    runs = history.get("runs", [])
    agg: dict[str, dict] = {}
    for r in runs:
        for suite, models in r["suites"].items():
            for model, info in models.items():
                a = agg.setdefault(model, {"model": model, "total_usd": 0.0,
                                           "total_tokens_in": 0, "total_tokens_out": 0, "runs": 0})
                a["total_usd"] += info["usd"]
                a["total_tokens_in"] += info["tokens_in"]
                a["total_tokens_out"] += info["tokens_out"]
                a["runs"] += 1
    # Round + sort
    out = []
    for a in agg.values():
        a["total_usd"] = round(a["total_usd"], 6)
        out.append(a)
    out.sort(key=lambda x: -x["total_usd"])
    return out


def build_dashboard_payload(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> dict[str, Any]:
    """One-call convenience for /api/eval/cost route."""
    history = collect_cost_history(results_dir)
    series = to_cost_chart_series(history)
    summary = model_cost_summary(history)
    return {
        "runs": history["runs"],
        "series": series,
        "summary": summary,
        "total_usd": history["total_usd"],
        "run_count": len(history["runs"]),
    }


__all__ = [
    "estimate_model_cost",
    "collect_cost_history",
    "to_cost_chart_series",
    "model_cost_summary",
    "build_dashboard_payload",
    "DEFAULT_RESULTS_DIR",
]
