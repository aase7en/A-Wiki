# Bilibili reference — `scripts/lib/platforms/bilibili_view.py`

## Endpoint (verified 2026-08-01)
- `https://api.bilibili.com/x/web-interface/view?bvid=<BV>` → HTTP 200, code:0
- DEAD: `?id=<aid>` (code -400 "请求错误"); ใช้ `?aid=<aid>` หรือ `?bvid=<BV>`
- Comments (`/x/v2/reply`) returns `replies:null` ถ้าไม่มี wbi-signature

## Auth
None สำหรับ view API. **ต้องส่ง `Referer: https://www.bilibili.com/`** — CDN
sometimes 412 ถ้าไม่มี (verified)

## API
```python
from lib.platforms.bilibili_view import fetch_metadata, extract_bvid, reshape_view
meta = fetch_metadata("https://www.bilibili.com/video/BV1xx411c7mD")   # network
bvid = extract_bvid("https://b23.tv/BV1xx411c7mD?t=30")                # → "BV1xx411c7mD"
```

## Output shape
```python
{
    "title":     "字幕君交流场所",
    "author":    "碧诗",
    "bvid":      "BV1xx411c7mD",
    "aid":       2,
    "url":       "https://www.bilibili.com/video/BV1xx411c7mD",
    "source":    "bilibili",
    "thumbnail": "https://i0.hdslb.com/...",
}
```
Fail-soft: `{"error": "..."}` on invalid URL / code != 0 / network error

## BV id format
`BV` + 10 chars from `[1-9A-HJ-NP-Za-km-z]` (base58-ish; skips I/O/0/1)

## Limits
- **Metadata only** — title, owner, pic, duration; ไม่มี comments
- Comments ต้อง wbi-signing (fetch nav endpoint → derive keys → sign params) — Phase 2
- Residential volume safe; Bilibili ไม่ค่อย IP-ban คนใช้น้อย

## Why not curl?
view API ใช้ curl ได้จริง แต่ต้อง: (1) ส่ง Referer, (2) ตรวจ `code==0` (Bilibili
return 200 แม้พารามิเตอร์ผิด แค่ code เป็นลบ), (3) extract BV จากหลาย URL shape
