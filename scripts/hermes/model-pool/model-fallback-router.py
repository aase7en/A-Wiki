#!/usr/bin/env python3
"""
Model Fallback Router — Restrict-Aware + Rate-Limit-Aware Auto-Switch
A-Wiki Brain · Hermes Agent

Two failure modes:
  1. RESTRICT (401/403) — provider-level BLACKLIST (persistent, manual recovery).
     Triggered by consecutive auth/restrict failures. Entire provider (e.g.
     zai-codeplan) is skipped until user clears restrict-state.json.
  2. RATE LIMIT (429) — short cooldown (60s), model-level, transient.

Usage:
    python3 model-fallback-router.py <failed_model> <capability> [--status 429]
    python3 model-fallback-router.py zai-codeplan/glm-5.2 reasoning --status 403

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
RESTRICT_PATH = os.path.join(SCRIPT_DIR, "restrict-state.json")
PRIORITY_CFG_PATH = os.path.join(SCRIPT_DIR, "model-priority-config.json")
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))

RESTRICT_STATUS = {401, 403}
RESTRICT_KEYWORDS = ["restricted", "unauthorized tool", "unsupported", "forbidden",
                     "not supported", "not allowed", "subscription benefits"]


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_pool():
    if not os.path.exists(POOL_PATH):
        return {"error": "No model pool found. Run model-pool-scanner.py first."}
    return load_json(POOL_PATH, {"error": "unreadable pool"})


def load_cooldowns():
    return load_json(STATE_PATH, {"cooldowns": {}})


def save_cooldowns(state):
    save_json(STATE_PATH, state)


def load_restrict():
    return load_json(RESTRICT_PATH, {"blacklisted_providers": {}, "schema_version": 1})


def save_restrict(state):
    save_json(RESTRICT_PATH, state)


def load_priority_cfg():
    return load_json(PRIORITY_CFG_PATH, {})


def is_cooling_down(model_ref, cooldowns):
    cd = cooldowns.get("cooldowns", {}).get(model_ref, {})
    if not cd:
        return False
    return time.time() < cd.get("until", 0)


def set_cooldown(model_ref, cooldowns, seconds=60):
    cooldowns["cooldowns"][model_ref] = {
        "since": time.time(),
        "until": time.time() + seconds,
        "reason": f"rate-limited, cooling {seconds}s",
    }
    save_cooldowns(cooldowns)


def is_restrict_status(status_code, body=""):
    """Decide if an HTTP failure indicates provider restriction (not transient)."""
    if status_code in RESTRICT_STATUS:
        low = (body or "").lower()
        if any(kw in low for kw in RESTRICT_KEYWORDS):
            return True
        # 401/403 without keyword still treated as restrict (auth/restrict family)
        return True
    return False


def blacklist_provider(provider, reason):
    """Persistently blacklist a provider (manual recovery)."""
    state = load_restrict()
    state.setdefault("blacklisted_providers", {})
    state["blacklisted_providers"][provider] = {
        "since": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "reason": reason,
        "recovery": "manual: delete entry from restrict-state.json",
    }
    save_restrict(state)
    return state


def clear_blacklist(provider=None):
    """Manual recovery: clear a provider (or all) from blacklist."""
    state = load_restrict()
    if provider:
        state.get("blacklisted_providers", {}).pop(provider, None)
    else:
        state["blacklisted_providers"] = {}
    save_restrict(state)
    return state


def blacklisted_providers():
    return set(load_restrict().get("blacklisted_providers", {}).keys())


def find_fallback(pool, failed_model, capability, cooldowns,
                  prefer_provider=None):
    """Find next available model with matching capability.

    Returns: (provider/model_id, base_url, status_message)
    """
    if "/" in failed_model:
        failed_provider, failed_id = failed_model.split("/", 1)
    else:
        failed_provider, failed_id = None, failed_model

    model_ref = f"{failed_provider}/{failed_id}" if failed_provider else failed_id

    chain = pool.get("fallback_chain", {}).get(capability, [])
    if not chain and capability == "text":
        chain = pool.get("fallback_chain", {}).get("text+vision", [])
    if not chain:
        return None, None, f"no fallback chain for capability '{capability}'"

    blacklist = blacklisted_providers()

    for candidate in chain:
        if "/" not in candidate:
            continue
        prov, mid = candidate.split("/", 1)
        candidate_ref = f"{prov}/{mid}"

        # Skip blacklisted providers (restrict)
        if prov in blacklist:
            continue
        # Skip cooling down (rate limit)
        if is_cooling_down(candidate_ref, cooldowns):
            continue
        # Skip the failed model
        if candidate_ref == model_ref:
            continue
        # Skip same provider unless no alternatives (rate-limit isolates provider)
        if prov == failed_provider and len(chain) > 1:
            continue

        provider_cfg = pool.get("providers", {}).get(prov, {})
        base_url = provider_cfg.get("base_url", "")
        return candidate_ref, base_url, f"switched {model_ref} -> {candidate_ref}"

    # Exhausted: clear stale cooldowns
    now = time.time()
    fresh = {"cooldowns": {k: v for k, v in cooldowns.get("cooldowns", {}).items()
                          if v.get("until", 0) > now}}
    save_cooldowns(fresh)
    return None, None, f"all {len(chain)} models in '{capability}' chain exhausted"


def handle_failure(failed_model, capability, status_code=429, body=""):
    """Route a failure: restrict -> blacklist provider; rate-limit -> cooldown.

    Returns (next_model, base_url, message, actions)
    """
    pool = load_pool()
    if "error" in pool:
        return None, None, pool["error"], []

    cooldowns = load_cooldowns()
    actions = []

    if "/" in failed_model:
        failed_provider, failed_id = failed_model.split("/", 1)
    else:
        failed_provider, failed_id = None, failed_model

    # RESTRICT path: blacklist entire provider
    if is_restrict_status(status_code, body):
        if failed_provider:
            blacklist_provider(failed_provider,
                               f"restrict: status {status_code} from {failed_model}")
            actions.append(f"BLACKLISTED provider '{failed_provider}' (manual recovery)")
        next_model, base_url, msg = find_fallback(
            pool, failed_model, capability, cooldowns)
        return next_model, base_url, msg, actions

    # RATE-LIMIT path: cooldown the model
    model_ref = f"{failed_provider}/{failed_id}" if failed_provider else failed_id
    set_cooldown(model_ref, cooldowns, 60)
    actions.append(f"cooled {model_ref} 60s (rate-limit)")
    next_model, base_url, msg = find_fallback(
        pool, failed_model, capability, cooldowns)
    return next_model, base_url, msg, actions


def update_hermes_aux_config(provider, model_id, capability):
    capability_map = {
        "text": None,
        "vision": "auxiliary.vision",
        "web_extract": "auxiliary.web_extract",
        "compression": "auxiliary.compression",
        "reasoning": None,
    }
    config_key = capability_map.get(capability)
    if not config_key:
        return False

    hermes_bin = os.path.join(HERMES_HOME, ".venv/bin/hermes")
    if not os.path.exists(hermes_bin):
        hermes_bin = "/opt/hermes/.venv/bin/hermes"
    if os.path.exists(hermes_bin):
        cmd = (f'{hermes_bin} config set {config_key}.model {model_id} && '
               f'{hermes_bin} config set {config_key}.provider {provider}')
        return os.system(cmd) == 0
    return False


def notify_telegram(message):
    """Best-effort Telegram alert (restrict events, advisory reports)."""
    notify = os.path.join(os.path.dirname(SCRIPT_DIR), "notify-telegram.sh")
    if not os.path.exists(notify):
        return False
    escaped = message.replace("'", "'\\''")
    return os.system(f"bash {notify} '{escaped}'") == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Model Fallback Router")
    parser.add_argument("failed_model", help="provider/model that failed")
    parser.add_argument("capability", help="text|vision|reasoning|...")
    parser.add_argument("--status", type=int, default=429,
                        help="HTTP status code of failure (429 default, 401/403 = restrict)")
    parser.add_argument("--body", default="", help="error response body (for restrict keyword check)")
    parser.add_argument("--unblacklist", default=None,
                        help="provider name to manually un-blacklist (recovery)")
    args = parser.parse_args()

    # Manual recovery
    if args.unblacklist is not None:
        clear_blacklist(args.unblacklist if args.unblacklist else None)
        print(json.dumps({"status": "ok", "action": "unblacklist",
                          "provider": args.unblacklist or "ALL"},
                         indent=2, ensure_ascii=False))
        return

    next_model, base_url, msg, actions = handle_failure(
        args.failed_model, args.capability, args.status, args.body)

    result = {"from": args.failed_model, "capability": args.capability,
              "status_code": args.status, "actions": actions, "message": msg}

    if next_model:
        prov, mid = next_model.split("/", 1)
        result.update({"status": "ok", "action": "switch", "to": next_model,
                       "provider": prov, "model": mid, "base_url": base_url,
                       "updated_config": update_hermes_aux_config(prov, mid, args.capability)})
        if args.status in RESTRICT_STATUS:
            notify_telegram(f"[Hermes] Codeplan RESTRICT: {args.failed_model} ({args.status}). "
                            f"Provider blacklisted. Switched to {next_model}. "
                            f"Manual recovery: edit restrict-state.json")
    else:
        result.update({"status": "exhausted"})
        notify_telegram(f"[Hermes] Fallback EXHAUSTED for {args.capability} after "
                        f"{args.failed_model} ({args.status}). All providers failed.")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
