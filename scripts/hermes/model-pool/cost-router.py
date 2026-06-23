#!/usr/bin/env python3
"""
Model Cost Router — Priority-Aware Tier Selection
A-Wiki Brain · Hermes Agent

Priority Chain:
  Tier -1: SUBSCRIPTION (Z.AI Codeplan) — Priority 1 (complex/routine, quota-limited)
  Tier 1:  CHEAP PAID (DeepSeek) — Priority 2 (DEFAULT — save Codeplan quota)
  Tier 0:  FREE (Z.AI pay-per-token, Gemini, OpenRouter) — Priority 3 (fallback)
  Tier 2:  VALUE (DeepSeek Pro) — Priority 2b (complex fallback when Codeplan restricted)

Calculates cost per 1M tokens with cached-input awareness.
Recommends cheapest tier that can handle the task complexity.

Usage:
    python3 cost-router.py --tokens 10000
    python3 cost-router.py --tokens 10000 --output 2000 --json
"""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POOL_PATH = os.path.join(SCRIPT_DIR, "model-pool.json")
RESTRICT_PATH = os.path.join(SCRIPT_DIR, "restrict-state.json")

# Cost matrix (USD per 1M tokens) — refreshed by scout/benchmark-scanner
# Source: Z.AI pricing page + DeepSeek + OpenRouter, updated 2026-06-23
COST_MATRIX = {
    # Tier -1 — SUBSCRIPTION (Priority 1 — Z.AI Codeplan, quota-limited)
    "zai-codeplan/glm-4.7":     {"input": 0.00, "output": 0.00, "cached": 0.00, "free": False, "subscription": True, "priority": 1, "quota_multiplier": 1},
    "zai-codeplan/glm-5.2":     {"input": 0.00, "output": 0.00, "cached": 0.00, "free": False, "subscription": True, "priority": 1, "quota_multiplier": 3},
    "zai-codeplan/glm-5-turbo": {"input": 0.00, "output": 0.00, "cached": 0.00, "free": False, "subscription": True, "priority": 1, "quota_multiplier": 3},

    # Tier 1 — CHEAP PAID (Priority 2 — DEFAULT: DeepSeek V4-Flash)
    "deepseek/deepseek-v4-flash":      {"input": 0.15, "output": 0.60, "cached": 0.04, "free": False, "subscription": False, "priority": 2},
    "deepseek/deepseek-v4-flash-lite": {"input": 0.14, "output": 0.28, "cached": 0.07, "free": False, "subscription": False, "priority": 2},

    # Tier 2 — VALUE (Priority 2b — complex fallback: DeepSeek V4-Pro)
    "deepseek/deepseek-v4-pro": {"input": 1.10, "output": 4.40, "cached": 0.55, "free": False, "subscription": False, "priority": 2},

    # Tier 0 — Z.AI PAY-PER-TOKEN (Priority 3 — free + cheap fallback)
    "zai/glm-4.7-flash":  {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "zai/glm-4.5-flash":  {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "zai/glm-4.6v-flash": {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "zai/glm-4.7-flashx": {"input": 0.07, "output": 0.40, "cached": 0.01, "free": False, "subscription": False, "priority": 3},
    "zai/glm-4.7":        {"input": 0.60, "output": 2.20, "cached": 0.11, "free": False, "subscription": False, "priority": 3},

    # Tier 0 — FREE OTHER (Priority 3 — last resort)
    "gemini/gemini-2.5-flash-lite":        {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "gemini/gemini-3-flash-lite-preview":  {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "openrouter/deepseek/deepseek-v4-flash-lite:free": {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "openrouter/poolside/laguna-m.1:free": {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},
    "groq/llama-3.3-70b-versatile":        {"input": 0.00, "output": 0.00, "cached": 0.00, "free": True, "subscription": False, "priority": 3},

    # Tier 3 — PREMIUM (emergency only)
    "xai/grok-3-mini":           {"input": 0.30, "output": 0.50, "cached": 0.00, "free": False, "subscription": False, "priority": 3},
}


def load_blacklist():
    """Load provider blacklist (restrict state). Returns set of provider names."""
    try:
        with open(RESTRICT_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        return set(state.get("blacklisted_providers", {}).keys())
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def estimate_cost(model_id, input_tokens, output_tokens, cached_ratio=0.0):
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
        "priority": prices.get("priority", 3),
        "subscription": prices.get("subscription", False),
        "free": prices.get("free", False),
        "quota_multiplier": prices.get("quota_multiplier", 0),
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


def recommend(input_tokens, output_tokens, cached_ratio=0.0,
              role="light", exclude_subscription=False):
    """Recommend best model for given token budget based on priority + role.

    role: 'light' (default DeepSeek), 'routine' (Codeplan GLM-4.7),
          'complex' (Codeplan GLM-5.2), 'fallback_complex' (DeepSeek Pro)
    """
    blacklist = load_blacklist()
    results = []
    for model_id in COST_MATRIX:
        # Skip blacklisted providers
        provider = model_id.split("/", 1)[0]
        if provider in blacklist:
            continue
        # Skip subscription if excluded
        prices = COST_MATRIX[model_id]
        if exclude_subscription and prices.get("subscription"):
            continue
        est = estimate_cost(model_id, input_tokens, output_tokens, cached_ratio)
        if "error" not in est:
            results.append(est)

    # Sort: subscription (prio 1) first, then cheapest within priority
    def sort_key(x):
        prio = x["priority"]
        cost = x["total_cost"]
        if prio == 1:
            return (0, x.get("quota_multiplier", 0))  # subscription: lower multiplier first
        elif prio == 2:
            return (1, cost)
        else:
            return (2, 0 if x["free"] else 1, cost)

    results.sort(key=sort_key)

    # Role-based default override
    role_defaults = {
        "light": "deepseek/deepseek-v4-flash",
        "routine": "zai-codeplan/glm-4.7",
        "complex": "zai-codeplan/glm-5.2",
        "fallback_complex": "deepseek/deepseek-v4-pro",
        "fallback_free": "zai/glm-4.7-flash",
    }
    preferred = role_defaults.get(role)
    chosen = None
    if preferred:
        for r in results:
            if r["model"] == preferred:
                chosen = preferred
                break
    if chosen is None and results:
        chosen = results[0]["model"]

    return {
        "role": role,
        "query": f"{input_tokens}+{output_tokens} tokens, {cached_ratio:.0%} cached",
        "blacklisted_providers": sorted(blacklist),
        "recommended": chosen,
        "top_3": [
            {"model": r["model"], "priority": r["priority"],
             "cost": f"${r['total_cost']:.6f}", "free": r["free"],
             "subscription": r["subscription"]}
            for r in results[:3]
        ],
        "all": results,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Model Cost Router")
    parser.add_argument("--tokens", type=int, default=10000, help="Estimated total input tokens")
    parser.add_argument("--output", type=int, default=2000, help="Estimated output tokens")
    parser.add_argument("--cached-ratio", type=float, default=0.0, help="Ratio of input cached")
    parser.add_argument("--role", default="light",
                        choices=["light", "routine", "complex", "fallback_complex", "fallback_free"],
                        help="Task role for routing")
    parser.add_argument("--no-subscription", action="store_true", help="Skip Codeplan subscription tier")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    rec = recommend(args.tokens, args.output, args.cached_ratio,
                    role=args.role, exclude_subscription=args.no_subscription)

    if args.json:
        print(json.dumps(rec, indent=2, ensure_ascii=False))
    else:
        print(f"Role: {rec['role']}  |  {rec['query']}")
        if rec["blacklisted_providers"]:
            print(f"Blacklisted: {', '.join(rec['blacklisted_providers'])}")
        print(f"Recommended: {rec['recommended']}")
        print()
        for r in rec["top_3"]:
            tags = []
            if r["subscription"]:
                tags.append("CODEPLAN")
            elif r["free"]:
                tags.append("FREE")
            tags.append(f"P{r['priority']}")
            tag_str = " | ".join(tags)
            print(f"  {r['model']:50s} {tag_str:18s} {r['cost']}")
        print()
        print("Priority Chain:")
        print("  1. Z.AI Codeplan (subscription, complex/routine)")
        print("  2. DeepSeek (paid, DEFAULT)")
        print("  3. Z.AI pay-per-token / Gemini / OpenRouter (free, fallback)")


if __name__ == "__main__":
    main()
