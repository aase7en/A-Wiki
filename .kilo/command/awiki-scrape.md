---
description: Scrape a URL or convert a file for wiki ingestion (multi-tier router)
---

Scrape a URL using the best available method (curl-impersonate → Scrapling → Crawl4AI → Firecrawl → Browser Use) with device-aware degradation.

Raw output is automatically saved to `raw/<slug>.md` for provenance (Iron Law #7).

`!python3 scripts/wiki/scrape-advanced.py "$ARGUMENTS" --json`

See `skills/wiki/scrape-web/SKILL.md` for the full decision flowchart.
