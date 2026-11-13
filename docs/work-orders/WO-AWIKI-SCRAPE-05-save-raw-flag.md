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

## Review status checkpoint — 2026-11-13 ~01:30

PR #84 open at candidate `de746fff`, CI pending. Independent review BLOCKED by
simultaneous rate limits: GPT-6.1-terra (OpenAI usage limit, resets 09:53 local
per receipt /tmp/awiki-rev84-terra-receipt.txt) AND session subagent quota.
Per process (no merge on author self-report): PR stays OPEN with evidence attached;
first action when either engine recovers = independent review → merge gates.
Not asking the operator: this is a rate-limit wait, not a decision.

## Review round 1 — Terra BLOCK → repairs (2026-11-13)

Receipt: /tmp/awiki-rev84-terra-receipt2.txt (VERDICT BLOCK; candidate cf71ec77)

- P1 sidecar/override clobber → new `_sidecar_path_for(slug, avoid)` diverts
  to `<slug>.original.html` when the sidecar path IS the override target;
  stale probe uses the same derived name. RED test test_r84_sidecar_diverts_when_override_is_sidecar_path
- P2 positional API regression → `raw_path_override` moved after `json_out`
  (keyword tail); historical 7-positional order restored. RED test
  test_r84_scrape_positional_compat_json_out_seventh
- P2 e2e cwd/network fragility → absolute fixture path, cwd=tmp_path,
  _looks_like_network_failure skip, checkout raw/ pollution guard (R84-T3)

Evidence: ~/awiki-venv/bin/python -m pytest tests/test_scrape_advanced.py
tests/test_scrape_defuddle.py tests/test_ingest_source.py -q → 111 passed
(e2e real run PASSED 0.78s, no skip)

## Review round 2 — Terra BLOCK → residual repairs (2026-11-13)

Receipt: /tmp/awiki-rev84-terra-receipt3.txt (repairs 1-2 confirmed fixed;
2 residual P2s on the e2e test)

- P2 r2-1 offline skip could never fire (adapter swallows npx stderr; broad
  markers) → replaced with an npx canary running the EXACT pinned parse
  command: canary ok ⇒ any CLI failure is a real defect and fails, not skips;
  _looks_like_network_failure removed
- P2 r2-2 sidecar anchored to checkout RAW_DIR; post-hoc guard unsound →
  module-level env seam AWIKI_RAW_DIR (R84-T4 RED→GREEN, fresh-spec module);
  e2e runs CLI with AWIKI_RAW_DIR=tmp — checkout pollution structurally
  impossible; stray duplicate CLI run removed

Evidence: pytest scrape trio → 112 passed (e2e PASSED, canary cached);
full local suite: 0 failures in scrape/ingest files (155 pre-existing
local-env failures in conductor/memory/review-bus suites, unchanged from
before this slice; hosted Core CI is the authority and was green at cf71ec77)

## Review round 3 — Terra BLOCK → pollution purge + hardening (2026-11-13)

Receipt: /tmp/awiki-rev84-terra-receipt4.txt

- P1 r3-1 test-run artifacts leaked into the candidate (round-2's blind
  `git add -A` after FULL local suite runs swept in wiki/sources/article*.md
  quoting fixture text as real knowledge + 20 generated files) → purged:
  article pages git-rm'd, all generated files restored to base; candidate
  diff is again exactly the 4 scope files. Root cause noted as backlog:
  pre-existing tests write into repo wiki/raw during full-suite runs
- P2 r3-2 env clobber → T4 now monkeypatch.setenv (restores runner value)
- P2 r3-3 canary hang → TimeoutExpired skips (availability, not defect)

Evidence: trio → 112 passed; `git diff --cached --stat 29dc5852` = 4 files
(COLLAB.md, WO doc, scrape-advanced.py, test_scrape_advanced.py)
