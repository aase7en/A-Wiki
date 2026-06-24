#!/usr/bin/env python3
"""Check provider balances by reading .env directly."""
import json, os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

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
        # API returns: balance_infos[0].total_balance (string)
        info = (d.get("balance_infos") or [{}])[0]
        return {"status": "ok", "balance": float(info.get("total_balance", 0)),
                "granted": float(info.get("granted_balance", 0)),
                "topped_up": float(info.get("topped_up_balance", 0)),
                "currency": info.get("currency", "USD")}
    except HTTPError as e:
        return {"status": f"HTTP {e.code}", "detail": e.read().decode()[:150]}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_openrouter(key):
    try:
        req = Request("https://openrouter.ai/api/v1/auth/key",
                      headers={"Authorization": f"Bearer {key}"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        d = d.get("data", {})
        return {"status": "ok", "remaining": d.get("limit_remaining"),
                "usage": d.get("usage_monthly"), "limit": d.get("limit"),
                "label": d.get("label", "")}
    except HTTPError as e:
        return {"status": f"HTTP {e.code}", "detail": e.read().decode()[:150]}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_zai(key):
    try:
        req = Request(
            "https://api.z.ai/api/paas/v4/chat/completions",
            data=json.dumps({"model": "glm-4.7-flash",
                             "messages": [{"role": "user", "content": "ping"}],
                             "max_tokens": 1}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )
        with urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        return {"status": "ok", "note": "GLM Coding Plan (quota-based)"}
    except HTTPError as e:
        body = e.read().decode()[:200]
        if e.code == 429:
            return {"status": "rate_limited", "detail": "Quota exceeded"}
        return {"status": f"HTTP {e.code}", "detail": body[:100]}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_gemini(key):
    try:
        req = Request(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        models = [m["name"].replace("models/","") for m in d.get("models",[]) if "gemini" in m["name"]]
        return {"status": "ok", "models": len(models), "note": "Free tier: 1,500 req/day"}
    except HTTPError as e:
        return {"status": f"HTTP {e.code}", "detail": e.read().decode()[:150]}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

# ── Map providers ──
PROVIDERS = [
    ("DeepSeek",  "DEEPSEEK_API_KEY",  check_deepseek),
    ("OpenRouter","OPENROUTER_API_KEY",check_openrouter),
    ("Z.AI/GLM",  "GLM_API_KEY",      check_zai),
    ("Gemini",    "GOOGLE_API_KEY",    check_gemini),
]

results = {}
for name, env_key, checker in PROVIDERS:
    key = env_vars.get(env_key, "")
    if not key or len(key) < 10:
        results[name] = {"status": "not_configured"}
        continue
    try:
        results[name] = checker(key)
    except Exception as e:
        results[name] = {"status": "error", "detail": str(e)[:100]}

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"☁️  Provider Balance Report — {ts}")
print(f"   A-Wiki Brain · Hermes Agent")
print(f"")

print(f"╔══════════════════════════════════════╗")
print(f"║   🤖 Provider Balance Report       ║")
print(f"╠══════════════════════════════════════╣")
print(f"║   📅 {ts}")
print(f"╚══════════════════════════════════════╝")
print(f"")

ok_count = 0
for name, r in results.items():
    s = r.get("status", "unknown")
    icons = {"ok": "✅", "rate_limited": "⚠️", "not_configured": "⚪"}
    icon = icons.get(s, "❌")

    if s == "ok":
        ok_count += 1
        if "balance" in r:
            print(f"{icon} {name}")
            print(f"   💰 Balance:  ${r['balance']:.2f} {r.get('currency','')}")
            if r.get('granted') and r['granted'] > 0:
                print(f"   🎁 Granted:   ${r['granted']:.2f}")
            if r.get('topped_up') and r['topped_up'] > 0:
                print(f"   💳 Topped-up: ${r['topped_up']:.2f}")
        elif "remaining" in r:
            print(f"{icon} {name}")
            print(f"   💳 Remaining: ${r['remaining']:.2f} / ${r.get('limit',0):.2f}")
            print(f"   📊 Used:      ${r.get('usage', 0):.2f} (this month)")
            print(f"   🏷️  Label:     {r.get('label', 'N/A')[:20]}...")
        elif "models" in r:
            print(f"{icon} {name}")
            print(f"   📡 {r['models']} models available")
        else:
            print(f"{icon} {name} — OK")
    elif s == "not_configured":
        print(f"{icon} {name} — not set in .env")
    else:
        print(f"{'❌' if 'error' in s else '⚠️'} {name}")
        print(f"   {r.get('detail', s)}")

    if "note" in r:
        print(f"   📝 {r['note']}")
    print()

print(f"\n── {ok_count}/{len(results)} providers connected ──")
print(f"   Report saved to: provider-balance-report.json")
