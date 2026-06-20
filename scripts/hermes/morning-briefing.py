#!/usr/bin/env python3
"""
Morning News Briefing — Finance + Tech + AI
Runs on Pi5 via systemd timer → sends to Telegram
"""
import os, json, sys, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

# ---- Config ----
BANGKOK_TZ = timezone(timedelta(hours=7))

# Load API keys from hermes-secrets
def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env

env = load_env(os.path.expanduser("~/hermes-secrets/.env"))
GROQ_KEY = env.get("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = env.get("TELEGRAM_CHAT_ID", "")

def web_search(query, limit=3):
    """Use DuckDuckGo HTML search (free, no API key needed)"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        results = []
        import re
        # Extract result snippets
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
        
        for i, (title, snippet) in enumerate(zip(titles[:limit], snippets[:limit])):
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            results.append(f"{clean_title}: {clean_snippet}")
        
        return results if results else [f"Search: {query} — no results parsed"]
    except Exception as e:
        return [f"Search failed: {e}"]

def summarize_with_ai(news_items, category):
    """Use Groq API to summarize news in Thai"""
    if not GROQ_KEY:
        return summarize_simple(news_items, category)
    
    prompt = f"""Summarize the following {category} news in Thai. 
For each item: 1-2 sentence summary + 1 sentence AI analysis.
Keep it concise. Use emoji.

News:
{chr(10).join(news_items[:5])}

Format:
💰/🤖/🧠 [Category]
• [Summary] — 📌 [Analysis]
"""

    try:
        data = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a Thai news analyst. Always respond in Thai."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.3
        }).encode()
        
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ AI summary unavailable ({e})\n" + summarize_simple(news_items, category)

def summarize_simple(items, category):
    """Fallback: simple concatenation"""
    emoji = {"finance": "💰", "tech": "🤖", "ai": "🧠"}.get(category, "📰")
    lines = [f"{emoji} **{category.upper()}**"]
    for item in items[:3]:
        lines.append(f"• {item[:200]}")
    return "\n".join(lines)

def send_telegram(message):
    """Send message via Telegram bot API"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured — printing to stdout:")
        print(message)
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"Telegram send failed: {e}")
        print(message)
        return False

# ---- Main ----
if __name__ == "__main__":
    today = datetime.now(BANGKOK_TZ).strftime("%d %B %Y")
    
    print(f"=== Morning Briefing: {today} ===")
    
    # 1. Finance News
    print("[1/3] Searching finance news...")
    finance_raw = web_search("financial markets investing news today", 3)
    finance_raw += web_search("crypto bitcoin news today", 2)
    
    # 2. Tech News
    print("[2/3] Searching tech news...")
    tech_raw = web_search("technology news breakthroughs today", 3)
    
    # 3. AI News
    print("[3/3] Searching AI news...")
    ai_raw = web_search("artificial intelligence news breakthrough today", 3)
    
    # Summarize each
    print("Summarizing with AI...")
    finance_summary = summarize_with_ai(finance_raw, "finance")
    tech_summary = summarize_with_ai(tech_raw, "tech")
    ai_summary = summarize_with_ai(ai_raw, "ai")
    
    # Build final message
    message = f"""📊 <b>สรุปข่าวเช้า — {today}</b>

{finance_summary}

{tech_summary}

{ai_summary}

---
⚡ <i>Hermes News Briefing — อัตโนมัติทุกเช้า 7:00 น.</i>"""
    
    # Send
    success = send_telegram(message)
    if success:
        print("✅ Sent to Telegram!")
    else:
        print("❌ Delivery failed (Telegram not configured or error)")
