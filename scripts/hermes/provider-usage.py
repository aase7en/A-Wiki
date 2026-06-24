#!/usr/bin/env python3
"""
Provider Usage Dashboard — Query API balance + remaining credits
[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent

Usage:
  python3 scripts/hermes/provider-usage.py              # human-readable
  python3 scripts/hermes/provider-usage.py --json       # JSON output
  python3 scripts/hermes/provider-usage.py --save       # save to drive/last-usage.json

Requires: Hermes environment (API keys in os.environ)
Run via:  hermes cron (gets real env vars)
          or terminal from Hermes session (gets real env vars)
"""
import json, os, sys, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "../../drive/last-usage.json"))

# ═══════════════════════════════════════════
# Provider checkers
# ═══════════════════════════════════════════

def check_deepseek(key: str) -> dict:
    """DeepSeek: query /user/balance"""
    try:
        req = Request("https://api.deepseek.com/user/balance",
                      headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return {
            "status": "ok",
            "available": data.get("is_available", False),
            "total_balance": data.get("total_balance", "unknown"),
            "granted_balance": data.get("granted_balance", "unknown"),
            "topped_up_balance": data.get("topped_up_balance", "unknown"),
        }
    except HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": "error", "detail": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:150]}

def check_openrouter(key: str) -> dict:
    """OpenRouter: query /auth/key for credits"""
    try:
        req = Request("https://openrouter.ai/api/v1/auth/key",
                      headers={"Authorization": f"Bearer {key}"})
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        d = data.get("data", {})
        return {
            "status": "ok",
            "credits": d.get("credits", "unknown"),
            "usage": d.get("usage", "unknown"),
            "limit": d.get("limit", "unknown"),
        }
    except HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": "error", "detail": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:150]}

def check_gemini(key: str) -> dict:
    """Gemini: test model availability (free tier = rate-limited, not credit-billed)"""
    try:
        req = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
            headers={"Content-Type": "application/json"}
        )
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        models = [m["name"] for m in data.get("models", []) if "gemini" in m.get("name", "")]
        return {
            "status": "ok",
            "models_available": len(models),
            "model_list": models[:5],
            "note": "Free tier: 1,500 req/day per model. No billing API.",
        }
    except HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": "error", "detail": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:150]}

def check_zai(key: str) -> dict:
    """Z.AI / GLM: test GLM-4.7 availability (Coding Plan = quota-based)"""
    try:
        req = Request(
            "https://api.z.ai/api/paas/v4/chat/completions",
            data=json.dumps({
                "model": "glm-4.7-flash",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            }).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
        )
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return {
            "status": "ok",
            "model": "glm-4.7-flash (Coding Plan)",
            "note": "Z.AI GLM Coding Plan = quota-based (ไม่ใช่ credit). Pro: 400/5h, 2,000/week",
        }
    except HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": "error" if e.code != 429 else "rate_limited",
                "detail": f"HTTP {e.code}: {body}",
                "note": "429 = quota exceeded or overloaded" if e.code == 429 else ""}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:150]}

def check_groq(key: str) -> dict:
    """Groq: test model availability (free tier)"""
    try:
        req = Request(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        models = [m["id"] for m in data.get("data", [])]
        return {
            "status": "ok",
            "models_available": len(models),
            "model_list": models[:5],
            "note": "Free tier: 30 req/min per model, 5,000 req/day total",
        }
    except HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": "error", "detail": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:150]}

# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════

PROVIDERS = {
    "DeepSeek":     ("DEEPSEEK_API_KEY", check_deepseek),
    "OpenRouter":   ("OPENROUTER_API_KEY", check_openrouter),
    "Gemini":       ("GOOGLE_API_KEY", check_gemini),
    "Z.AI / GLM":   ("GLM_API_KEY", check_zai),
    "Groq":         ("GROQ_API_KEY", check_groq),
}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Provider Usage Dashboard")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--no-save", action="store_true", help="Skip saving to file")
    args = parser.parse_args()

    results = {}
    for name, (env_var, checker) in PROVIDERS.items():
        key = os.environ.get(env_var, "")
        if key and len(key) > 10:
            try:
                results[name] = checker(key)
            except Exception as e:
                results[name] = {"status": "error", "detail": str(e)[:150]}
        else:
            results[name] = {"status": "not_configured", "detail": f"${env_var} not set"}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "timestamp": timestamp,
        "generated_by": "[Thai ไอ้A Plus Spot.] · A-Wiki Brain · Hermes Agent",
        "providers": results,
        "summary": {"total": len(results), "ok": 0, "error": 0, "not_configured": 0},
    }

    for name, r in results.items():
        if r.get("status") == "ok":
            report["summary"]["ok"] += 1
        elif r.get("status") in ("error", "rate_limited"):
            report["summary"]["error"] += 1
        else:
            report["summary"]["not_configured"] += 1

    if not args.no_save:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {SAVE_PATH}")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print()
        print("╔═══════════════════════════════════════╗")
        print("║  ☁️  Provider Usage Dashboard         ║")
        print(f"║  {timestamp}          ║")
        print("╚═══════════════════════════════════════╝")
        print()
        for name, r in results.items():
            st = r.get("status", "unknown")
            icon = {"ok": "✅", "error": "❌", "rate_limited": "⚠️", "not_configured": "⚪"}
            print(f"  {icon.get(st, '❓')} {name}")
            if st == "ok":
                if "total_balance" in r:
                    print(f"     Balance:   ${r['total_balance']}")
                if "credits" in r:
                    print(f"     Credits:   {r['credits']}")
                if "models_available" in r:
                    print(f"     Models:    {r['models_available']}")
                if "note" in r:
                    print(f"     Note:      {r['note']}")
            elif st == "error":
                print(f"     Detail:    {r.get('detail', 'unknown')}")
            elif st == "rate_limited":
                print(f"     ⭳ {r.get('note', 'Rate limited')}")
                print(f"     Detail:    {r.get('detail', '')}")
            else:
                print(f"     {r.get('detail', 'Not configured')}")
            print()

        print(f"  Summary: {report['summary']['ok']} ✅  |  {report['summary']['error']} ❌  |  {report['summary']['not_configured']} ⚪ not configured")
        print()

if __name__ == "__main__":
    main()
