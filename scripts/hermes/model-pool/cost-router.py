#!/usr/bin/env python3
"""
Model Cost Router — Estimate + Recommend Best Value Tier
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Calculates cost per 1M tokens with cached-input awareness.
Recommends cheapest tier that can handle the task complexity.
"""
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POOL_PATH = os.path.join(SCRIPT_DIR, "model-pool.json")
COSTS_PATH = os.path.join(SCRIPT_DIR, "model-costs.json")

# Static cost matrix (USD per 1M tokens) — refreshed by scout
# Prices from OpenRouter API + Artificial Analysis, updated 2026-06
COST_MATRIX = {
    # Tier 0 — FREE
    "gemini/gemini-2.5-flash-lite":       {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},
    "gemini/gemini-3-flash-lite-preview":  {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},
    "zai/glm-4.7-flash":                  {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},
    "zai/glm-4.6v-flash":                 {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},
    "openrouter/poolside/laguna-m.1:free": {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},
    "groq/llama-3.3-70b-versatile":       {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True},

    # Tier 1 — Very Cheap
    "gemini/gemini-3-flash-preview":      {"input": 0.15, "output": 0.60, "cached": 0.04, "free": False},
    "deepseek/deepseek-v4-flash-lite":    {"input": 0.14, "output": 0.28, "cached": 0.07, "free": False},

    # Tier 2 — Value
    "deepseek/deepseek-v4-pro":           {"input": 1.10, "output": 4.40, "cached": 0.55, "free": False},
    "xai/grok-3-mini":                    {"input": 0.30, "output": 0.50, "cached": 0.00, "free": False},
}


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int,
                  cached_ratio: float = 0.0) -> dict:
    """Calculate estimated cost for a model"""
    prices = COST_MATRIX.get(model_id)
    if not prices:
        return {"error": f"unknown model: {model_id}"}

    cached_tokens = int(input_tokens * cached_ratio)
    uncached_tokens = input_tokens - cached_tokens

    input_cost = (uncached_tokens / 1_000_000) * prices["input"]
    cached_cost = (cached_tokens / 1_000_000) * prices.get("cached", prices["input"] * 0.5)
    output_cost = (output_tokens / 1_000_000) * prices["output"]

    total = input_cost + cached_cost + output_cost

    return {
        "model": model_id,
        "free": prices.get("free", False),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "cached_ratio": cached_ratio,
        "input_cost": round(input_cost, 6),
        "cached_cost": round(cached_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total, 6),
        "cost_per_1k": round((total / (input_tokens + output_tokens)) * 1000, 6),
    }


def recommend(input_tokens: int, output_tokens: int, cached_ratio: float = 0.0,
              prefer_free: bool = True, max_tier: int = 4) -> dict:
    """Recommend best model for given token budget"""
    results = []
    for model_id in COST_MATRIX:
        est = estimate_cost(model_id, input_tokens, output_tokens, cached_ratio)
        if "error" in est:
            continue
        results.append(est)

    # Sort by total cost
    results.sort(key=lambda x: (0 if x["free"] else 1, x["total_cost"]))

    return {
        "query": f"{input_tokens}+{output_tokens} tokens, {cached_ratio:.0%} cached",
        "recommended": results[0]["model"] if results else None,
        "top_3": [
            {"model": r["model"], "cost": f"${r['total_cost']:.6f}", "free": r["free"]}
            for r in results[:3]
        ],
        "all": results,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Model Cost Router")
    parser.add_argument("--tokens", type=int, default=10000, help="Estimated total input tokens")
    parser.add_argument("--output", type=int, default=2000, help="Estimated output tokens")
    parser.add_argument("--cached-ratio", type=float, default=0.0, help="Ratio of input that will be cached")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    rec = recommend(args.tokens, args.output, args.cached_ratio)

    if args.json:
        print(json.dumps(rec, indent=2, ensure_ascii=False))
    else:
        print(f"📊 Cost Estimate: {rec['query']}")
        print(f"🎯 Recommended: {rec['recommended']}")
        print()
        for r in rec["top_3"]:
            tag = "🆓 FREE" if r["free"] else f"💰 {r['cost']}"
            print(f"  {r['model']:50s} {tag}")


if __name__ == "__main__":
    main()
