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
