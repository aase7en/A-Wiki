#!/usr/bin/env python3
"""
📊 Super Report: Mode + Balance + Usage + Routing
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent
"""
import json, os, subprocess, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ── Config ──
MODE_FILE = "/opt/data/.hermes-mode"
env_path = "/opt/data/.env"

env_vars = {}
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'\"")

# ── Check balances ──
def check(url, headers):
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)[:100]}

ds_raw = {}
or_raw = {}
if env_vars.get("DEEPSEEK_API_KEY",""):
    ds_raw = check("https://api.deepseek.com/user/balance",
                   {"Authorization": f"Bearer {env_vars['DEEPSEEK_API_KEY']}", "Accept":"application/json"})
if env_vars.get("OPENROUTER_API_KEY",""):
    or_raw = check("https://openrouter.ai/api/v1/auth/key",
                   {"Authorization": f"Bearer {env_vars['OPENROUTER_API_KEY']}"})

# Parse balances
ds_info = (ds_raw.get("balance_infos") or [{}])[0] if ds_raw else {}
ds_bal = float(ds_info.get("total_balance", 0)) if ds_info else 0
or_info = or_raw.get("data", {})
or_bal = or_info.get("limit_remaining", 0) or 0
or_limit = or_info.get("limit", 0) or 0
or_usage = or_info.get("usage_monthly", 0) or 0

# ── Mode ──
current_mode = "eco"
if os.path.exists(MODE_FILE):
    with open(MODE_FILE) as f:
        current_mode = f.read().strip().lower()

# Auto-force ECO if credit low
force_reason = None
if ds_bal < 0.30:
    force_reason = "DeepSeek critical ($%.2f)" % ds_bal
elif ds_bal < 0.50:
    force_reason = "DeepSeek low ($%.2f)" % ds_bal

if force_reason and current_mode == "pro":
    current_mode = "eco"
    with open(MODE_FILE, "w") as f:
        f.write("eco")

# ── Pricing ──
ECO_PAID = {
    0: ("DeepSeek V4 Flash", 0.14),
    1: ("DeepSeek Chat", 0.50),
}
PRO_PAID = {
    0: ("GLM-5.2", 0.00),
    1: ("DeepSeek Chat", 0.50),
    2: ("OpenRouter Premium", 0.20),
}
FREE_MODELS = {
    "eco": ["Step-3.7-Flash", "Gemini-Flash-Lite", "GLM-4.7-Flash"],
    "pro": ["Step-3.7-Flash", "Gemini-3-Flash", "GLM-4.7-Flash"],
}

# ── Budget ──
ds_tokens = int(ds_bal / 0.166 * 1_000_000) if ds_bal > 0 else 0
or_tokens = int(or_bal / 0.20 * 1_000_000) if or_bal > 0 else 0
total_budget = ds_bal + or_bal

# ── Usage ──
try:
    r = subprocess.run(
        ["/opt/hermes/.venv/bin/hermes", "insights", "--days", "30"],
        capture_output=True, text=True, timeout=20,
        env={**os.environ, "PATH": f"/opt/hermes/.venv/bin:{os.environ.get('PATH','')}"}
    )
    insights = r.stdout
    model_usage = {}
    for line in insights.split("\n"):
        line = line.strip()
        parts = line.split()
        if len(parts) >= 3 and any(c in parts[0] for c in ["deepseek","glm","step","gpt","claude","gemini"]):
            try:
                t = int(parts[-1].replace(",",""))
                model_usage[parts[0]] = t
            except: pass
    total_tok = sum(model_usage.values())
except:
    model_usage = {}
    total_tok = 0

# ═══════════════════
# 🖨️  PRINT REPORT
# ═══════════════════
mode_icon = "🟢" if current_mode == "eco" else "🔴"
mode_name = "ECO (ประหยัด)" if current_mode == "eco" else "PRO (ประสิทธิภาพ)"

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

print(f"╔══════════════════════════════════════╗")
print(f"║   📊 Provider Report (All-in-One)   ║")
print(f"╠══════════════════════════════════════╣")
print(f"║   {ts}")
print(f"╚══════════════════════════════════════╝")
print()

# 1. MODE
print(f"【ℹ️】Mode: {mode_icon} {mode_name}")
if force_reason:
    print(f"   ⚠️ Auto-ECO: {force_reason}")
