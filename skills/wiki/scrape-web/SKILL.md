---
name: scrape-web
description: Route a URL to the best available scraper (curl → Scrapling → Crawl4AI → Firecrawl → Browser Use) with device-aware degradation and raw/ provenance.
---

# scrape-web — Multi-Tier Web Scraper Router

> **Model-agnostic**. Works with any AI agent (Claude Code, Codex, Gemini CLI, Cursor).

## When to use

- A URL returns 403/Cloudflare/JS-rendered content in `ingest-source.py`
- A site requires browser rendering, login, or interaction
- Need bulk crawling or structured extraction (RAG chunking)
- `--file <path>` fails to convert a binary document

## Decision Flowchart

```
URL needs scraping?
├── Simple page, no blocking
│   └── Use ingest-source.py --url <url>
├── 403/Cloudflare detected
│   └── scrape-advanced.py --url <url> --method auto
├── JS-rendered / dynamic page
│   ├── MacBook → Crawl4AI or Browser Use
│   └── Pi5 → Firecrawl API (needs FIRECRAWL_API_KEY)
├── Bulk crawl (many pages)
│   └── Scrapy or Crawlee (see docs/protocols/scraping-advanced.md)
└── Login / multi-step form
    └── Browser Use (MacBook only, needs LLM backend)
```

## Tier Reference

| Tier | Method | Device | Install |
|------|--------|--------|---------|
| 0 | curl-impersonate | All | Binary (brew install curl-impersonate-chrome) |
| 1 | Scrapling | All | pip install scrapling |
| 1 | AutoScraper | All | pip install autoscraper |
| 2 | Crawl4AI | MacBook only | pip install crawl4ai && playwright install |
| 3 | Firecrawl API | All | pip install firecrawl + API key in drive/.secrets |
| 4 | Browser Use | MacBook only | pip install browser-use[all] |

## Usage

```bash
# List available methods for this device
python3 scripts/wiki/scrape-advanced.py --list

# Auto-pick best installed method
python3 scripts/wiki/scrape-advanced.py --url <url> --json

# Force a specific method (with fallback allowed)
python3 scripts/wiki/scrape-advanced.py --url <url> --method crawl4ai --fallback

# AutoScraper wizard mode (prompts for example items to extract)
python3 scripts/wiki/scrape-advanced.py --url <url> --method autoscraper --wizard

# Firecrawl (requires FIRECRAWL_API_KEY in drive/.secrets)
python3 scripts/wiki/scrape-advanced.py --url <url> --method firecrawl
```

## Provenance (Iron Law #7)

Every scrape automatically saves raw output to `raw/<slug>.md` **before** returning.
After scraping, feed the output into `ingest-source.py` to create the wiki source page:

```bash
python3 scripts/wiki/ingest-source.py --file raw/<slug>.md --domain <domain>
```

This ensures the `original_file: raw/<slug>.md` frontmatter passes the provenance hook.

## Device Blocking

| Device | Blocked methods |
|--------|----------------|
| Pi5 (headless) | Crawl4AI, Browser Use |
| Home Mac | None |
| Work PC | scrcpy (needs ADB + Android) |
