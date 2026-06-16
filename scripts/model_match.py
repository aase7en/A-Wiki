#!/usr/bin/env python3
"""
model_match.py — Task -> tier -> price matrix for cost-aware (parallel) routing.

Given a task class and the scouted catalog (.tmp/model-catalog.json), pick the
cheapest model that fits the tier, and decide whether parallelizing is worth it.

Cost-first rules:
  * Pick the cheapest model in the tier's price band (free preferred).
  * Parallelize (race) ONLY when latency-sensitive AND there are >=2 free/cheap
    lanes AND the tier is cheap (L1/L2). Never pay 3x for trivial or flagship work.

Emits a `route_plan` event so the Live Dashboard shows which models a plan will
use (see scripts/live-dashboard/event_logger.py).

Usage:
  model_match.py <task_class> [--catalog <json>] [--latency] [--size N]
                 [--json] [--emit]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / ".tmp" / "model-catalog.json"
EVENT_LOGGER = REPO_ROOT / "scripts" / "live-dashboard" / "event_logger.py"

# task class -> base tier
TASK_TIER = {
    "search": "L1", "lookup": "L1", "summarize": "L1",
    "reason": "L2", "compare": "L2", "analyze": "L2",
    "scan": "L3", "longcontext": "L3",
    "code": "L4", "architect": "L4", "design": "L4",
}
# preferred price bands per target tier (cheapest fit first, then graceful fallback)
BAND_ORDER = {
    "L1": ["L1", "L2"],
    "L2": ["L2", "L1", "L3"],
    "L3": ["L3", "L2", "L4"],
    "L4": ["L4", "L3"],
}
ASSUMED_TOKENS = 1500  # rough in+out for a single delegated call (cost label only)


def _total(m: dict) -> float:
    try:
        return float(m.get("prompt_price") or 0) + float(m.get("completion_price") or 0)
    except (TypeError, ValueError):
        return float("inf")


def _is_free(m: dict) -> bool:
    return _total(m) == 0 or str(m.get("model_id", "")).endswith(":free")


def _est_cost(m: dict | None) -> str:
    if not m:
        return "$0.0000"
    total = _total(m)
    if total == float("inf"):
        return "n/a"
    return f"${total * ASSUMED_TOKENS:.4f}"


def pick_models(models: list[dict], tier: str):
    """Return (primary, fallbacks, free_count, band) for the target tier."""
    for band in BAND_ORDER.get(tier, [tier]):
        cands = [m for m in models if m.get("tier_hint") == band]
        if cands:
            cands.sort(key=_total)
            free_count = sum(1 for m in cands if _is_free(m))
            return cands[0], cands[1:3], free_count, band
    if models:
        ordered = sorted(models, key=_total)
        return ordered[0], ordered[1:3], sum(1 for m in ordered if _is_free(m)), None
    return None, [], 0, None


def decide(task_class: str, catalog, size: int = 0, latency: bool = False) -> dict:
    tier = TASK_TIER.get(task_class, "L2")
    # large inputs escalate trivial work one tier (free model may truncate/fail)
    if tier == "L1" and size and size > 8000:
        tier = "L2"
    models = catalog.get("models", []) if isinstance(catalog, dict) else (catalog or [])
    primary, fallbacks, free_count, band = pick_models(models, tier)

    parallelize = bool(latency and tier in ("L1", "L2") and free_count >= 2)
    race_models: list[str] = []
    if parallelize and primary:
        race_models = [primary["model_id"]] + [m["model_id"] for m in fallbacks]
        race_models = [m for m in race_models if str(m).endswith(":free")] or race_models

    return {
        "task_class": task_class,
        "tier": tier,
        "primary": primary.get("model_id") if primary else None,
        "fallbacks": [m["model_id"] for m in fallbacks],
        "parallelize": parallelize,
        "race_models": race_models,
        "free_lanes": free_count,
        "est_cost": _est_cost(primary),
        "reason": f"{task_class} -> {tier} (band {band}); "
                  f"{'parallel: latency + free lanes' if parallelize else 'sequential: cheapest-fit'}",
    }


def emit_route_plan(decision: dict) -> None:
    if not EVENT_LOGGER.exists():
        return
    models = " ".join(decision["race_models"] or [decision["primary"] or "?"])
    try:
        subprocess.run(
            [
                sys.executable, str(EVENT_LOGGER), "route_plan",
                f"tier={decision['tier']}",
                f"models={models}",
                f"parallelize={'1' if decision['parallelize'] else '0'}",
                f"est_cost={decision['est_cost']}",
            ],
            check=False, capture_output=True,
        )
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task->tier->price routing matrix")
    parser.add_argument("task_class", help="search|lookup|summarize|reason|compare|scan|code|architect")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--latency", action="store_true", help="latency-sensitive (enables race when cheap)")
    parser.add_argument("--size", type=int, default=0, help="approx input size in chars")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--emit", action="store_true", help="emit route_plan to the live dashboard")
    args = parser.parse_args(argv)

    catalog_path = Path(args.catalog)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    decision = decide(args.task_class, catalog, size=args.size, latency=args.latency)

    if args.emit:
        emit_route_plan(decision)

    if args.json:
        print(json.dumps(decision, ensure_ascii=False))
    else:
        print(f"{decision['task_class']} -> {decision['tier']}  primary={decision['primary']}")
        print(f"  fallbacks: {decision['fallbacks']}")
        print(f"  parallelize: {decision['parallelize']}  est_cost: {decision['est_cost']}")
        print(f"  {decision['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
