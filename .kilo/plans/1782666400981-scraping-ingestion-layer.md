# A-Wiki Universal Scraping & Ingestion Layer (USIL)

> **Goal**: Integrate 10 open-source web scraping/crawling/document-conversion tools into A-Wiki so every AI Agent (Hermes+Telegram on Pi5, Claude Code, Codex, Antigravity, Cursor) can extract web content and convert documents into Markdown for wiki ingestion — at lowest cost, with graceful device-aware degradation.
>
> **Architecture decision**: Option C — Hybrid (Tier 0-1 light tools embedded in `ingest-source.py`; Tier 2-4 heavy tools in standalone `scrape-advanced.py`)
>
> **Overlap audit result**: 10/10 tools are NEW capabilities — zero duplication with existing A-Wiki functionality (`web-research` is LLM Q&A not scraping; `extract_text_from_url()` is plain `curl`; Anthropic `docx/pptx/pdf` skills are human-facing doc creation not pipeline conversion).

---

## Context & Constraints

### Source tools (10 GitHub repos)
| Tool | Repo | Role | Tier |
|------|------|------|------|
| MarkItDown | microsoft/markitdown | PDF/DOCX/XLSX/PPTX → Markdown | 0 |
| curl-impersonate | lwthiker/curl-impersonate | TLS-fingerprint HTTP fetch (bypass Cloudflare/Akamai) | 0 |
| Scrapling | D4Vinci/Scrapling | Adaptive lightweight scraper for layout-changing sites | 1 |
| AutoScraper | alirezamika/autoscraper | Exemplar-based pattern extraction (zero-config) | 1 |
| Scrapy | scrapy/scrapy | Enterprise spider framework for scheduled bulk pipelines | 2 |
| Crawl4AI | unclecode/crawl4ai | LLM/RAG-optimized crawler with chunking | 2 |
| Crawlee | apify/crawlee | JS/TS crawler framework with proxy rotation | 2 |
| Firecrawl | firecrawl/firecrawl | Cloud API: web → Markdown/JSON/structured | 3 |
| Browser Use | browser-use/browser-use | Agentic browser control (click, type, login) | 4 |
| scrcpy | Genymobile/scrcpy | Android screen mirror + ADB automation | 4 |

### Device constraints
| Device | RAM | GUI | Can run |
|--------|-----|-----|---------|
| **RPi 5** (Hermes 24/7) | 8GB shared w/ Umbrel | headless | Tier 0-1 + Firecrawl API + Scrapy |
| **MacBook** (Claude Code) | 16-32GB | yes | All tiers including Browser Use + scrcpy |
| **Work PC** (Codex/Cursor) | varied | yes | Most tiers (scrcpy needs ADB+Android) |

### Iron Laws that apply
- **#7 Source provenance — raw/ first, always**: every scraper output MUST be saved to `raw/<slug>.<ext>` BEFORE creating `wiki/sources/<slug>.md`. Hook `check_source_original_file.py` enforces this.
- **Cost-First Pyramid**: start at Tier 0 (free local), escalate only when needed.
- **raw/ is immutable**: hook-protected, never edit scraped raw files.

---

## Architecture — Data Flow

