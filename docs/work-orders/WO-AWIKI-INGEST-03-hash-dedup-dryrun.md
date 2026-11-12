# WO-AWIKI-INGEST-03 — Ingestion hardening: content hash, duplicate detection, dry-run

Status: CLAIMED / IN_PROGRESS
From: Phase A audit 2026-11-11 ("ingest-source.py: no hash dedup, no --dry-run, no source_url frontmatter").
Claim: WO-AWIKI-INGEST-03 | Agent: GLM (Kilo) | Branch: `feat/ingest-hash-dedup` | Base: `origin/main@0ab8790b`

## Scope
- `scripts/wiki/ingest-source.py`: `content_sha256` (sha256 of raw fetched text) + `source_url`
  frontmatter fields; pre-write duplicate scan over `wiki/sources/**` frontmatter (pointer to the
  existing note, refuse new write); `--dry-run` flag covering BOTH note write and raw/ writes.
- `tests/test_ingest_source.py`: additive class (hash correctness, dedup hit/miss, grandfather
  notes without hash, dry-run writes nothing, source_url only for URLs).
- THIS WO; COLLAB row + DEFUDDLE-02 done marker.

Forbidden: scrape-advanced.py (dead --save-raw fix is a separate WO), provenance hook, templates.

## Policy (Jev-informed; record appended after call)
Hash match → refuse + pointer. Cross-domain duplicate policy: decided with Jev judgment + code table.

## Jev decision record — 2026-11-12 (jev-1.14.0)

Question: cross-domain hash-match policy (block_with_pointer / write_new_domain_note /
write_with_backlink) + companion noul (same content different purpose across domains).
Answers: choice split **write_with_backlink 0.41 vs block_with_pointer 0.37**
(confidence 0.11); noul **0.48** — the state does NOT settle the question.
Code decision (fail-safe branch per typesafe-ai skill "confidence is rarely the gate;
unsettled state → policy in code"): **block with pointer by default** + explicit
`--allow-duplicate` escape hatch which writes a `duplicate_of:` frontmatter marker
(borrowing write_with_backlink's visibility on the explicit path only).
Request/response preserved: /tmp/jev-ingest03-req.json, /tmp/jev-ingest03-resp.json
(reproduced in PR body).

## Implementation checkpoint — 2026-11-12

- RED: 6 genuine failures → GREEN **43/43** (tests/test_ingest_source.py).
- New: `_content_hash` (sha256 of raw text), `_find_hash_duplicate` (frontmatter-head
  scan, grandfather-safe), frontmatter fields `content_sha256` / `source_url` (URL
  only) / `duplicate_of` (allow-duplicate only), `--dry-run` (guards note write AND
  both raw/ writes in main()), `--allow-duplicate`.
- REAL CLI dry-run proof on a committed fixture: prints would-create/would-save lines;
  `git status` shows zero new files.
- Claim note: first claim attempt failed (comma in scope — strict reader), re-claimed
  comma-free (c3b2dfb9a51f) BEFORE any source mutation; the intermediate docs commit
  24d23905 contains WO+done-marker only.

## Review + repair cycle #1 — 2026-11-12 (second session, Goal mode)

Independent GLM review (fresh subagent, probes with DI + TemporaryDirectory): **BLOCK**, 4 findings:
- R82-1 (P1): --dry-run still wrote raw via extract_text_from_file's internal MarkItDown
  success write, and mkdir preceded the dry-run gate.
- R82-2 (P1): duplicate_of serialized str(Path) — machine-absolute path into public notes
  (test even pinned the unsafe form).
- R82-3 (P2): head-2000 substring scan matched body prose, prefixed keys, suffixed values.
- R82-4 (P2): fixed cutoff missed hashes emitted after long metadata BY OUR OWN WRITER.

Repairs: extract_text_from_file(write_raw=...) honored from main() (--dry-run → False);
mkdir moved after the dry-run gate; duplicate_of now SOURCES_DIR-relative posix
(never machine-absolute; regression asserts no leading "/"); _note_declares_hash parses the
real --- delimited frontmatter with exact key/value equality (body/prefix/suffix immune,
no cutoff). Tests: marker assertion rewritten portable; +mkdir guard, +write_raw honoring
(fake markitdown module), +legacy-body, +prefixed/suffixed, +late-hash, +no-directories.
GREEN: **87/87** across tests/test_ingest_source.py + tests/test_scrape_defuddle.py +
tests/test_scrape_advanced.py. GPT-6.1-terra (codex exec, read-only) re-review requested
per operator instruction (dual-engine verification).
