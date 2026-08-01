# YouTube reference — `scripts/lib/platforms/youtube_oembed.py`

## Endpoint (verified 2026-08-01)
- `https://www.youtube.com/oembed?url=https%3A//www.youtube.com/watch%3Fv%3D<id>&format=json`
- HTTP 200, valid JSON, no auth

## Auth
None.

## API
```python
from lib.platforms.youtube_oembed import fetch_metadata, extract_video_id, reshape_oembed
meta = fetch_metadata("https://youtu.be/dQw4w9WgXcQ")          # network
vid  = extract_video_id("https://youtu.be/dQw4w9WgXcQ&t=42s")  # → "dQw4w9WgXcQ"
```

## Output shape
```python
{"title": str, "author": str, "thumbnail": str, "url": str, "source": "youtube"}
```
Fail-soft: `{"error": "..."}` on invalid URL / network error / non-200

## URL shapes supported
`watch?v=`, `youtu.be/`, `embed/`, `shorts/`, `live/`, `m.youtube.com/watch?v=`

## Limits
- **Metadata only** — ไม่มี transcript, duration, view count
- Transcript ต้อง `yt-dlp` + `yt-dlp-ejs` (JS engine) + `curl_cffi` — Phase 2 opt-in
- Video id = 11 chars `[A-Za-z0-9_-]`

## Why not curl?
oEmbed เป็น official public endpoint ที่ไม่ต้อง auth; curl ใช้ได้ตรงๆ แต่
ยังไงก็ต้อง parse JSON + extract video id จากหลาย URL shape — module
จัดการให้