```
┌─ URL ─────────────────────────────────────────────────────────────┐
│  scrape-advanced.py OR ingest-source.py --url                     │
│    Tier 0: curl-impersonate (TLS fingerprint)                     │
│    Tier 1: Scrapling (dynamic page, no browser)                   │
│    Tier 2: Crawl4AI / Scrapy (bulk, RAG chunking)                 │
│    Tier 3: Firecrawl API (cloud render, remote)                   │
│    Tier 4: Browser Use (agentic, MacBook only)                    │
│         ↓                                                          │
│  raw/<slug>.md  (Iron Law #7 — provenance mandatory)              │
│         ↓                                                          │
│  ingest-source.py → wiki/sources/<slug>.md (original_file: raw/…) │
└────────────────────────────────────────────────────────────────────┘

┌─ Local binary file (.pdf/.docx/.xlsx/.pptx/.epub/.html) ──────────┐
│  ingest-source.py --file <path>                                   │
│    MarkItDown → convert to Markdown                                │
│         ↓                                                          │
│  raw/<slug>.md  (save converted MD; keep binary gitignored)       │
│         ↓                                                          │
│  wiki/sources/<slug>.md (original_file: raw/<slug>.md)            │
└────────────────────────────────────────────────────────────────────┘

┌─ Pharmacy pipeline (scheduled) ───────────────────────────────────┐
│  scrape-pharmacy.py (cron on Pi5)                                 │
│    Scrapy/Scrapling → drug catalog HTML → raw/pharmacy/            │
│    AutoScraper → extract structured drug list                      │
│    diff vs existing drugs.db → update alt-source-items.json        │
│    build_pharmacy_db.py → rebuild drugs.db                         │
│         ↓                                                          │
│  pharmacy_lookup.py — now matches new drugs automatically          │
│                                                                   │
│  not_found resolver:                                              │
│    pharmacy_lookup.py "not_found" queue                           │
│    → AutoScraper/Firecrawl web search for each item                │
│    → verify → add to alt-source-items.json → rebuild               │
└────────────────────────────────────────────────────────────────────┘
```

---

## Phase Breakdown (ordered, each phase = commit-ready chunk)

### Phase 1 — Core Pipeline Enhancement (Tier 0)
**Files**: `scripts/wiki/ingest-source.py`, `requirements-optional.txt`, `scripts/setup-local.sh`

- [ ] **P1.1** Add `markitdown` + `curl-impersonate` to `requirements-optional.txt`
- [ ] **P1.2** Upgrade `extract_text_from_url()` in `ingest-source.py`:
  - Try `curl-impersonate` binary first (TLS fingerprint: chrome)
  - Fallback to existing `curl -sL`
  - If both fail with HTTP 403/429 → print suggestion: `python3 scripts/wiki/scrape-advanced.py --url <url>`
- [ ] **P1.3** Upgrade `extract_text_from_file()` in `ingest-source.py`:
  - Detect extension: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.epub`, `.html`, `.csv`
  - If binary/office → call MarkItDown to convert → save output to `raw/<slug>.md`
  - Keep original binary in `raw/<slug>.<ext>` (gitignored via existing rules)
  - Set `original_file: raw/<slug>.md` in frontmatter (passes hook check)
  - If MarkItDown not installed → warning + fallback to existing plaintext read
- [ ] **P1.4** Add `SCRAPER_INSTALL=1` optional flag to `scripts/setup-local.sh` (pip install markitdown + curl-impersonate wrapper)
- [ ] **P1.5** Test: `python3 scripts/wiki/ingest-source.py --file <test.pdf> --domain ai-tools` → verify raw/ MD created + source page created
- [ ] **Commit**: `feat(ingest): add MarkItDown binary conversion + curl-impersonate TLS fetch [next: P2]`

### Phase 2 — Multi-Tier Scraper Router (Tier 1-3)
**Files**: `scripts/wiki/scrape-advanced.py` (NEW), `tests/test_scrape_advanced.py` (NEW)

- [ ] **P2.1** Create `scripts/wiki/scrape-advanced.py` with CLI:
  ```
  python3 scripts/wiki/scrape-advanced.py --url <url> [--method auto|scrapling|autoscraper|crawl4ai|firecrawl|browser-use]
                                           [--save-raw raw/<slug>.md] [--domain <domain>]
                                           [--fallback] [--wizard] [--list] [--json]
  ```
- [ ] **P2.2** Implement method dispatch with graceful degradation:
  - `--list`: scan installed deps, print available methods + device tier
  - Each method wrapped in try/except ImportError → skip + try next
  - Device-detect: if `~/.wiki-device == "pi5"` or no display server → block browser-use/crawl4ai-browser → route to firecrawl
- [ ] **P2.3** Implement adapters (each in its own function):
  - `_scrape_scrapling(url)`: `from scrapling import ...` — adaptive fetch
  - `_scrape_autoscraper(url, wanted_list)`: `from autoscraper import AutoScraper` — exemplar mode (`--wizard` prompts for example items)
  - `_scrape_crawl4ai(url)`: `from crawl4ai import ...` — RAG chunking output
  - `_scrape_firecrawl(url)`: API call to `https://api.firecrawl.dev/v1/scrape` using key from `drive_secrets.fetch_secret("FIRECRAWL_API_KEY")`
  - `_scrape_browser_use(url, task)`: `from browser_use import ...` — agentic, MacBook only
