# WO-AWIKI-DEFUDDLE-01 — Defuddle extraction evaluation (isolated, no production dependency)

Status: CLAIMED / IN_PROGRESS
Parent goal: A-Wiki Knowledge Pipeline Modernization (Phase B — extraction evaluation).
Related: kepano/defuddle (MIT, v0.19.6 pinned); `docs/OBSIDIAN_SKILLS.md` claims defuddle usage at docs level only (no code integration exists — audit 2026-11-11).
Claim: WO-AWIKI-DEFUDDLE-01 | Agent: GLM (Kilo) | Branch: `feat/defuddle-evaluation` | Base: `origin/main@fe1484fa`
Worktree: isolated macOS clone (`~/GitHub/A-Wiki`).

## Goal

Evaluate Defuddle as an OPTIONAL extraction adapter for readable public HTML pages,
against the existing ingestion path, with pinned version in an isolated environment.
**No production dependency, no scraper-router change, no install into the repo env.**
Evaluation runs via `npx -y defuddle@0.19.6` (npx cache only — no global install).

## Allowed scope

- NEW `tests/fixtures/defuddle/article-noisy-en.html`, `article-noisy-thai.html`, `js-shell.html`
- THIS Work Order (+ COLLAB claim row; PIPE-01 done marker housekeeping)

Forbidden: `scripts/wiki/**` changes, requirements changes, registry/generated surfaces, any production wiring (a future WO would do RED-first adapter integration if justified).

## Methodology

Fixtures: (1) EN article + nav/sidebar/cookie/footer noise; (2) Thai article + same noise;
(3) JS-only shell (no static content). Per fixture run
`npx -y defuddle@0.19.6 parse <file> -m -j -l <en|th>` and record: exit code, extracted
title, content length, content-marker retention (unique body phrases), noise-marker
rejection (nav/sidebar/cookie/footer strings), Thai text integrity, empty-content behavior.

Baseline = existing default URL path (`scripts/wiki/ingest-source.py`): audit 2026-11-11
shows it saves the fetched response as `raw/<slug>.md` with NO article extraction —
noise retention is therefore 100% by construction; numbers come from the audit, not re-run here.

## Results

(appended after run)

## Results — 2026-11-11 (macOS clone, node v22.23.0, npx cached install, defuddle@0.19.6 pinned)

| Fixture | Exit | Title | Content | Noise rejected | Parse |
|---|---|---|---|---|---|
| article-noisy-en.html | ok | ✅ exact | ✅ 3/3 body paragraphs verbatim, wordCount 84 | ✅ nav/cookie/sidebar/footer: 0 occurrences in output | 21 ms |
| article-noisy-thai.html | ok | ✅ Thai exact | ✅ 2/2 Thai paragraphs verbatim, encoding intact | ✅ cookie banner "ยอมรับทั้งหมด"/sidebar/footer: 0 occurrences | 20 ms |
| js-shell.html | graceful error | — | — | — | — message: `Error: No content could be extracted` (explicit, no crash, no fabricated content) |

Baseline (existing default URL path, from audit — not re-run): fetched HTML saved as `raw/<slug>.md` with **no article extraction** → noise retention 100% by construction.

### Notes / limitations (honest)
- `-m -j` returns markdown as a JSON string field — pipeline-friendly; title is a separate field and is NOT duplicated into content (integration must compose frontmatter title + content itself).
- Thai `wordCount: 7` is unreliable (Thai lacks spaces) — never use as a Thai length metric; content-completeness verified by verbatim comparison instead.
- Local-file mode validated only; URL mode + real-world blocked/paywalled/JS-heavy sites NOT covered by this evaluation — the existing 5-tier scraper router (`scripts/wiki/scrape-advanced.py`) remains necessary; Defuddle would be an *additional readable-HTML extraction adapter*, not a replacement for Moli/Browser/Playwright.
- Exit-code capture for the js-shell case was piped through `head` (message is the evidence; code not reliably captured).

## Verdict — JUSTIFIED as optional extraction adapter (DO_INTEGRATE_IN_FUTURE_WO)

Defuddle v0.19.6 (MIT, zero-repo-install via npx, ms-fast, Thai+EN clean, fail-explicit)
clearly beats the current no-extraction baseline for readable public HTML. Recommended
next slice (separate claim, RED-first): add defuddle as an opt-in extraction tier/adapter
in the existing scraper router + compose `raw/` provenance (raw HTML preserved; cleaned
markdown marked as extraction, not archival copy). This WO adds NO production dependency.
