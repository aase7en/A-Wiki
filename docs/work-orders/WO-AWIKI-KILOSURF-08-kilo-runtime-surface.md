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