- [ ] **P2.4** All adapters MUST save raw output to `raw/<slug>.md` before returning (Iron Law #7)
- [ ] **P2.5** Integrate `scripts/lib/drive_secrets.py` for FIRECRAWL_API_KEY
- [ ] **P2.6** Add `--json` output mode for agent consumption (compact JSON, not verbose HTML)
- [ ] **P2.7** Write `tests/test_scrape_advanced.py`: test each adapter with mock, test missing-dep graceful degradation, test device-detect Pi5 blocking
- [ ] **Commit**: `feat(scrape): add multi-tier scraper router with 5 adapters [next: P3]`

### Phase 3 — Pharmacy Pipeline
**Files**: `scripts/wiki/scrape-pharmacy.py` (NEW), updates to `scripts/pharmacy_lookup.py`, `scripts/build_pharmacy_db.py`

- [ ] **P3.1** Create `scripts/wiki/scrape-pharmacy.py`:
  - `--catalog <url>`: scrape supplier drug catalog → `raw/pharmacy/catalog-<date>.json`
  - `--resolve-not-found`: read last `order-history.json` not_found items → AutoScraper/Firecrawl search → verify → append to `alternative-source-items.json`
  - `--diff`: compare new catalog vs existing drugs.db → report new/changed items
  - `--rebuild`: call `build_pharmacy_db.py` after update
- [ ] **P3.2** Add `--queue-not-found` flag to `pharmacy_lookup.py`: when not_found items detected, write them to `wiki/entities/pharmacy/pending-search.json` for batch resolution
- [ ] **P3.3** Design cron entry for Pi5 (document in `docs/runbooks/hermes-multi-device.md`):
  ```
  # Weekly drug catalog refresh (Sunday 3 AM)
  0 3 * * 0 cd /path/to/A-Wiki && python3 scripts/wiki/scrape-pharmacy.py --catalog <supplier-url> --diff --rebuild
  ```
- [ ] **P3.4** Privacy: supplier URLs and any session cookies stored in `drive/.secrets` (PHARMACY_SUPPLIER_URL, PHARMACY_SESSION_COOKIE) — never in repo
- [ ] **P3.5** Test: mock catalog HTML → verify alt-source-items.json updated → verify drugs.db rebuilt → verify pharmacy_lookup now matches new drug
- [ ] **Commit**: `feat(pharmacy): add scheduled catalog scraper + not_found auto-resolver [next: P4]`

### Phase 4 — Agentic Browser + Mobile (Tier 4, MacBook only)
**Files**: `skills/claude-code/browser-automation/SKILL.md` (NEW)

- [ ] **P4.1** Create `skills/claude-code/browser-automation/SKILL.md`:
  - **Browser Use section**: install (`pip install browser-use`), usage pattern, when to use (login-required sites, multi-step forms, CAPTCHA)
  - **scrcpy section**: install, ADB setup, usage (screenshot → OCR via existing Claude Vision, tap/swipe via ADB)
  - Device guard: "ONLY on workstation with display (MacBook). Blocked on Pi5/headless."
- [ ] **P4.2** Document integration with `scrape-advanced.py --method browser-use`
- [ ] **P4.3** Privacy rules: login credentials from `drive/.secrets` only; screenshots saved to `raw/browser-captures/` (gitignored); never store session cookies in repo
- [ ] **P4.4** Crawlee (JS/TS): document as alternative for Node.js-heavy teams — optional, install via `npm install crawlee` — wrap in `scrape-advanced.py --method crawlee` (subprocess call to JS script)
- [ ] **Commit**: `docs(skills): add browser-automation skill (Browser Use + scrcpy) [next: P5]`

### Phase 5 — Multi-Agent Wiring + Skills + Commands
**Files**: skills updates, `.kilo/command/awiki-scrape.md` (NEW), Hermes config

- [ ] **P5.1** Update `skills/wiki/ingest-source/SKILL.md`: add Step 0.5 — "if URL fails with 403/JS-rendered → use `scrape-advanced.py`"
- [ ] **P5.2** Update `skills/claude-code/ingest-source/SKILL.md`: add binary-file conversion note + scrape-advanced.py pointer
- [ ] **P5.3** Create `skills/wiki/scrape-web/SKILL.md` (model-agnostic):
  - Decision flowchart: URL type → recommended method → device constraint
  - When to use each tier
  - raw/ provenance reminder
- [ ] **P5.4** Create `.kilo/command/awiki-scrape.md`:
  ```
  --- 
  description: Scrape a URL or convert a file for wiki ingestion (multi-tier router)
  ---
  !`python3 scripts/wiki/scrape-advanced.py "$ARGUMENTS" --json`
  ```
- [ ] **P5.5** Hermes Telegram commands (document in `docs/runbooks/hermes-multi-device.md`):
  - `/scrape <url> [method]` — scrape single page
  - `/crawl <url> [domain]` — crawl site for RAG (routes to Crawl4AI/Firecrawl)
  - `/pharmacy_update` — trigger pharmacy catalog refresh
  - `/drug_search <name>` — existing pharmacy_lookup wrapper
- [ ] **P5.6** Update `wiki/context/cost-routing.conf`: add scraper tiers (Tier 0-4 mapping)
- [ ] **P5.7** Update AGENTS.md Scripts Index table: add scrape-advanced.py, scrape-pharmacy.py entries
- [ ] **Commit**: `feat(wiring): multi-agent scrape commands + skill updates [next: P6]`

### Phase 6 — Tests, Validation, Privacy Audit
**Files**: `tests/` extensions, `scripts/check-privacy.py` updates

- [ ] **P6.1** Extend `tests/test_ingest_source.py`: test binary file conversion (mock MarkItDown), test curl-impersonate fallback
- [ ] **P6.2** `tests/test_scrape_advanced.py`: full coverage — each adapter, missing-dep fallback, device-detect, raw/ save verification
- [ ] **P6.3** Privacy audit: `python3 scripts/check-privacy.py` — verify no API keys, session cookies, or personal paths leak into tracked files; all secrets via `drive/.secrets`
- [ ] **P6.4** Cross-platform smoke test: `python3 scripts/verify-cross-platform.py` — confirm scrape-advanced.py imports cleanly on macOS/Linux; graceful degradation when deps missing
- [ ] **P6.5** End-to-end validation:
  - `python3 scripts/wiki/scrape-advanced.py --list` → shows available methods per device
  - Scrape a simple test page → verify `raw/` file created → verify hook passes
  - `python3 scripts/wiki/ingest-source.py --file <test.pdf>` → verify MarkItDown conversion → source page created
- [ ] **P6.6** Update `wiki/context/session-memory.md` with USIL completion entry
- [ ] **Commit**: `test(usil): full validation + privacy audit — USIL complete`

---

## Tool-to-Tier Mapping (final)

| Tier | Tool | Where | Install | Cost |
|------|------|-------|---------|------|
| 0 | MarkItDown | All devices | pip (light, no browser) | Free |
| 0 | curl-impersonate | All devices | binary (light) | Free |
| 1 | Scrapling | All devices | pip (light, no browser) | Free |
| 1 | AutoScraper | All devices | pip (light) | Free |
| 2 | Scrapy | Pi5+ (cron) | pip (medium) | Free |
| 2 | Crawl4AI | MacBook only | pip+playwright (heavy) | Free |
| 2 | Crawlee | MacBook only | npm (heavy, optional) | Free |
| 3 | Firecrawl API | All devices | pip + API key | Paid (credits) |
| 4 | Browser Use | MacBook only | pip+playwright (heavy) | Free |
| 4 | scrcpy | MacBook+Android | binary+adb | Free |

---

## Failure Modes & Graceful Degradation

| Failure | Behavior |
|---------|----------|
| curl-impersonate not installed | Fallback to existing `curl -sL` |
| MarkItDown not installed | Warning + keep binary in raw/, skip conversion |
| Scrapling/AutoScraper not installed | Skip tier, try next method |
| Browser Use on Pi5/headless | Device-detect blocks → route to Firecrawl API |
| Firecrawl API key missing | Skip method, suggest `echo FIRECRAWL_API_KEY >> drive/.secrets` |
| Target site blocks all methods | Save partial content + report "extraction incomplete" |
| Playwright/Chromium not installed | Crawl4AI/Browser Use adapters report ImportError → degrade |

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Privacy leak**: Browser Use/scrcpy captures login sessions | HIGH | Credentials/cookies from `drive/.secrets` only; screenshots to gitignored `raw/browser-captures/`; `check-privacy.py` audit |
| **Pi5 instability**: heavy scraper crashes Hermes | HIGH | Device-detect blocks browser tools; subprocess isolation with memory limit in scrape-advanced.py |
| **Firecrawl cost overrun**: API credits exhausted | MEDIUM | Rate-limit in adapter (max 50/day default); cache raw/ results; Tier 0-1 first always |
| **Iron Law #7 violation**: scraper writes source page directly | HIGH | scrape-advanced.py ALWAYS writes raw/ first; never writes to wiki/sources/ (that's ingest-source.py's job) |
| **Dependency bloat**: all tools force-installed | MEDIUM | All heavy deps in `requirements-optional.txt` (not base requirements.txt); `SCRAPER_INSTALL=1` opt-in flag |
| **Supplier TOS violation**: scraping protected catalog | LOW | Rate-limit; respect robots.txt; user-configured URLs from drive/.secrets only |

---

## Validation Plan

```bash
# 1. Core pipeline (Tier 0)
python3 scripts/wiki/ingest-source.py --file test.pdf --domain ai-tools
# Expect: raw/test.md created, wiki/sources/ai-tools/test.md created

# 2. Scraper router
python3 scripts/wiki/scrape-advanced.py --list
# Expect: shows available methods + device tier

python3 scripts/wiki/scrape-advanced.py --url https://example.com --json
# Expect: raw/ file created, JSON summary to stdout

# 3. Pharmacy pipeline
python3 scripts/wiki/scrape-pharmacy.py --diff --dry-run
# Expect: reports what would change without writing

# 4. Privacy
python3 scripts/check-privacy.py
# Expect: no secrets/API keys in tracked files

# 5. Tests
python3 -m pytest tests/test_scrape_advanced.py tests/test_ingest_source.py -v
# Expect: all pass

# 6. Cross-platform
python3 scripts/verify-cross-platform.py
# Expect: clean import on macOS + Linux
```

---

## Open Questions (resolved during implementation)

1. **Supplier catalog URL for pharmacy scraping**: must come from `drive/.secrets` (PHARMACY_SUPPLIER_URL) — implementation agent should leave a placeholder + config doc if user hasn't set it yet.
2. **Firecrawl free tier limits**: check current limits at implementation time (API docs); set conservative default rate-limit.
3. **Crawlee integration**: optional (P4.4) — only if user needs JS/TS scraping; otherwise defer to Crawl4AI which covers same use cases in Python.
4. **Browser Use model config**: needs an LLM backend (default: Claude API or OpenRouter free) — document in SKILL.md, let user configure via existing model router.

---

## Out of Scope

- **Scrapy spider projects**: full spider codebases for specific sites — user/agent creates these on-demand per target site; this plan only provides the framework integration.
- **Vector embeddings**: Crawl4AI has embedding features but A-Wiki's vector search is a separate future project (per `docs/protocols/ai-engineering-ingest-roadmap.md` which deferred sqlite-vec).
- **Real-time monitoring scrapers**: not covered — this is batch/trigger-based ingestion only.
