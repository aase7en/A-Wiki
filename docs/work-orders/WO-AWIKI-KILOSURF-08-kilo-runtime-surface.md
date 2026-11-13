# WO-AWIKI-KILOSURF-08 — .kilo/kilo.jsonc skills.paths synced from registry

Branch: feat/kilo-runtime-surface · Agent: GLM (Kilo) · Opened: 2026-11-13
Base: efa80a72 (main, PR #86 merged)

## Defect (AGENTS.md "Kilo template drift" known gap, root-caused today)

- generated/kilo.skills-paths.json (CI-checked) is CORRECT: 26 registry-derived
  paths incl. skills/awiki, skills/ecosystem, skills/anthropic-skills,
  skills/claude-thai
- BUT the runtime file Kilo actually reads — tracked .kilo/kilo.jsonc — carries
  a stale hand-frozen list of 8 old paths (incl. a ./skills/research entry that
  is not even in the registry) and misses the four known-gap categories
- Root cause: no generator owns .kilo/kilo.jsonc; kilo.jsonc.template
  (bundled + Drive) hardcodes paths, contradicting Iron Law #10 (registry is
  the single source of truth)

## Fix (registry→runtime closure)

1. NEW generator gen_kilo_runtime: renders .kilo/kilo.jsonc by loading the
   current file (pure JSON, verified no comments) and replacing ONLY
   skills.paths with gen_kilo._category_dirs(registry); fails loud if the
   file is missing
2. regen-skill-surfaces.py: ROOT_SURFACES mechanism for repo-root-relative
   output paths; gen_kilo_runtime wired into GENERATORS (regen writes it,
   CI --check guards drift both ways)
3. RED-first tests/test_kilo_surface.py: runtime paths must equal the
   registry-derived render

Known remaining (separate follow-up, NOT this slice): kilo.jsonc.template
(bundled + Drive) still hardcodes a path list for fresh-machine bootstrap;
low risk once runtime is regen-owned.

## Checkpoints

- [x] Claim row WO-AWIKI-KILOSURF-08
- [x] HYGIENE-07 DONE marker (this docs commit)

## Implementation (2026-11-13)

- RED: tests/test_kilo_surface.py 4 tests (equality with registry render,
  known-gap categories present, no non-dir entries, unrelated config
  preserved) — 3 failed against unfixed tree
- NEW gen_kilo_runtime.py: renders .kilo/kilo.jsonc from its current content,
  replaces ONLY skills.paths (fails loud if the tracked file is missing)
- regen-skill-surfaces.py: ROOT_SURFACES output class + generator wired
  (14 surfaces; --check guards both directions)
