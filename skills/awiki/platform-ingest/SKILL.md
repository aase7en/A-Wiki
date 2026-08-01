---
name: platform-ingest
description: "ดึง content จาก platform (Reddit RSS, YouTube oEmbed, Bilibili view, Jina fallback) แบบ no-auth/no-cookie — เติม gap ที่ curl/scrape-advanced ตาย (anti-bot, 403). Dispatcher ล้วน ไม่มีเทคนิคของตัวเอง; เรียก backend ใน scripts/lib/platforms/. Trigger: 'reddit', 'youtube', 'bilibili', 'ดึงโพสต์', 'platform-ingest'."
version: 1.0.0
author: A-Wiki
domain: [engineering, code]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/platform-ingest"
a_phase: any
---

# Platform-Ingest — ดึง content จาก platform (no-auth)

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก URL →
> backend module ใน `scripts/lib/platforms/`. ถ้าต้อง *อธิบายวิธีทำ* แปลว่า
> มันควรเป็น canonical skill ไม่ใช่ pack
>
> **ทำไมมี**: `scripts/wiki/scrape-advanced.py` + `curl` ตายตรง anti-bot
> (Twitter syndication, Reddit `.json` 403, Nitter challenge, Bilibili
> wbi-sign). Agent-Reach ใช้ cookie-based unofficial scrapers (ToS risk +
> Iron Law #6 violation). Pack นี้เลือกเฉพาะทางเลือกที่ **verified ใช้ได้
> จริง 2026 + no-auth + ToS-compliant**

## เมื่อไหร่ใช้

✅ ใช้:
- อ่าน latest posts จาก subreddit (RSS feed)
- ดึง metadata วิดีโอ YouTube (title, author, thumbnail)
- ดึง metadata วิดีโอ Bilibili (title, owner, duration)
- อ่าน URL ทั่วไปที่ `curl`/`scrape-advanced.py` โดน 403/429/anti-bot
- ตรวจสถานะ backends ทั้งหมด (`/platform-ingest doctor`)

❌ ข้าม:
- อ่านหน้าเว็บทั่วไปที่ `curl` ใช้ได้อยู่ → `scrape-advanced.py` tier 0
- ดึง tweet → ไม่มีทางปลอดภัย 2026 (oEmbed dead, Nitter anti-bot)
- ดึง Reddit thread body → `.json` 403; thread content = Phase 2 (redlib opt-in)
- ดึง YouTube transcript → ต้อง `yt-dlp` + `yt-dlp-ejs` (Phase 2)
- ดึง XiaoHongShu → ไม่มี no-auth path
- ดึง Bilibili comments → ต้อง wbi-signing (Phase 2)

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain ถ้าไม่ประกาศ phase
> จะไหลจาก ASK ไป IMPLEMENT โดยไม่มีอะไรจับได้

```
focus_set({"skill": "platform-ingest", "goal": "<URL หรือ platform + done criteria>", "phase": "ask"})
```

## Backend registry

| Name | Module | Endpoint (verified 2026-08-01) | Auth | Output |
|------|--------|-------------------------------|------|--------|
| `reddit`   | `scripts/lib/platforms/reddit_rss.py`     | `reddit.com/r/X/.rss`                          | None | list[{title,url,summary,published}] |
| `youtube`  | `scripts/lib/platforms/youtube_oembed.py` | `youtube.com/oembed?url=...`                   | None | {title,author,thumbnail,url} (metadata only) |
| `bilibili` | `scripts/lib/platforms/bilibili_view.py`  | `api.bilibili.com/x/web-interface/view?bvid=X` | None | {title,author,bvid,aid,thumbnail} (metadata only) |
| `jina`     | `scripts/lib/platforms/jina_reader.py`    | `r.jina.ai/{url}` (Jina Reader free)           | None | Markdown text (universal fallback) |

> Health-check: `python scripts/wiki/platform-doctor.py` (run before relying on a backend)

## Phase → action

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | (internal) URL detection | ดู URL แล้ว resolve ไป backend (`extract_video_id` / `extract_bvid` / host match) |
| DESIGN | — | ไม่ต้อง — backend เลือกอัตโนมัติ |
| PLAN | — | — |
| IMPLEMENT | เรียก backend module ตรงๆ | `from lib.platforms.reddit_rss import fetch_posts` |
| REVIEW | (verify output shape) | ตรวจ dict keys ครบ + ไม่มี `error` |
| DEBUG | `platform-doctor.py` + ดู status | probe backend ก่อน ดูว่า alive ไหม |
| TEST | `python -m pytest tests/platforms/` | 69 tests |

> เดิน phase ด้วย `focus_advance` · จบงาน `focus_clear`
> backend ทุกตัว fail-soft: return `{"error": "..."}` ไม่ใช่ raise

## Code example (caller pattern)

```python
import sys
sys.path.insert(0, "scripts/lib")

# Reddit: latest 25 posts from r/python
from platforms.reddit_rss import fetch_posts
posts = fetch_posts("python", limit=25)  # list[{title,url,summary,published,source}]

# YouTube: metadata for one video
from platforms.youtube_oembed import fetch_metadata
meta = fetch_metadata("https://youtu.be/dQw4w9WgXcQ")  # {title,author,thumbnail,url,source}

# Bilibili: metadata for one video
from platforms.bilibili_view import fetch_metadata
meta = fetch_metadata("https://www.bilibili.com/video/BV1xx411c7mD")

# Jina: any URL → Markdown (universal fallback)
from platforms.jina_reader import read
md = read("https://example.com/heavily-protected-page")  # str (Markdown)

# Doctor: probe all backends
from platforms.doctor import check_all, render_text
print(render_text(check_all()))
```

## CLI

```bash
# Probe all backends (default)
python scripts/wiki/platform-doctor.py

# JSON output for agent consumption
python scripts/wiki/platform-doctor.py --json

# Probe one channel
python scripts/wiki/platform-doctor.py reddit

# List registered backends
python scripts/wiki/platform-doctor.py --list
```

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ Agent-Reach เลยไม่ดีกว่าเหรอ?" | ไม่ — Agent-Reach ใช้ cookie-based unofficial scrapers (twitter-cli/rdt-cli/bili-cli) ที่ผิด ToS และ Iron Law #6; + ดึง dependency หนัก + `rich`; + doctor มันไม่ยอมทดสอบจริง (Agent-ReachTrap #1) |
| "ทำไมไม่ curl ธรรมดา?" | Reddit `.json` ตายแล้ว (403); Nitter anti-bot; syndication.twitter.com ว่างเปล่า — curl ดิบไม่ผ่าน anti-bot ของ platform ยุคใหม่ |
| "ทำไมไม่ใส่ Twitter/X?" | ไม่มี no-auth path ที่ verified ใช้ได้ 2026: oEmbed dead (`publish.x.com/oembed` → 404), syndication ว่าง, Nitter/xcancel โดน anti-bot challenge. Cookie-based = ผิด Iron Law #6 |
| "ทำไม YouTube ได้แค่ metadata?" | oEmbed ให้ title/author/thumbnail ไม่ให้ transcript; transcript ต้อง `yt-dlp` + `yt-dlp-ejs` (JS engine) ซึ่งเป็น dep หนัก — Phase 2 opt-in |
| "Reddit thread body ล่ะ?" | `.json` DEAD ตั้งแต่ 2025; thread body ต้อง self-host redlib (OAuth spoofing) — Phase 2 opt-in |
| "pack นี้ควรมี fetch logic ของตัวเอง" | ไม่ — logic อยู่ใน `scripts/lib/platforms/` (separation of concerns); pack = dispatcher only |

## Patterns borrowed

จาก Agent-Reach (MIT, 2026 Pnant/Panniantong) — re-implemented ไม่ vendored:
- `ordered_backends()` 2-pass routing (`channels/base.py:29-70`) → `scripts/lib/platforms/base.py`
- doctor per-channel resilience (`doctor.py:16-45`) → `scripts/lib/platforms/doctor.py`
- Jina Reader wrapper (`channels/web.py:24-34`) → `scripts/lib/platforms/jina_reader.py`

## Invocation

```
/platform-ingest <URL หรือ "reddit r/X" หรือ "doctor">
```
