# WO-AWIKI-DEFUDDLE-02 — Defuddle adapter in the scraper router (production integration)

Status: CLAIMED / IN_PROGRESS
Builds on: WO-AWIKI-DEFUDDLE-01 (merged PR #80 — verdict JUSTIFIED as optional extraction adapter).
Claim: WO-AWIKI-DEFUDDLE-02 | Agent: GLM (Kilo) | Branch: `feat/defuddle-integration` | Base: `origin/main@7d5304dd`
Decision support: Jev (TypeSafe System One) per operator instruction 2026-11-12 (key from drive secrets, used via env, never committed).

## Goal

Add `defuddle` as a first-class method in `scripts/wiki/scrape-advanced.py`:
- TIERS entry (devices: all; binary: npx; pinned `defuddle@0.19.6`)
- `_scrape_defuddle(url)` adapter: `npx -y defuddle@0.19.6 parse <url> -m -j` (list argv, timeout, JSON parse → return content Markdown per existing adapter contract)
- npx-missing → explicit error detail (not silent no_content); nonzero exit / no-content → None per contract; timeout handled
- Auto-order position decided with Jev judgment + code decision (recorded below)

## Allowed scope

- `scripts/wiki/scrape-advanced.py` (additive only — no changes to existing adapters/TIERS semantics)
- NEW `tests/test_scrape_defuddle.py` (RED-first, network-free: monkeypatch subprocess/shutil)
- THIS WO; COLLAB.md claim row + DEFUDDLE-01 done marker

Forbidden: ingest-source.py, requirements, registry/surfaces, other adapters.

## Test plan (RED first)

1. TIERS contains defuddle with pinned desc; ADAPTERS maps it.
2. Happy path: monkeypatched subprocess returns defuddle JSON → adapter returns content markdown.
3. npx missing (monkeypatch shutil.which→None) → RuntimeError "npx not found" (dispatch records error status with detail).
4. Nonzero exit with stderr → returns None (no_content path).
5. Timeout raised → propagates as handled error (dispatch status error).
6. Pinned version present in subprocess argv; timeout enforced; `-m -j` flags present.
7. Auto order: defuddle appears exactly once; position matches the Jev-informed decision constant.

## Jev decision record

(filled after the call — request payload + answers preserved verbatim)

## Jev decision record — 2026-11-12 (jev-1.14.0, request/response preserved verbatim)

Request state: pipeline goal (readable-Markdown wiki ingest; raw HTML saved for provenance
regardless), all 6 current tiers with concrete behaviors, defuddle candidate behavior, and the
key interaction (curl-impersonate returns non-empty raw HTML → auto STOPS → defuddle would never
run after it). Payload: `/tmp/jev-defuddle02-request.json` (reproduced in PR comment).

Answers:
- `best_position` (choice): **position_first** — probabilities first 0.84 / second 0.13 / late 0.01 / last 0.02, confidence 0.79
- `has_clear_best` (noul): 0.58 (trade-off hesitance present, but direction consistent with the choice)
- `blocked_pages_common` (noul): 0.28 → anti-bot pages are the exception, not the rule

Code decision (truth table): blocked_pages < 0.3 (no curl-first override) AND choice top = first
with a 0.84/0.13 gap → **defuddle inserted at TIERS index 0**, ahead of curl-impersonate. On
machines without npx the adapter raises an explicit `npx not found` error in milliseconds
(shutil.which probe, no subprocess), and auto mode falls through to curl-impersonate unchanged.

## Implementation checkpoint — 2026-11-12

- RED: 11/11 failed on missing tier/adapter. GREEN: **11/11** + existing suite updated
  (`test_returns_all_methods` 6→7 — consequential contract update, documented here) → **34/34**.
- REAL end-to-end smoke (actual npx + defuddle@0.19.6 through the actual adapter, Thai fixture
  from WO-AWIKI-DEFUDDLE-01): extracted 267 chars containing `เซ็นเซอร์วัดพีเอช` — True.
- Tests are network-free (subprocess + shutil.which patched); CI-safe without node.