print(f"   💡 Say 'เริ่ม [โปรเจกต์]' for PRO | 'กลับ eco' to save credits")
print()

# 2. BALANCE
print(f"【💰】Balance")
print(f"   ✅ DeepSeek      ${ds_bal:.2f}    (≈ {ds_tokens:,} tokens)")
print(f"   ✅ OpenRouter    ${or_bal:.2f}     (limit ${or_limit:.0f}/mo, used ${or_usage:.2f})")
print(f"   ✅ Z.AI/GLM      Weekly quota")
print(f"   ✅ Gemini        Free tier (1,500 req/day)")
print(f"   {'─'*45}")
print(f"   💰 Total budget: ${total_budget:.2f}")
print()

# 3. USAGE
print(f"【📊】Usage (30 days)")
if model_usage:
    for m, t in sorted(model_usage.items(), key=lambda x: -x[1]):
        pct = t/total_tok*100 if total_tok else 0
        print(f"   {m:<30} {t:>12,} tok ({pct:.0f}%)")
    print(f"   {'─'*45}")
    print(f"   {'TOTAL':<30} {total_tok:>12,} tok")
else:
    print("   (no data)")
print()

# 4. BUDGET HEALTH
print(f"【💪】Budget Health")
ds_h = "🟢" if ds_bal>1.0 else "🟡" if ds_bal>0.3 else "🔴"
or_h = "🟢" if or_bal>2.0 else "🟡" if or_bal>0.5 else "🔴"
print(f"   {ds_h} DeepSeek:   ${ds_bal:.2f}")
print(f"   {or_h} OpenRouter: ${or_bal:.2f}")

if current_mode == "eco":
    ds_days = ds_tokens / max(total_tok/30, 1) if total_tok else 999
    print(f"   📈 DeepSeek budget: ~{ds_days:.1f} days (ECO mode)")
    print(f"   🟢 ECO = using FREE models first → credit lasts longer")
elif current_mode == "pro":
    ds_days = ds_tokens / max(total_tok/30, 1) if total_tok else 999
    print(f"   📈 DeepSeek budget: ~{ds_days:.1f} days")
    if ds_bal < 0.50:
        print(f"   ⚠️ PRO mode with low credit — will auto-switch to ECO")
print()

# 5. ACTIVE TIERS
print(f"【🔀】Active Tiers ({mode_name})")
print()

ECO_FREE = [
    ("🆓  Step-3.7-Flash",      "Coding, agentic tasks, vision"),
    ("🆓  Gemini-Flash-Lite",   "Chat, search, light work (1M ctx)"),
    ("🆓  GLM-4.7-Flash",       "General text backup (quota)"),
]
PRO_FREE = [
    ("⭐  GLM-5.2",             "🏆 Top-tier: planning, design, reasoning"),
    ("🆓  Step-3.7-Flash",      "Coding, agentic subtasks"),
    ("🆓  Gemini-3-Flash",      "Multimodal, vision, analysis"),
]

if current_mode == "eco":
    for i, (name, use) in enumerate(ECO_FREE):
        print(f"   ✅ T{i} {name:<28} {use}")
    if ds_bal > 0.30:
        print(f"   ✅ T3 💲 DeepSeek V4 Flash     $0.14/M — Medium work (when needed)")
    if ds_bal > 0.50:
        print(f"   ✅ T4 💲 DeepSeek Chat         $0.50/M — Heavy reasoning (sparingly)")
else:
    for i, (name, use) in enumerate(PRO_FREE):
        print(f"   ✅ T{i} {name:<28} {use}")
    if ds_bal > 0.30:
        print(f"   ✅ T3 💲 DeepSeek Chat         $0.50/M — Analysis + reasoning")
    if or_bal > 0.50:
        print(f"   ✅ T4 💲 OpenRouter Premium    $0.20/M — Heavy lifting")
print()

# 6. DATA-AGE NOTE
print(f"──✦ DUAL-MODE ROUTER · A-Wiki Brain · Hermes Agent ✦──")
print(f"   {ts}")
print(f"   Mode state: /opt/data/.hermes-mode")
print(f"   Report: /opt/data/scripts/dual-mode-router.py")
