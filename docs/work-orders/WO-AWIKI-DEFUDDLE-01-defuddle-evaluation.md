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
