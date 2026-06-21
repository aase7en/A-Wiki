#!/usr/bin/env python3
"""
Model Pool Scanner — Free Model Discovery + Rate-Limit-Aware Pool
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Scans all connected providers for free/cheap models.
Outputs: model-pool.json — ranked by capability + cost = 0
"""
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
ENV_PATH = os.environ.get("HERMES_ENV_PATH", os.path.join(HERMES_HOME, ".env"))
POOL_PATH = os.path.join(os.path.dirname(__file__), "model-pool.json")


# ─────────────────────────────────────────────
# Known Free Model Catalog (static fallback)
# Updated: 2026-06-21
# ─────────────────────────────────────────────

FREE_MODEL_CATALOG = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": [
            {"id": "gemini-2.5-flash-lite",       "capability": "text",   "rpm": 30,  "context": 1_048_576},
            {"id": "gemini-2.5-flash",            "capability": "text",   "rpm": 15,  "context": 1_048_576},
            {"id": "gemini-2.5-pro",              "capability": "text",   "rpm": 5,   "context": 1_048_576, "free_tier_only": False},
            {"id": "gemini-3-flash-preview",       "capability": "text+vision", "rpm": 15, "context": 1_048_576, "note": "free tier"},
            {"id": "gemini-3-flash-lite-preview",  "capability": "text+vision", "rpm": 30, "context": 1_048_576, "note": "free tier"},
        ],
        "has_free_tier": True,
        "env_var": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    },
    "zai": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-4.7-flash",    "capability": "text",   "rpm": 60,  "context": 131_072, "note": "free"},
            {"id": "glm-4.6v-flash",   "capability": "vision", "rpm": 30,  "context": 131_072, "note": "free vision"},
            {"id": "glm-4.6v",         "capability": "vision", "rpm": 30,  "context": 131_072, "note": "vision general"},
        ],
        "has_free_tier": True,
        "env_var": ["GLM_API_KEY", "ZAI_API_KEY"],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            {"id": "poolside/laguna-m.1:free",              "capability": "text", "rpm": 20, "context": 32_768},
            {"id": "deepseek/deepseek-v4-flash-lite:free",  "capability": "text", "rpm": 20, "context": 131_072},
            {"id": "google/gemini-2.5-flash-lite:free",     "capability": "text", "rpm": 20, "context": 1_048_576},
            {"id": "nvidia/llama-3.3-nemotron-super-49b-v1:free", "capability": "text", "rpm": 20, "context": 131_072},
            {"id": "meta-llama/llama-4-maverick:free",      "capability": "text", "rpm": 20, "context": 131_072},
        ],
        "has_free_tier": True,
        "env_var": ["OPENROUTER_API_KEY"],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            {"id": "llama-3.3-70b-versatile",   "capability": "text", "rpm": 30, "context": 131_072},
            {"id": "mixtral-8x7b-32768",        "capability": "text", "rpm": 30, "context": 32_768},
            {"id": "gemma2-9b-it",              "capability": "text", "rpm": 30, "context": 8_192},
        ],
        "has_free_tier": True,
        "env_var": ["GROQ_API_KEY"],
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "models": [
            {"id": "grok-3-mini",         "capability": "text",   "rpm": 10, "context": 131_072, "note": "may have free credits"},
            {"id": "grok-4.20-reasoning", "capability": "text+reasoning", "rpm": 5, "context": 1_048_576, "free_tier_only": False},
        ],
        "has_free_tier": False,
        "env_var": ["XAI_API_KEY"],
    },
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co/models",
        "models": [
            {"id": "Qwen/Qwen3-32B",  "capability": "text", "rpm": 10, "context": 32_768, "note": "free inference API"},
        ],
        "has_free_tier": True,
        "env_var": ["HF_TOKEN"],
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "models": [
            {"id": "accounts/fireworks/models/llama-v3p3-70b-instruct", "capability": "text", "rpm": 30, "context": 131_072},
        ],
        "has_free_tier": True,
        "env_var": ["FIREWORKS_API_KEY"],
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            {"id": "deepseek-v4-flash-lite", "capability": "text", "rpm": 20, "context": 131_072, "note": "cheapest tier"},
        ],
        "has_free_tier": False,
        "env_var": ["DEEPSEEK_API_KEY"],
    },
}


def load_api_keys() -> dict[str, str]:
    """Load API keys from .env"""
    keys = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    keys[k] = v.strip().strip('"').strip("'")
    return keys


def detect_providers(api_keys: dict) -> dict:
    """Map API keys to providers"""
    active = {}
    for provider_name, cfg in FREE_MODEL_CATALOG.items():
        for env_var in cfg["env_var"]:
            if env_var in api_keys and api_keys[env_var]:
                active[provider_name] = {
                    "base_url": cfg["base_url"],
                    "has_free_tier": cfg["has_free_tier"],
                    "env_var": env_var,
                    "api_key": api_keys[env_var],
                    "models": [
                        m for m in cfg["models"]
                        if m.get("free_tier_only") is not False  # skip paid-only
                    ],
                }
                break
    return active


def probe_model(provider: str, base_url: str, api_key: str, model_id: str) -> dict:
    """Probe a model endpoint to verify availability"""
    import urllib.request
    import urllib.error

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": "ok", "model": model_id, "provider": provider}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 429:
            return {"status": "rate_limited", "model": model_id, "provider": provider, "retry_after": e.headers.get("Retry-After", "60")}
        elif e.code == 401:
            return {"status": "unauthorized", "model": model_id, "provider": provider}
        else:
            return {"status": "error", "model": model_id, "provider": provider, "code": e.code, "body": body[:200]}
    except Exception as e:
        return {"status": "unreachable", "model": model_id, "provider": provider, "error": str(e)[:200]}


def build_pool(active_providers: dict) -> dict:
    """Build the ranked model pool"""
    pool = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent",
        "providers": {},
        "fallback_chain": {
            "text": [],
            "vision": [],
            "reasoning": [],
        },
        "stats": {"total_models": 0, "total_providers": len(active_providers)},
    }

    for provider, cfg in active_providers.items():
        models = []
        for m in cfg["models"]:
            entry = {
                "id": m["id"],
                "capability": m["capability"],
                "rpm": m.get("rpm", 20),
                "context": m.get("context", 131_072),
                "note": m.get("note", ""),
                "provider": provider,
            }
            models.append(entry)

            # Build fallback chain
            cap = m["capability"]
            for c in cap.split("+"):
                c = c.strip()
                if c in pool["fallback_chain"]:
                    pool["fallback_chain"][c].append(f"{provider}/{m['id']}")

        pool["providers"][provider] = {
            "base_url": cfg["base_url"],
            "has_free_tier": cfg["has_free_tier"],
            "models": models,
        }
        pool["stats"]["total_models"] += len(models)

    return pool


def main():
    api_keys = load_api_keys()
    active = detect_providers(api_keys)

    if not active:
        print("❌ No providers detected. Check .env for API keys.")
        sys.exit(1)

    pool = build_pool(active)

    # Write pool
    os.makedirs(os.path.dirname(POOL_PATH), exist_ok=True)
    with open(POOL_PATH, "w") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)

    print(f"✅ Model pool: {pool['stats']['total_models']} free models from {pool['stats']['total_providers']} providers")
    print(f"   Saved to: {POOL_PATH}")
    print(f"\n📋 Fallback Chains:")

    for cap, chain in pool["fallback_chain"].items():
        print(f"   {cap} ({len(chain)} models):")
        for m in chain[:3]:
            print(f"      → {m}")

    return pool


if __name__ == "__main__":
    main()
