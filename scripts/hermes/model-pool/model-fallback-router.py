#!/usr/bin/env python3
"""
Model Fallback Router — Rate-Limit-Aware Auto-Switch
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

When a provider hits rate limit (429), this picks the next available
free model with matching capability from an alternative provider.

Usage:
    python3 model-fallback-router.py <failed_model> <capability>

    # Called internally by Hermes cron/scripts
    python3 model-fallback-router.py gemini/gemini-3-flash-preview vision

Output:
    JSON with next model to use, or error if pool exhausted.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POOL_PATH = os.path.join(SCRIPT_DIR, "model-pool.json")
STATE_PATH = os.path.join(SCRIPT_DIR, "rate-limit-state.json")
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))


def load_pool() -> dict:
    """Load the model pool JSON"""
    if not os.path.exists(POOL_PATH):
        # Run scanner if pool doesn't exist
        scanner = os.path.join(SCRIPT_DIR, "model-pool-scanner.py")
        if os.path.exists(scanner):
            os.system(f"python3 {scanner}")
        if not os.path.exists(POOL_PATH):
            return {"error": "No model pool found. Run model-pool-scanner.py first."}

    with open(POOL_PATH) as f:
        return json.load(f)


def load_cooldowns() -> dict:
    """Load rate-limit cooldown state"""
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"cooldowns": {}}


def save_cooldowns(state: dict):
    """Save rate-limit cooldown state"""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def is_cooling_down(model_ref: str, cooldowns: dict) -> bool:
    """Check if a model is still in cooldown"""
    cd = cooldowns.get("cooldowns", {}).get(model_ref, {})
    if not cd:
        return False
    until = cd.get("until", 0)
    return time.time() < until


def set_cooldown(model_ref: str, cooldowns: dict, seconds: int = 60):
    """Mark a model as rate-limited for N seconds"""
    cooldowns["cooldowns"][model_ref] = {
        "since": time.time(),
        "until": time.time() + seconds,
        "reason": f"rate-limited, cooling {seconds}s",
    }
    save_cooldowns(cooldowns)


def find_fallback(pool: dict, failed_model: str, capability: str,
                  cooldowns: dict, prefer_provider: Optional[str] = None
                  ) -> Tuple[Optional[str], Optional[str], str]:
    """
    Find the next available model with matching capability.

    Returns: (provider/model_id, base_url, status_message)
    """
    # Parse failed model: "provider/model" or just "model"
    if "/" in failed_model:
        failed_provider, failed_id = failed_model.split("/", 1)
    else:
        failed_provider, failed_id = None, failed_model

    # Mark the failed model as cooling down
    model_ref = f"{failed_provider}/{failed_id}" if failed_provider else failed_id
    set_cooldown(model_ref, cooldowns, 60)

    # Get fallback chain for this capability
    chain = pool.get("fallback_chain", {}).get(capability, [])
    if not chain:
        # Try parent capabilities
        if capability in ("text",):
            chain = pool.get("fallback_chain", {}).get("text+vision", [])
        if not chain:
            return None, None, f"no fallback chain for capability '{capability}'"

    # Try each model in the chain
    for candidate in chain:
        if "/" not in candidate:
            continue
        prov, mid = candidate.split("/", 1)
        candidate_ref = f"{prov}/{mid}"

        # Skip if cooling down
        if is_cooling_down(candidate_ref, cooldowns):
            continue

        # Skip the failed model itself
        if candidate_ref == model_ref:
            continue

        # Skip if it's the same provider (unless no alternatives)
        if prov == failed_provider and len(chain) > 1:
            continue

        # Found a candidate
        provider_cfg = pool["providers"].get(prov, {})
        base_url = provider_cfg.get("base_url", "")

        return candidate_ref, base_url, f"switched from {model_ref} → {candidate_ref}"

    # All models exhausted — try clearing old cooldowns
    now = time.time()
    fresh_cooldowns = {
        "cooldowns": {
            k: v for k, v in cooldowns.get("cooldowns", {}).items()
            if v.get("until", 0) > now
        }
    }
    save_cooldowns(fresh_cooldowns)

    return None, None, f"all {len(chain)} models in '{capability}' chain exhausted or cooling"


def update_hermes_aux_config(provider: str, model_id: str, capability: str) -> bool:
    """Update Hermes config.yaml to use the fallback model for this capability"""
    # Determine which config key to update
    capability_map = {
        "text": None,  # main model — don't auto-switch
        "vision": "auxiliary.vision",
        "web_extract": "auxiliary.web_extract",
        "compression": "auxiliary.compression",
        "reasoning": None,  # no direct mapping
    }

    config_key = capability_map.get(capability)
    if not config_key:
        return False

    hermes_bin = os.path.join(HERMES_HOME, ".venv/bin/hermes")
    if not os.path.exists(hermes_bin):
        hermes_bin = "/opt/hermes/.venv/bin/hermes"

    if os.path.exists(hermes_bin):
        cmd = (
            f'{hermes_bin} config set {config_key}.model {model_id} && '
            f'{hermes_bin} config set {config_key}.provider {provider}'
        )
        ret = os.system(cmd)
        return ret == 0
    return False


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "message": "Usage: model-fallback-router.py <failed_model> <capability>",
            "example": "model-fallback-router.py gemini/gemini-3-flash-preview vision"
        }))
        sys.exit(1)

    failed_model = sys.argv[1]
    capability = sys.argv[2]

    pool = load_pool()
    if "error" in pool:
        print(json.dumps(pool))
        sys.exit(1)

    cooldowns = load_cooldowns()
    new_model, base_url, msg = find_fallback(pool, failed_model, capability, cooldowns)

    if new_model:
        prov, mid = new_model.split("/", 1)
        result = {
            "status": "ok",
            "action": "switch",
            "from": failed_model,
            "to": new_model,
            "provider": prov,
            "model": mid,
            "base_url": base_url,
            "capability": capability,
            "updated_config": update_hermes_aux_config(prov, mid, capability),
            "message": msg,
        }
    else:
        result = {
            "status": "exhausted",
            "from": failed_model,
            "capability": capability,
            "message": msg,
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
