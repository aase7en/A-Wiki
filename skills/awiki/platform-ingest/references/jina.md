# Jina Reader reference — `scripts/lib/platforms/jina_reader.py`

## Endpoint
- `https://r.jina.ai/{url}` → Markdown text (Jina's free public Reader API)
- No auth; free tier
- Adapted from Agent-Reach `channels/web.py:24-34` (MIT, 2026 Pnant/Panniantong)

## When to use
**Universal fallback** — เมื่อ URL ไม่ตรง backend อื่น (reddit/youtube/bilibili) หรือ
`scrape-advanced.py` tier 0-1 (curl/scrapling) โดน 403/anti-bot.

## API
```python
from lib.platforms.jina_reader import read
md = read("https://example.com/heavily-protected-page")   # → Markdown str
md = read("example.com/page")                             # auto-prepends https://
```

## Output shape
- Success: `str` (Markdown text)
- Fail-soft: `{"error": "..."}` on network error / non-200

## Behavior
- ปกติ URL ต้องมี `http://` หรือ `https://`; ถ้าไม่มี module เติม `https://` ให้
- Header: `User-Agent: A-Wiki-PlatformIngestBot/1.0`, `Accept: text/plain`
- Timeout: 30s

## Limits
- Free tier มี rate limit (ไม่เปิดเผยตัวเลข; residential low volume ปลอดภัย)
- ผลลัพธ์อาจมี prefix header ของ Jina (timestamp/source URL) — caller ต้อง parse เอา
- ไม่ใช่ "magic scraper" — ถ้าหน้านั้นกัน bot จริงๆ (Cloudflare challenge) Jina ก็อาจ fail

## Why a fallback (not primary)?
- Reddit/YouTube/Bilibili มี structured JSON ที่ parse ง่ายกว่า Markdown
- Jina return Markdown ซึ่งดีสำหรับ wiki ingestion แต่ structure ไม่คงที่
- ใช้เป็นทางเลือกสุดท้ายเมื่อ curl + structured API ไม่ work
