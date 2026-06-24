#!/usr/bin/env python3
"""
Dual-Mode Model Router — ECO / PRO
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent
"""
import json, os, sys, subprocess
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ════════════════════════════════
# CONFIG
# ════════════════════════════════
MODE_FILE = "/opt/data/.hermes-mode"

ECO_TIERS = [
    ("🆓  Step-3.7-Flash",      "stepfun/step-3.7-flash:free",    0.00, "Coding, agentic, multimodal"),
    ("🆓  Gemini-Flash-Lite",   "gemini/gemini-2.5-flash-lite",  0.00, "Chat, search, light work"),
    ("🆓  GLM-4.7-Flash",       "zai/glm-4.7-flash",             0.00, "General text (quota)"),
    ("💲  DeepSeek V4 Flash",   "deepseek/deepseek-v4-flash",     0.14, "Medium reasoning"),
    ("💲  DeepSeek Chat",       "deepseek/deepseek-chat",         0.50, "Heavy reasoning (sparingly)"),
]

PRO_TIERS = [
    ("⭐  GLM-5.2",             "zai/glm-5.2",                   0.00, "🏆 TOP — planning, design, deep reasoning"),
    ("🆓  Step-3.7-Flash",      "stepfun/step-3.7-flash:free",    0.00, "Coding, agentic subtasks"),
    ("💲  DeepSeek Chat",       "deepseek/deepseek-chat",         0.50, "Analysis, reasoning"),
    ("🆓  Gemini-3-Flash",      "gemini/gemini-3-flash-preview",  0.00, "Multimodal, vision"),
    ("💲  OpenRouter Premium",  "(openrouter/any)",              0.20, "Heavy lifting"),
]

# ════════════════════════════════
# READ BALANCE
# ════════════════════════════════
env_path = "/opt/data/.env"
env_vars = {}
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'\"")

def check_deepseek(key):
    try:
        req = Request("https://api.deepseek.com/user/balance",
                      headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        info = (d.get("balance_infos") or [{}])[0]
        return {"status": "ok", "balance": float(info.get("total_balance", 0))}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:60]}

def check_openrouter(key):
    try:
        req = Request("https://openrouter.ai/api/v1/auth/key",
                      headers={"Authorization": f"Bearer {key}"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        d = d.get("data", {})
        return {"status": "ok", "remaining": d.get("limit_remaining"), "limit": d.get("limit")}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:60]}

