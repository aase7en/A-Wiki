# WO-AWIKI-INGEST-04 — Original-fetch sidecar when an extraction method wins

Status: CLAIMED / IN_PROGRESS
Builds on: WO-AWIKI-INGEST-03 (merged PR #82); maintainer concern from PR #81 review
("router saves the winning method's text — with defuddle first that is extracted
Markdown, not original HTML").
Claim: WO-AWIKI-INGEST-04 | Agent: GLM (Kilo) | Branch: `feat/defuddle-sidecar`
Base: `origin/main@95074b38` | Worktree: isolated macOS clone.

## Jev decision record (jev-1.14.0, 2026-11-12 — payload /tmp/jev-ingest04-req.json)

- `original_is_true_source` (noul): **0.90** — original fetch bytes are mandatory
  provenance for a citation-grade wiki.
- `storage_layout` (choice): **sidecar_html 0.53** vs extracted_subdir 0.43 (confidence
  0.3 — narrow). Code tie-breaker for sidecar: (1) Jev top choice, (2) zero migration —
  existing notes' original_file links keep working, (3) extracted_subdir would nest a
  second tree inside the immutable raw/ layer that the provenance hook validates.

## Design

In `scrape()` — after a winning method and BEFORE/Around save_raw_output:
- When `method_used == "defuddle"` (extraction) and save_raw is on, make a best-effort
  plain `curl -sL --max-time 20 <url>` fetch of the ORIGINAL page and save it as
  `raw/<slug>.html` (sidecar; slug shared with the .md). Best-effort: any failure is
  recorded in result["original_fetch"] = {status: ...} and never fails the scrape.
- result gains `original_fetch` evidence field; the .md remains the extraction
  provenance the note links via original_file.

## Allowed scope
- `scripts/wiki/scrape-advanced.py` — additive: `_save_original_sidecar()` + wiring in
  scrape() + result field. No changes to existing adapters/TIERS.
- `tests/test_scrape_defuddle.py` — additive sidecar test class (mocked subprocess).
- THIS WO; COLLAB.md claim row + WO-AWIKI-INGEST-03 done marker.

## Test plan (RED first)
1. defuddle win → sidecar .html written with original bytes (mocked curl).
2. curl failure → scrape still succeeds, original_fetch records the failure.
3. Non-defuddle win → NO sidecar written.
4. save_raw off → NO sidecar.
5. Sidecar path shares the slug of the .md.

## Continuity
Dual-engine review on the exact final SHA (GLM subagent + Terra codex exec read-only)
before any merge; hosted CI + post-main verification per established cycle.

## Implementation checkpoint — 2026-11-12 (Goal mode)

- RED: 4 failures → GREEN: test_scrape_defuddle.py + test_scrape_advanced.py = **44/44**.
- `_save_original_sidecar(url, slug)`: best-effort plain curl (list argv, 20s curl cap,
  30s subprocess timeout), never raises; wired in scrape() raw-save block only when
  `method_used == "defuddle"`; result gains `original_fetch: {status, path}` evidence.
- Sidecar slug = raw_path.stem — .md (extraction) and .html (original) share the slug.

## Terra (GPT-6.1-terra) review #1 — codex exec read-only receipt /tmp/awiki-rev83-terra-receipt.txt

VERDICT BLOCK — R83-1 (P1) sidecar mkdir/write outside try could abort a successful
scrape (OSError/decode); R83-2 (P1) `saved` claimed without HTTP-status check or
byte-for-byte guarantee; R83-3 (P2) stale same-slug sidecar may mislead after a
failed re-fetch; R83-4 (P2) negative/edge tests missing. (Terra's sandbox could not
run pytest — read-only no-temp-dir — recorded honestly; my own runs + hosted CI
carry the execution evidence.)

## Repairs #1 — R83-1..4

- R83-1: bytes-mode fetch, mkdir/write_bytes inside try-OSError → helper never
  raises; wiring additionally wrapped defensively.
- R83-2: curl `-f` (HTTP ≥ 400 → curl failure → unavailable, error pages never
  recorded as saved); bytes written byte-for-byte of THIS fetch; result note
  states explicitly "best-effort second fetch; not guaranteed identical to what
  the extractor consumed".
- R83-3: failed re-fetch flags `stale_sidecar_possible: true` when an old
  same-slug sidecar exists. Pre-existing same-slug collision across DIFFERENT
  urls (save_raw_output slugify) documented as a separate follow-up lane.
- R83-4: +6 tests — save_raw=False no sidecar, wiring survives OSError,
  curl timeout, HTTP error page not saved, stale flag, honest note.
GREEN: **50/50** (test_scrape_defuddle.py + test_scrape_advanced.py).
