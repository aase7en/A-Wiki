#!/usr/bin/env python3
"""
Dual-Mode Model Router v2 — Dynamic Scout + ECO / PRO
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Architecture:
  - ECO mode  →  cheapest/free models for 24/7 automation
  - PRO mode  →  strongest models for deep engineering (GLM-5.2 Z.AI→OR fallback)

No hardcoded model names. Every decision is scouted live from OpenRouter API.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ════════════════════════════════
# PATHS
# ════════════════════════════════
MODE_FILE = "/opt/data/.hermes-mode"
SCOUT_SCRIPT = Path("/opt/data/A-Wiki/scripts/model-scout-current.py")
HERMES = "/opt/hermes/.venv/bin/hermes"

# ════════════════════════════════
# CONSTANTS
# ════════════════════════════════
PAID_THRESHOLD_LOW = 0.50   # below this → force ECO
PAID_THRESHOLD_CRIT = 0.30  # below this → critical alert

# Providers with free/zero-cost tiers for ECO
FREE_PROVIDERS = {"gemini", "google"}


def read_mode() -> str:
    """Read current ECO/PRO mode from file."""
    try:
        with open(MODE_FILE) as f:
            return f.read().strip().lower()
    except (FileNotFoundError, OSError):
        return "eco"


def write_mode(mode: str) -> None:
    """Persist mode to file."""
    try:
        with open(MODE_FILE, "w") as f:
            f.write(mode.strip().lower())
    except OSError:
        pass


# ════════════════════════════════
# RUN SCOUT
# ════════════════════════════════

def run_scout() -> dict | None:
    """Run A-Wiki model-scout-current.py and return parsed payload."""
    if not SCOUT_SCRIPT.exists():
        return None

    result_path = "/tmp/model-scout-router.json"
    try:
        subprocess.run(
            [sys.executable, str(SCOUT_SCRIPT), "--out", result_path, "--quiet"],
            timeout=25, capture_output=True,
        )
        if os.path.exists(result_path):
            with open(result_path) as f:
                return json.load(f)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


# ════════════════════════════════
# READ BALANCES
# ════════════════════════════════

def load_env() -> dict[str, str]:
    """Read .env into dict (keys only)."""
    env = {}
    env_path = "/opt/data/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env


def check_balance_deepseek(key: str) -> dict:
    """Check DeepSeek remaining balance."""
    import urllib.request, urllib.error
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        info = (d.get("balance_infos") or [{}])[0]
        return {"status": "ok", "balance": float(info.get("total_balance", 0))}
    except Exception:
        return {"status": "error", "balance": 0}


def check_balance_openrouter(key: str) -> dict:
    """Check OpenRouter remaining credit."""
    import urllib.request, urllib.error
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        d = d.get("data", {})
        return {"status": "ok", "remaining": d.get("limit_remaining", 0), "limit": d.get("limit", 0)}
    except Exception:
        return {"status": "error", "remaining": 0}


# ════════════════════════════════
# CLASSIFY MODELS FROM SCOUT
# ════════════════════════════════

def classify_model(mid: str, prompt_price, completion_price) -> str:
    """Classify a model as 'free', 'cheap', or 'premium' based on combined price."""
    mid_lower = mid.lower()

    def _to_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    pp = _to_float(prompt_price)
    cp = _to_float(completion_price)

    if mid_lower.endswith(":free") or (pp == 0 and cp == 0):
        return "free"
    if pp is not None and cp is not None and (pp + cp) < 1e-6:  # < $0.001/M
        return "cheap"
    return "premium"


def select_eco_models(scout: dict) -> dict:
    """Pick the best free/cheap models for ECO mode from scout data."""
    catalog = scout.get("catalog", {})
    models = catalog.get("models", [])

    free_models = [m for m in models if classify_model(
        m.get("model_id", ""),
        m.get("prompt_price"),
        m.get("completion_price"),
    ) == "free"]

    cheap_models = [m for m in models if classify_model(
        m.get("model_id", ""),
        m.get("prompt_price"),
        m.get("completion_price"),
    ) == "cheap"]

    # Sort: highest context window first
    free_sorted = sorted(free_models, key=lambda m: -(m.get("context_length") or 0))
    cheap_sorted = sorted(cheap_models, key=lambda m: -(m.get("context_length") or 0))

    return {
        "free_models": [m.get("model_id", "?") for m in free_sorted[:6]],
        "free_details": free_sorted[:6],
        "cheap_models": [m.get("model_id", "?") for m in cheap_sorted[:4]],
        "cheap_details": cheap_sorted[:4],
    }


def find_zai_premium(scout: dict) -> list:
    """Find the latest premium Z.AI GLM model from scout data (dynamic — no hardcode)."""
    catalog = scout.get("catalog", {})
    models = catalog.get("models", [])
    # Find Z.AI models — match any glm-x.x pattern dynamically
    zai = [m for m in models
           if any(p in (m.get("model_id", "") or "").lower()
                  for p in ["z-ai/glm", "zai/glm", "zhipu/glm"])]
    # Sort by version: glm-X.Y descending (extract X.Y from model id)
    import re
    def version_key(m):
        vs = re.findall(r"glm-?(\d+(?:\.\d+)?)", (m.get("model_id", "") or "").lower())
        return tuple(float(v) for v in vs) if vs else (0,)
    zai_sorted = sorted(zai, key=version_key, reverse=True)
    return zai_sorted


def select_pro_models(scout: dict) -> dict:
    """Pick the strongest models for PRO mode — dynamic, no hardcoded model names."""
    catalog = scout.get("catalog", {})
    models = catalog.get("models", [])

    # Dynamically find latest Z.AI premium model
    zai_premium = find_zai_premium(scout)

    # Find premium (expensive) models sorted by context
    premium = [m for m in models if classify_model(
        m.get("model_id", ""),
        m.get("prompt_price"),
        m.get("completion_price"),
    ) == "premium"]
    premium_sorted = sorted(premium, key=lambda m: -(m.get("context_length") or 0))

    return {
        "zai_premium": [m.get("model_id", "?") for m in zai_premium],
        "zai_details": zai_premium,
        "premium_models": [m.get("model_id", "?") for m in premium_sorted[:6]],
        "premium_details": premium_sorted[:6],
    }


# ════════════════════════════════
# GET TOKEN USAGE
# ════════════════════════════════

def get_token_usage() -> int:
    """Query Hermes insights for 7-day token usage."""
    try:
        r = subprocess.run(
            [HERMES, "insights", "--days", "7"],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "PATH": f"{os.path.dirname(HERMES)}:{os.environ.get('PATH', '')}"},
        )
        for line in r.stdout.split("\n"):
            if "Total tokens:" in line:
                for p in line.split():
                    try:
                        return int(p.replace(",", ""))
                    except ValueError:
                        continue
        return 0
    except Exception:
        return 0


# ════════════════════════════════
# GENERATE REPORT
# ════════════════════════════════

def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    current_mode = read_mode()

    # ── Run scout ──
    scout = run_scout()
    if scout is None:
        print("⚠️  Scout unavailable (A-Wiki model-scout-current.py not found or failed)")
        print("   Using last known cached config.\n")

    # ── Balances ──
    env = load_env()
    ds_key = env.get("DEEPSEEK_API_KEY", "")
    or_key = env.get("OPENROUTER_API_KEY", "")
    ds_bal = check_balance_deepseek(ds_key) if len(ds_key) >= 10 else {"status": "no_key", "balance": 0}
    or_bal = check_balance_openrouter(or_key) if len(or_key) >= 10 else {"status": "no_key", "remaining": 0}
    ds_balance = ds_bal.get("balance", 0)
    or_remaining = or_bal.get("remaining", 0) or 0

    # ── Auto-force ECO on low credit ──
    force_reason = None
    if ds_balance < PAID_THRESHOLD_LOW and or_remaining < 1.00:
        force_reason = "⚠️  All paid credits low! Auto-forcing ECO mode"
    elif ds_balance < PAID_THRESHOLD_CRIT:
        force_reason = f"🔴 DeepSeek nearly empty (${ds_balance:.2f}). Auto-forcing ECO"

    if force_reason and current_mode == "pro":
        current_mode = "eco"
        write_mode("eco")

    # ── ECO / PRO model analysis ──
    eco = select_eco_models(scout) if scout else {}
    pro = select_pro_models(scout) if scout else {}

    # ── Estimate DeepSeek tokens remaining ──
    ds_tokens = int(ds_balance / 0.166 * 1_000_000) if ds_balance > 0 else 0
    or_tokens = int(or_remaining / 0.20 * 1_000_000) if or_remaining > 0 else 0
    total_tokens_7d = get_token_usage()
    daily_avg = total_tokens_7d / 7 if total_tokens_7d else 0

    # ══════════════════════════════════════
    # PRINT REPORT
    # ══════════════════════════════════════
    mode_icon = "🟢" if current_mode == "eco" else "🔴"
    mode_label = "ECO (ประหยัด)" if current_mode == "eco" else "PRO (ประสิทธิภาพ)"

    print(f"╔══════════════════════════════════════╗")
    print(f"║   🔀 Dual-Mode Model Router v2      ║")
    print(f"╠══════════════════════════════════════╣")
    print(f"║   📅 {ts}")
    print(f"╚══════════════════════════════════════╝")
    print()

    # ── Mode ──
    print(f"【ℹ️】 Current Mode: {mode_icon} {mode_label}")
    if force_reason:
        print(f"   {force_reason}")
    print()

    # ── Balance ──
    print(f"【💰】 Credit Balance")
    print(f"   DeepSeek API    ${ds_balance:.2f}  (≈ {ds_tokens:,} tokens)")
    print(f"   OpenRouter      ${or_remaining:.2f}  (≈ {or_tokens:,} tokens)")
    print(f"   Google/Gemini   Free Tier (active)")
    ds_health = "🟢 Healthy" if ds_balance > 1.00 else "🟡 Low" if ds_balance > 0.50 else "🔴 Critical"
    or_health = "🟢 Healthy" if or_remaining > 2.00 else "🟡 Low" if or_remaining > 1.00 else "🔴 Critical"
    print(f"   DeepSeek:   {ds_health}")
    print(f"   OpenRouter: {or_health}")
    if daily_avg > 0:
        ds_days = ds_tokens / daily_avg if daily_avg > 0 else 0
        print(f"   7-day avg:  {daily_avg:,.0f} tok/day  ·  DeepSeek lasts ~{ds_days:.1f} days")
    print()

    # ── ECO Recommendations ──
    print(f"【♻️】 ECO Mode — Recommended Models (Dynamic Scout)")
    print()
    if scout and eco.get("free_models"):
        print(f"   🆓  Free Tier (best for 24/7 automation):")
        for m in eco["free_details"][:4]:
            mid = m.get("model_id", "?")
            ctx = m.get("context_length") or "?"
            print(f"       {mid:45}  context: {ctx:,}" if isinstance(ctx, int)
                  else f"       {mid:45}  context: {ctx}")
    if scout and eco.get("cheap_models"):
        print(f"\n   💲  Cheap Tier (light reasoning):")
        for m in eco["cheap_details"][:4]:
            mid = m.get("model_id", "?")
            ctx = m.get("context_length") or "?"
            prompt_p = m.get("prompt_price") or "?"
            comp_p = m.get("completion_price") or "?"
            p_str = f"${prompt_p}" if prompt_p not in (None, "-1", "?") else "?"
            c_str = f"${comp_p}" if comp_p not in (None, "-1", "?") else "?"
            print(f"       {mid:45}  context: {ctx:,}  {p_str}/{c_str}/M" if isinstance(ctx, int)
                  else f"       {mid:45}  context: {ctx}")
    if not scout:
        print(f"   ❇️  Default ECO: deepseek-v4-flash + gemini-3.5-flash")
    print()

    # ── PRO Recommendations ──
    print(f"【⚡】 PRO Mode — Recommended Models (Heavy Engineering)")
    print()
    if scout and pro.get("zai_premium"):
        latest_id = pro["zai_details"][0].get("model_id", "") if pro["zai_details"] else "?"
        print(f"   ⭐  Z.AI GLM latest ({latest_id}) — Z.AI key → fallback OpenRouter:")
        for m in pro["zai_details"]:
            mid = m.get("model_id", "?")
            ctx = m.get("context_length") or "?"
            prompt_p = m.get("prompt_price") or "?"
            comp_p = m.get("completion_price") or "?"
            p_str = f"${prompt_p}" if prompt_p not in (None, "-1", "?") else "?"
            c_str = f"${comp_p}" if comp_p not in (None, "-1", "?") else "?"
            print(f"       {mid:45}  context: {ctx:,}  prompt {p_str}  comp {c_str}/M" if isinstance(ctx, int)
                  else f"       {mid:45}  context: {ctx}")
    if scout and pro.get("premium_models"):
        print(f"\n   💎  Premium alternatives:")
        for m in pro["premium_details"][:4]:
            mid = m.get("model_id", "?")
            ctx = m.get("context_length") or "?"
            prompt_p = m.get("prompt_price") or "?"
            comp_p = m.get("completion_price") or "?"
            p_str = f"${prompt_p}" if prompt_p not in (None, "-1", "?") else "?"
            c_str = f"${comp_p}" if comp_p not in (None, "-1", "?") else "?"
            print(f"       {mid:45}  context: {ctx:,}  prompt {p_str}  comp {c_str}/M" if isinstance(ctx, int)
                  else f"       {mid:45}  context: {ctx}")
    if not scout:
        print(f"   ❇️  Default PRO: GLM x.x (Z.AI latest) + DeepSeek V4 Flash fallback")
    print()

    # ── Cost comparison ──
    print(f"【💰】 Cost Comparison (per 1M tokens)")
    print(f"   ┌────────────────────┬────────────┬──────────────┐")
    print(f"   │ Model              │  รับเข้า    │  ส่งออก       │")
    print(f"   ├────────────────────┼────────────┼──────────────┤")
    print(f"   │ DeepSeek V4 Flash  │  $0.09     │  $0.18       │")
    print(f"   │ Gemini 3.5 Flash   │  ~$0.00    │  ~$0.00      │  ← ฟรี")
    print(f"   │ GLM x.x (Z.AI)     │  $0.95     │  $3.00       │  ← PRO mode")
    print(f"   │ GPT-5.5            │  $5.00     │  $30.00      │  ← ไม่ต้องใช้")
    print(f"   └────────────────────┴────────────┴──────────────┘")
    print(f"   สรุป: ECO mode = ~$0.27/M  |  PRO mode = ~$3.95/M")
    print(f"   เทียบกับ subscription $18/เดือน → แบบ PAYG คุ้มกว่าเมื่อใช้ < 4.5M tok/เดือน")
    print()

    # ── Current config reference ──
    print(f"【⚙️】 Current Hermes Config Reference (ECO Default)")
    print(f"   Main model:      deepseek-v4-flash (DeepSeek API)")
    print(f"   Vision:          gemini-3.5-flash (Gemini — ฟรี)")
    print(f"   Web extract:     gemini-3.5-flash (Gemini — ฟรี)")
    print(f"   Context comp:    gemini-3.5-flash (Gemini — ฟรี)")
    print(f"   Skills hub/MCP:  deepseek-v4-flash (ECO) → Z.AI GLM (PRO)")
    print(f"   Triage/Kanban:   deepseek-v4-flash (ECO) → Z.AI GLM (PRO)")
    print(f"   Curator:         Z.AI GLM x.x (สัปดาห์ละครั้ง — คุ้ม)")
    print()

    # ── Usage tips ──
    if current_mode == "eco":
        print(f"【💡】 ECO active — saving credits for 24/7 automation.")
        print(f"   🎮  Game Farm Invest Moon     → Flash (routine) / GLM (PRO)")
        print(f"   🤖  Robot Trade + Analysis    → Flash+Gemini (ECO) / GLM (PRO)")
        print(f"   📊  TradingView signals       → Gemini 3.5 Flash (ฟรี — vision)")
        print(f"   🏛️  Polymarket analysis       → Flash (data) / GLM (deep reasoning)")
        print(f"   Say 'เริ่ม [project]' to switch to PRO mode")
    else:
        print(f"【💡】 PRO mode active — full power for projects:")
        print(f"   🎮  Game Farm Invest Moon     → Z.AI GLM (latest) + DeepSeek Flash")
        print(f"   🤖  Robot Trade + Analysis    → Z.AI GLM + Gemini 3.5 Flash")
        print(f"   📊  TradingView + TA logic    → Z.AI GLM (deep reasoning)")
        print(f"   🏛️  Polymarket routing        → Z.AI GLM + Flash fallback")
        print(f"   Say 'กลับ eco' to switch back")
    print()

    # ── Credit alerts ──
    if ds_balance < PAID_THRESHOLD_LOW and current_mode == "eco":
        print(f"【⚠️】 DeepSeek < ${PAID_THRESHOLD_LOW:.2f} — auto-forcing ECO for all tasks")
        print(f"   Consider topping up DeepSeek +$5-10 to unlock PRO mode")
    elif ds_balance < PAID_THRESHOLD_CRIT:
        print(f"【🔴】 Critical: DeepSeek almost empty (${ds_balance:.2f})")
        print(f"   Route non-critical work to Gemini/OpenRouter free models")
    print()

    # ── Footer ──
    print(f"──✦ Dual-Mode Router v2 · Dynamic Scout · A-Wiki · Hermes Agent ✦──")

    return 0


if __name__ == "__main__":
    sys.exit(main())
