# Reddit reference — `scripts/lib/platforms/reddit_rss.py`

## Endpoint (verified 2026-08-01)
- `https://www.reddit.com/r/<sub>/.rss` → HTTP 200, valid Atom 1.0, 25 entries/page
- DEAD: `.json` (HTTP 403 ทุก host: reddit.com, old.reddit.com)
- 429-prone: `/comments/.rss` (aggressively rate-limited — หลีกเลี่ยง)

## Auth
None. Reddit ปฏิเสธ anonymous UA — module ส่ง `A-Wiki-PlatformIngestBot/1.0`

## API
```python
from lib.platforms.reddit_rss import fetch_posts, parse_feed
posts = fetch_posts("python", limit=25)         # network
items = parse_feed(atom_xml_text)               # pure parser
```

## Output shape
```python
[{"title": str, "url": str, "summary": str, "published": str, "source": "reddit"}]
```
- `summary` truncated to 500 chars (HTML stripped)
- Fail-soft: `[{"error": "..."}]` on network/parse failure

## Limits
- 25 entries/page (Reddit's page size)
- `.rss` safe at low residential volume (a few req/min)
- Thread body ต้อง self-host redlib (Phase 2)

## Why not curl?
Reddit `.json` DEAD; `.rss` เป็น official public Atom ที่ยังใช้ได้ — แต่ต้อง
ส่ง UA จริง ไม่งั้น Reddit ปฏิเสธ
