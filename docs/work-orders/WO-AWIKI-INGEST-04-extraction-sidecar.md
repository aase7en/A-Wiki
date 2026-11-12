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
