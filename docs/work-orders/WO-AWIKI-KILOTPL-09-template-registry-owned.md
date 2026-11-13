# WO-AWIKI-KILOTPL-09 — kilo.jsonc.template paths from the registry

Branch: feat/kilo-template-registry · Agent: GLM (Kilo) · Opened: 2026-11-13
Base: efdce5c5 (main, PR #87 merged)

## Defect (last piece of the KILOSURF follow-up noted in WO-08)

KILOSURF-08 made regen own the runtime .kilo/kilo.jsonc skills.paths, but
the BOOTSTRAP path still hardcodes 22 path lines in
scripts/lib/kilo.jsonc.template (SSoT for fresh-machine renders; synced
repo→Drive automatically). The hardcoded list already drifted once in
history (2026-07-17: repo 22 vs Drive 8). Registry is the single source
of truth (Iron Law #10) — the template must not carry its own copy.

## Fix

1. Template: the 22 `__REPO_ROOT__/skills/...` lines become ONE
   `__SKILLS_PATHS__` token (the `__DRIVE_SKILLS__` entry stays as the
   final element)
2. render_kilo_config.render_config: load
   scripts/skills_registry/generated/kilo.skills-paths.json, map each
   "./x" to "<__REPO_ROOT__>/x" token strings, replace __SKILLS_PATHS__
   with the comma-joined quoted list; FAIL LOUD when the generated file
   is missing (message: run scripts/regen-skill-surfaces.py first)
3. RED-first tests: render derives paths from the generated file (a fake
   generated file with sentinel paths must surface them in the output);
   missing generated file → RuntimeError with the regen hint

Drive template keeps syncing repo→Drive unchanged (sync copies whatever
the repo template says — now one token).

## Checkpoints

- [x] Claim row WO-AWIKI-KILOTPL-09
- [x] KILOSURF-08 DONE marker (this docs commit)
