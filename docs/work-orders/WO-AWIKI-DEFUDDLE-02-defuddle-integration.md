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
