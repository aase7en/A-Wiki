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
