#!/usr/bin/env python3
"""
Provider Balance Check — GitHub Action version
Queries API balance using keys from GitHub Secrets (env vars)
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent
"""
import json, os, sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ═══════════════════════════════════════════
# Provider checkers
# ═══════════════════════════════════════════

def check_deepseek(key):
    try:
        req = Request("https://api.deepseek.com/user/balance",
                      headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        return {"status": "ok", "balance": d.get("total_balance"),
                "granted": d.get("granted_balance"), "topped_up": d.get("topped_up_balance")}
    except HTTPError as e:
        body = e.read().decode()[:150]
        return {"status": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_openrouter(key):
    try:
        req = Request("https://openrouter.ai/api/v1/auth/key",
                      headers={"Authorization": f"Bearer {key}"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        d = d.get("data", {})
        return {"status": "ok", "credits": d.get("credits"),
                "usage": d.get("usage"), "limit": d.get("limit")}
    except HTTPError as e:
        body = e.read().decode()[:150]
        return {"status": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_zai(key):
    """Z.AI GLM Coding Plan — test availability + check rate-limit status"""
    try:
        req = Request(
            "https://api.z.ai/api/paas/v4/chat/completions",
            data=json.dumps({
                "model": "glm-4.7-flash",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            }).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )
        with urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        return {"status": "ok", "note": "GLM Coding Plan = quota-based (Pro: 400/5h, 2,000/week)"}
    except HTTPError as e:
        body = e.read().decode()[:200]
        if e.code == 429:
            return {"status": "rate_limited", "detail": "Quota exceeded or model overloaded"}
        return {"status": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_gemini(key):
    try:
        req = Request(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        models = [m["name"].replace("models/","") for m in d.get("models",[]) if "gemini" in m["name"]]
        return {"status": "ok", "models": len(models), "note": "Free tier 1,500 req/day"}
    except HTTPError as e:
        body = e.read().decode()[:150]
        return {"status": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

def check_groq(key):
    try:
        req = Request("https://api.groq.com/openai/v1/models",
                      headers={"Authorization": f"Bearer {key}"})
        with urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        return {"status": "ok", "models": len(d.get("data",[])),
                "note": "Free tier: 30 req/min, 5,000 req/day"}
    except HTTPError as e:
        body = e.read().decode()[:150]
        return {"status": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:100]}

PROVIDERS = [
    ("DeepSeek",  "DEEPSEEK_API_KEY",  check_deepseek),
    ("OpenRouter","OPENROUTER_API_KEY",check_openrouter),
    ("Gemini",    "GOOGLE_API_KEY",    check_gemini),
    ("Z.AI/GLM",  "GLM_API_KEY",      check_zai),
    ("Groq",      "GROQ_API_KEY",     check_groq),
]

def main():
    results = {}
    for name, env_key, checker in PROVIDERS:
        key = os.environ.get(env_key, "")
        if not key or len(key) < 10:
            results[name] = {"status": "not_configured"}
            continue
        try:
            results[name] = checker(key)
        except Exception as e:
            results[name] = {"status": "error", "detail": str(e)[:100]}

    # ── Generate report ──
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# ☁️ Provider Balance Report", f"> Generated: {ts}", ""]

    for name, r in results.items():
        s = r.get("status", "unknown")
        icons = {"ok": "✅", "rate_limited": "⚠️", "not_configured": "⚪"}
        icon = icons.get(s, "❌")
        
        if s == "ok":
            if "balance" in r:
                lines.append(f"### {icon} {name}")
                lines.append(f"  - 💰 Balance: **${r['balance']}**")
                if r.get('granted'): lines.append(f"  - Granted: ${r['granted']}")
                if r.get('topped_up'): lines.append(f"  - Topped up: ${r['topped_up']}")
            elif "credits" in r:
                lines.append(f"### {icon} {name}")
                lines.append(f"  - 💳 Credits: **{r['credits']}**")
                if r.get('usage'): lines.append(f"  - Used: {r['usage']}")
            elif "models" in r:
                lines.append(f"### {icon} {name}")
                lines.append(f"  - 📡 {r['models']} models available")
            else:
                lines.append(f"### {icon} {name}")
        elif s == "not_configured":
            lines.append(f"### {icon} {name}")
            lines.append(f"  - API key not set in GitHub Secrets")
        elif s == "rate_limited":
            lines.append(f"### {icon} {name}")
            lines.append(f"  - ⏳ Rate limited / quota exceeded")
        else:
            lines.append(f"### {icon} {name}")
            lines.append(f"  - {r.get('detail', s)}")
        
        if "note" in r:
            lines.append(f"  - 📝 {r['note']}")
        lines.append("")

    ok_count = sum(1 for r in results.values() if r.get("status") == "ok")
    total = len(results)
    lines.insert(2, f"\n**{ok_count}/{total} providers connected**\n")

    report = "\n".join(lines)

    # Save to file (for Telegram action)
    with open("provider-balance-report.md", "w") as f:
        f.write(report)

    # Also JSON for reference
    with open("provider-balance-report.json", "w") as f:
        json.dump({
            "timestamp": ts,
            "results": results,
            "summary": {"ok": ok_count, "total": total}
        }, f, indent=2, ensure_ascii=False)

    print(report)

if __name__ == "__main__":
    main()
