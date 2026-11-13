# WO-AWIKI-TITLE-06 — MarkItDown-absent: refuse-hard + filename-stem title

Branch: feat/markitdown-refuse · Agent: GLM (Kilo) · Opened: 2026-11-13
Base: debe6653 (main, PR #84 merged)

## Defect

When MarkItDown is absent (or conversion fails) for a binary/office file
(.pdf .docx .xlsx .pptx .epub .html), `extract_text_from_file` falls through
to `read_text(errors="replace")` → mojibake body, and `infer_title_from_content`
picks the first garbage line as the note title (e.g. `%PDF-1.7`). Junk enters
wiki/sources, FTS and the knowledge graph.

## Jev decision (jev-1.14.0, /tmp/jev-title06-{req,resp}.json, 2026-11-13)

- degraded_binary_policy: **refuse_hard 0.68** (heuristic_gate 0.31,
  proceed_degraded 0.01) — garbage bodies must never enter the wiki
- degraded_title_source: **filename_stem 1.00** (unanimous) for any
  non-converted fallback text

Code decision (fail-safe per truth table): refusal covers BOTH the
ImportError path and the conversion-Exception path (same defect class);
unknown-extension fallback text (non-BINARY_EXTS) ingests but takes its
title from the prettified filename stem, never from content inference.

## Plan

1. RED tests in tests/test_ingest_source.py (new class TestBinaryRefusal):
   absent-markitdown refusal, conversion-failure refusal, unknown-ext
   filename-stem title via CLI dry-run
2. `extract_text_from_file` → returns `(text, title_safe)`; raises new
   `BinaryUnavailableError` on the two binary failure paths; plain reads
   return title_safe=True, unknown-ext fallback returns title_safe=False
3. main(): catch → `error: … install: pip install markitdown` exit 1
   (before any raw write; dry-run prints the same refusal and exits 1);
   pass `--title or prettified stem` when not title_safe
4. GREEN trio; PR #85; terra review; merge; post-main verify

## Checkpoints

- [x] Claim row WO-AWIKI-TITLE-06 (cache_claim_id a941592246a8, RECONCILED)
- [x] SCRAPE-05 DONE marker (this docs commit)

## Implementation record (2026-11-13)

- RED 5 (TestBinaryRefusal) → GREEN 56/56 in test_ingest_source.py; trio green
- ingest-source.py: BinaryUnavailableError + prettify_stem; extract returns
  (text, title_safe); binary ImportError/convert-fail/empty-result all raise
  BEFORE any write; unknown-ext fallback flagged title_safe=False; main()
  exits 1 with install hint; effective_title from prettify_stem when unsafe
- Machine anomaly logged: sys.environ absent host-wide (os.environ intact;
  sys.executable fine) — CLI test merges env via os.environ

## Review round 1 — Terra BLOCK → repairs (2026-11-13)

Receipt: /tmp/awiki-rev85-terra-receipt1.txt (4×P2, all confirmed real)

- F1 missing-file return broke tuple contract → `return None, True`
- F2 degenerate stem ('---.dat' → '') re-enabled garbage inference →
  `prettify_stem(...) or "Untitled Source"`
- F3 raw-write failure surfaced as conversion refusal after possible partial
  write → write block isolated with warn-only OSError handling (binary itself
  still lands in raw/ via main's copy)
- F4 test strength → +7 tests: missing-file tuple, empty-conversion refusal,
  write-failure-is-not-refusal (monkeypatched write_text), writes-enabled
  refusal leaves no raw/, CLI slug for filename-stem title, explicit-title
  precedence, degenerate-stem → untitled-source; refusal asserts pinned to
  BinaryUnavailableError (no bare Exception)

Evidence: file 63/63; trio 124/124 (with real npx e2e)