- Found-and-fixed adjacent bug: gen_kilo._category_dirs leaked single-file
  personas (agents/*.md) into skills-paths — now filtered to real skill
  category roots (skills/, agent-skills/); cross_agent_visibility test
  updated to enforce both directions

Evidence: kilo-surface 4/4; registry-related suite 249/249;
regen --check "No drift — 14 surface(s)"

## Review round 1 — Terra BLOCK → hardening (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt1.txt (P1 + 2×P2, all confirmed)

- P1 F1 concurrent overwrite + truncating write → write_atomic: stat_before
  taken BEFORE render reads; mtime+size guard refuses to overwrite a file
  that changed mid-render; temp+fsync+os.replace atomic replace; failure
  never truncates (test proves original bytes survive a failed replace)
- P2 F2 whole-file parse/reserialize could drift operator formatting →
  render is now a SURGICAL string replace of the paths array only; bytes
  outside it are preserved verbatim (test strips paths from both sides and
  asserts byte equality); --check can never report path-unrelated drift
- P2 F3 tests now pin the full contract: formatting preservation, missing
  skills block → RuntimeError, missing file → RuntimeError, concurrent
  modification → RuntimeError (deterministic render-spy, not Path.stat
  patching), failed replace leaves original untouched (stale-file setup
  forces the write path)

Evidence: kilo-surface 9/9; registry-related suite 253/253; --check no drift

## Review round 2 — Terra BLOCK → byte-level closure (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt2.txt (P1 + 3×P2, all confirmed)

- P1 F1 post-guard race → second TOCTOU guard immediately before
  os.replace; concurrency limitation documented (best-effort single-writer,
  microsecond stat→replace window, no cross-process lock)
- P2 F2 read_text newline-translation could rewrite CRLF outside the
  array → whole pipeline is BYTES now (read_bytes, bytes regex, byte
  writes); --check decodes only for the str-based timestamp normaliser;
  +CRLF-preservation test
- P2 F3 mkstemp 0600 replaced the 0644 config → chmod(original mode)
  before replace; +mode-preservation test
- P2 F4 regex could match a nested skills.paths → pattern anchored to the
  standard two-space top-level key indentation; nested-only shapes fail
  loud; +nested-rejection test

Evidence: kilo-surface 12/12; registry-related suite 257/257; --check no drift

## Review round 3 — Terra BLOCK → structural scanner (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt3.txt (P1 + 2×P2)

- P1 F1 indentation anchor provably spoofable (Terra demonstrated a nested
  skills.paths at two-space indent replacing the WRONG array while the
  top-level sanity still passed) → replaced regex entirely with a JSON
  depth-scanner (_locate_top_level_paths_span): full string/escape-aware
  brace/bracket depth tracking; only the array that is structurally the
  top-level skills.paths is located and replaced; +regression test using
  the exact shape Terra proved (nested decoy BEFORE the top-level key,
  top-level already registry-correct — decoy must survive byte-identical)
- P2 F2 formatting test only contained-CRLF → now byte-compares the exact
  same scanner-located span on both sides (prefix and suffix equal)
- P2 F3 docstring overstated the concurrency guarantee → rewritten as
  best-effort: mtime+size can miss same-size content edits and anything
  after the last stat; real serialization needs a lock, out of scope

Evidence: kilo-surface 13/13; registry-related suite 258/258; --check no
drift; regen rerun is a no-op on the synced file

## Review round 4 — Terra BLOCK → duplicate-key closure (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt4.txt (P1 + 2×P2)

- P1 F1 duplicate top-level `skills` (first operator-owned, last
  registry-matching) made the scanner replace the FIRST array while
  json.loads sanity blessed the LAST → scanner now scans to END of
  document after locating the span and rejects any second top-level
  skills key; duplicate `paths` keys inside the skills object likewise
  rejected after the span; +two regression tests using the exact
  proven shape
- P2 F2 decoy regression test now uses the EXACT two-space-indent shape
  Terra proved (hand-built string, not json.dumps which indents deeper)
- P2 F3 CRLF test now byte-compares prefix AND suffix of the
  scanner-located span on the CRLF fixture itself

Evidence: kilo-surface 15/15; registry-related suite 260/260; --check no drift

## Review round 5 — Terra BLOCK → JSON-exact escape decoding (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt5.txt (P1)

- P1 F1 unicode-escaped duplicate keys ("sk\u0069lls" / "pa\u0074hs") hid
  from the scanner while json.loads merged them → _read_string_at now
  decodes escapes EXACTLY like a JSON parser (\uXXXX incl. surrogate
  pairs, all simple escapes) before key comparison; +two escaped-duplicate
  regression tests (both levels)
- r5 note: decoy fixture now carries the FULL registry-derived list (was
  first-entry-only), matching its docstring's "already registry-correct"

Evidence: kilo-surface 15/15; registry-related suite 260/260; --check no drift

## Review round 6 — receipt reviewed a stale candidate (2026-11-13)

Receipt 6 answered against HEAD 674a3ed0 (round-4 commit) while the
worktree was 9ad86b6f — its two escaped-duplicate findings were HALF
right: the round-5 commit carried the escape-decoding fix but the two
regression tests were silently lost when an append script aborted on a
stale anchor (author error, disclosed). This commit restores both tests;
they pass against the escape-decoding scanner (17/17) and would fail
against the round-4 generator.

## Review round 7 — Terra BLOCK → one residual (2026-11-13)

Receipt 7 verified the correct SHA (41419225) and confirmed both
escaped-duplicate spoofs now raise at both levels. One P2 left: an
unpaired surrogate (\ud800) inside an operator-owned string elsewhere in
the file crashed chr().encode("utf-8") before the scanner reached skills
— json.loads accepts it. Fixed: encode("utf-8", "surrogatepass") (canonical
per codepoint, never matches compared keys) + regression test (render must
succeed with \ud800 present).

Evidence: kilo-surface 18/18; registry-related suite 263/263

## Review round 8 — Terra APPROVE (2026-11-13)

Receipt: /tmp/awiki-rev87-terra-receipt8.txt — VERDICT APPROVE, FINDINGS
none, verified SHA a144cffc. 8-round cycle: whole-file reserialize →
surgical regex → JSON depth-scanner → duplicate-key + unicode-escape +
surrogate closure; byte pipeline; guarded atomic write; 18 contract
tests. Merge authorized at a144cffc pending hosted CI.