def check_zai(key):
    try:
        req = Request("https://api.z.ai/api/paas/v4/chat/completions",
                      data=json.dumps({"model":"glm-4.7-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":1}).encode(),
                      headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
        with urlopen(req, timeout=15) as r:
            return {"status": "ok", "note": "Weekly quota (active)"}
    except HTTPError as e:
        if e.code == 429: return {"status": "rate_limited"}
        return {"status": f"HTTP {e.code}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:60]}

balances = {}
for name, env_key, checker in [
    ("DeepSeek","DEEPSEEK_API_KEY",check_deepseek),
    ("OpenRouter","OPENROUTER_API_KEY",check_openrouter),
    ("Z.AI/GLM","GLM_API_KEY",check_zai),
]:
    key = env_vars.get(env_key, "")
    if not key or len(key) < 10:
        balances[name] = {"status": "not_configured"}
        continue
    balances[name] = checker(key)

ds_bal = balances.get("DeepSeek", {}).get("balance", 0)
or_bal = balances.get("OpenRouter", {}).get("remaining", 0) or 0

# ════════════════════════════════
# READ MODE
# ════════════════════════════════
current_mode = "eco"
if os.path.exists(MODE_FILE):
    with open(MODE_FILE) as f:
        current_mode = f.read().strip().lower()

# ════════════════════════════════
# AUTO-FORCE ECO IF LOW CREDIT
# ════════════════════════════════
force_eco_reason = None
if ds_bal < 0.50 and or_bal < 1.00:
    force_eco_reason = "⚠️ All paid credits low! Auto-forcing ECO mode"
elif ds_bal < 0.30:
    force_eco_reason = "🔴 DeepSeek nearly empty ($%.2f). Auto-force ECO" % ds_bal

if force_eco_reason and current_mode == "pro":
    current_mode = "eco"
    with open(MODE_FILE, "w") as f:
        f.write("eco")

# ════════════════════════════════
# GET USAGE FROM INSIGHTS
# ════════════════════════════════
def get_token_usage():
    try:
        r = subprocess.run(
            ["/opt/hermes/.venv/bin/hermes", "insights", "--days", "7"],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "PATH": f"/opt/hermes/.venv/bin:{os.environ.get('PATH','')}"}
        )
        # Parse total tokens
        for line in r.stdout.split("\n"):
            if "Total tokens:" in line:
                parts = line.split()
                for p in parts:
                    try:
                        return int(p.replace(",",""))
                    except: pass
        return 0
    except: return 0

total_tokens_7d = get_token_usage()

# ════════════════════════════════
# CALCULATE BUDGET
# ════════════════════════════════
daily_avg = total_tokens_7d / 7 if total_tokens_7d else 0
ds_tokens = int(ds_bal / 0.166 * 1_000_000) if ds_bal > 0 else 0
or_tokens = int(or_bal / 0.20 * 1_000_000) if or_bal > 0 else 0

# ════════════════════════════════
# GENERATE REPORT
# ════════════════════════════════
ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ── Mode Status ──
mode_icon = "🟢" if current_mode == "eco" else "🔴"
mode_label = "ECO (ประหยัด)" if current_mode == "eco" else "PRO (ประสิทธิภาพ)"

print(f"╔══════════════════════════════════════╗")
print(f"║   🔀 Dual-Mode Model Router        ║")
print(f"╠══════════════════════════════════════╣")
print(f"║   📅 {ts}")
print(f"╚══════════════════════════════════════╝")
print()

# Mode status
print(f"【ℹ️】 Current Mode: {mode_icon} {mode_label}")
if force_eco_reason:
    print(f"   {force_eco_reason}")
print()

# Balance
print(f"【💰】Credit Balance")
print(f"   ✅ DeepSeek      ${ds_bal:.2f}  (≈ {ds_tokens:,} tokens)")
print(f"   ✅ OpenRouter    ${or_bal:.2f}  (≈ {or_tokens:,} tokens)")
print(f"   ✅ Z.AI/GLM      Weekly quota active")
print()

# Budget health
print(f"【📊】Budget Health")
health = "🟢 Healthy" if ds_bal > 1.00 else "🟡 Low" if ds_bal > 0.50 else "🔴 Critical"
print(f"   DeepSeek:   {health}")
health2 = "🟢 Healthy" if or_bal > 2.00 else "🟡 Low" if or_bal > 1.00 else "🔴 Critical"
print(f"   OpenRouter: {health2}")
if daily_avg > 0:
    ds_days = ds_tokens / daily_avg if daily_avg > 0 else 0
    print(f"   7-day avg:  {daily_avg:,.0f} tok/day")
    print(f"   DeepSeek lasts ~{ds_days:.1f} days at current rate")
print()

# Available tiers
print(f"【🔀】Active Routing Tiers ({mode_label})")
print()

tiers = ECO_TIERS if current_mode == "eco" else PRO_TIERS
for i, (name, model, cost, use) in enumerate(tiers):
    # Mark as available/limited
    if cost > 0 and current_mode == "eco" and i >= 3:
        # Paid tiers - show with remaining balance
        avail = ds_bal > 0.50 or or_bal > 0.50
        status = "✅" if avail else "⛔ (no credit)"
        print(f"   {status}  Tier {i}: {name:25}  ${cost:.2f}/M  — {use}")
    elif cost > 0:
        status = "✅"
        print(f"   {status}  Tier {i}: {name:25}  ${cost:.2f}/M  — {use}")
    else:
        print(f"   ✅  Tier {i}: {name:25}  FREE      — {use}")
print()

# Project recommendations
if current_mode == "eco":
    print(f"【💡】ECO is active — saving credits.")
    print(f"   Use 'เริ่ม [project]' to switch to PRO mode")
    print(f"   Example: 'เริ่ม Sunday Estate' → GLM-5.2 for design + planning")
else:
    print(f"【💡】PRO mode active — full power for your projects:")
    print(f"   🏡 Sunday Estate webapp     → GLM-5.2 (structure + design)")
    print(f"   🤖 Robot Trading + AI       → GLM-5.2 + DeepSeek Chat")
    print(f"   🎮 Game Farm Invest Moon     → GLM-5.2 + Step-3.7 coding")
    print(f"   ♻️ IoT Hospital Waste        → Step-3.7 + Gemini")
    print(f"   Say 'จบโปรเจกต์' or 'กลับ eco' to switch back")
print()

# Auto-switch warning
if ds_bal < 0.50 and current_mode == "eco":
    print(f"【⚠️】Credit Alert")
    print(f"   DeepSeek < $0.50 — auto-force ECO mode for all tasks")
    print(f"   Consider topping up to unlock PRO mode")
elif ds_bal < 0.30:
    print(f"【🔴】Critical: DeepSeek nearly empty ($%.2f)" % ds_bal)
    print(f"   Route all non-critical work to Gemini/Step free models")
print()

# Footer
print(f"──✦ Dual-Mode Router · A-Wiki Brain · Hermes Agent ✦──")
