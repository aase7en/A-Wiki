# WO-AWIKI-SCRAPE-05 — Fix dead --save-raw flag (path-override semantics)

Status: CLAIMED / IN_PROGRESS
From: Phase A audit 2026-11-11 — `save_raw=not args.save_raw or True` always True; the
documented "Override raw output path" value was silently ignored.
Claim: WO-AWIKI-SCRAPE-05 | Agent: GLM (Kilo) | Branch: `feat/save-raw-fix` | Base: `origin/main@29dc5852`

## Jev decision record (jev-1.14.0, payload /tmp/jev-scrape05-req.json)

- `flag_semantics`: **path_override 0.59** (plus_opt_out 0.40, break_to_toggle 0.01)
- `raw_preservation_is_default`: 0.79 — always-on default favored.
Code decision: `--save-raw <path>` writes raw output to that exact path; default behavior
unchanged (always save to raw/<slug>.md). NO CLI opt-out (API-level save_raw=False remains
for programmatic callers). Sidecar note: with an override, the sidecar slug follows the
override stem.

## Scope
- scripts/wiki/scrape-advanced.py: save_raw_output(url, text, override=None); scrape()
  raw_path_override param; main() wiring replaces the dead expression.
- tests/test_scrape_advanced.py: additive class (override honored, default unchanged,
  scrape-level override, real-CLI e2e skipif-npx).
- THIS WO; COLLAB claim row + INGEST-04 done marker.

## Implementation checkpoint — 2026-11-13

- RED: 3 failures (override param missing) → GREEN: **58/58** across
  tests/test_scrape_advanced.py (27 incl. 4 new) + tests/test_scrape_defuddle.py (31).
- Real CLI e2e (actual npx + defuddle on committed fixture, --save-raw to custom path):
  file written at the override path containing the article marker.
- Dead expression `save_raw=not args.save_raw or True` removed; default always-save
  unchanged; sidecar follows override stem (documented).
