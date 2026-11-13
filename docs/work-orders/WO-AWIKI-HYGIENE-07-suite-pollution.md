# WO-AWIKI-HYGIENE-07 — full-suite repo pollution: root causes + hermetic fixes

Branch: feat/suite-hygiene · Agent: GLM (Kilo) · Opened: 2026-11-13
Base: 05931fbf (main, PR #85 merged)

## Defect (reproduced deterministically)

A full pytest run leaves the checkout dirty (19 generated files). Root-cause
hunt in a throwaway worktree at 05931fbf (timed -v log + per-file bisect):

1. `tests/test_skills_service.py::test_update_skill_field_writes_and_restores`
   writes the REAL skills-registry.json, then "restores" by re-dumping JSON
   with its own serialization → bytes differ from the tracked file → permanent
   `M skills-registry.json`. (mtime 18:58:31)
2. `tests/test_user_journey_e2e.py` presses the destructive MCP button
   `wiki_regen_index` (line ~338) with cwd=REPO_ROOT; the tool spawns
   gen-index.py for real → writes .wiki-graph.json, brain-map.canvas,
   skills-registry.json, wiki/context/*, wiki/entities/*/CLAUDE.md,
   wiki/concepts/iot/CLAUDE.md, wiki/sources/CLAUDE.md (18 files).
   The test's own docstring says destructive buttons must be pressed
   " politely refused" — the assertion accepts a real successful regen too.
   (mtime 18:58:40)

Single-file runs of both reproduce their pollution; the earlier PR #84
round-3 incident (wiki/sources/article*.md) did NOT reproduce at 05931fbf —
that vector was already closed by the PR #84/#85 hermetic e2e work.

## Fix plan (code decision, no Jev needed — mechanical hermeticity)

1. skills_service test: restore byte-exact — snapshot read_bytes() before,
   write_bytes(saved) in finally
2. user_journey_e2e: autouse fixture `_no_generated_pollution` — snapshot
   `git status --porcelain` before; after the test, restore ONLY what changed
   since the snapshot (git checkout -- for tracked files that were clean at
   start; delete untracked files that appeared). Developer dirty state that
   existed before the run is never touched
3. NEW tests/test_repo_hygiene.py — RED first: creates a git worktree at
   HEAD in tmp, runs the two offender files as a subprocess pytest, asserts
   `git status --porcelain` is empty. Guards the whole class of pollution

## Checkpoints

- [x] Claim row WO-AWIKI-HYGIENE-07 (RECONCILED)
- [x] TITLE-06 DONE marker (this docs commit)
