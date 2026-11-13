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

## Implementation (2026-11-13)

- RED: 3 tests (template carries the token not a list; render expands from
  generated with sentinel paths; missing generated → RuntimeError with the
  regen hint) — all failed against the unfixed tree
- template: 22 hardcoded lines → single "__SKILLS_PATHS__" element
  (__DRIVE_SKILLS__ stays last); still strict JSON
- render_kilo_config: _expand_skills_paths() runs before path-token
  resolution — reads generated/kilo.skills-paths.json, maps ./x →
  __REPO_ROOT__/x so the existing token machinery resolves absolutes;
  fails loud when the generated file is absent

Evidence: render suite 16/16; related suite 96/96; end-to-end render on
the real template+registry → 23 paths incl. skills/awiki and the Drive
entry last; regen --check no drift

## Review round 1 — Terra BLOCK → token guard + sync self-check (2026-11-13)

Receipt: /tmp/awiki-rev88-terra-receipt1.txt (P1 + P2, both confirmed)

- P2 F2 __SKILLS_PATHS__ in any other position/string passed silently →
  _assert_no_placeholders now fails loud on the token ANYWHERE (element or
  embedded); two regressions (foreign field, embedded substring)
- P1 F1 cross-version hazard (new Drive template + old renderer on another
  machine renders an unresolved token silently): repo-level half closed —
  sync_template_repo_to_drive refuses to push a token template when THIS
  renderer lacks the expander (half-updated checkouts cannot poison the
  shared Drive); cross-machine transition risk documented here and in the
  sync docstring: any machine rendering after this merge must pull main
  first; on updated machines a stuck token now fails loud instead of
  silently hiding skills

Evidence: render suite 18/18; related suite 98/98


## Round 2 residual — transition runbook (2026-11-13)

The remaining cross-machine risk CANNOT be closed by repo-side code
alone (old renderers by definition lack any new guard). Transition
measures shipped with this slice:
(a) updated machines fail LOUD on any unresolved token (assert)
(b) sync self-check: a half-updated checkout cannot push the token
    template to the shared Drive
(c) evidence trail: sync writes template-needs-renderer-token-v1 next
    to the Drive template, explaining the requirement to any machine
(d) POST-MERGE RUNBOOK (executed by GLM immediately after merge):
    1. Mac (primary renderer): git pull — fast-forward
    2. Windows (online, checkout behind): git pull --ff-only —
       does NOT touch the user's untracked files or the one modified
       tracked file (different path)
    3. Verify: render once on Mac; confirm no token in output
    Pi5/Hermes does not render desktop kilo configs (no
    render_kilo_config consumer) — not part of the blast radius.

## Review round 3 — Terra BLOCK → marker self-heals (2026-11-13)

Receipt: /tmp/awiki-rev88-terra-receipt3.txt — round-2 guards confirmed
(fail-loud verified in-memory, sync self-check verified); ONE P1: the
marker was written AFTER the template with no transaction — a partial
failure left the Drive with the token template and no marker, forever.

Fix: the marker is now written on EVERY sync run, BEFORE the
already-in-sync early return — any partial failure from a previous run is
self-healed by the next. Regression: simulate template-written-marker-
lost → next no-op sync recreates it.

Evidence: render suite 19/19; related suite 99/99
