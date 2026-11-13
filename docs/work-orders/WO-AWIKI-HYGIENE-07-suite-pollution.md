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

## Implementation (2026-11-13)

- RED: tests/test_repo_hygiene.py guard — fresh worktree at HEAD runs the two
  offenders, asserts porcelain-clean (by design it evaluates HEAD, so it
  stays RED until the fixes are committed)
- fix 1: skills_service test restores skills-registry.json byte-exact
  (read_bytes/write_bytes) instead of re-dumping JSON
- fix 2: user_journey_e2e autouse _no_generated_pollution fixture —
  porcelain-diff restore: only paths changed during the test are reverted
  (checkout for tracked-that-were-clean, delete for new untracked);
  pre-existing dev dirty state never touched

## Review round 1 — Terra BLOCK → redesign (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt1.txt (2×P1 + 1×P2, all confirmed)

- P1 F1 fixture compared whole porcelain LINES → could discard dev unstaged
  edits (M→MM seen as new) and could NOT recover dev bytes a generator had
  overwritten (line unchanged M→M) → redesigned: _git_status_z() parses
  `status --porcelain -z -uall` (no C-quoting, per-file untracked, rename
  originals captured) and snapshots BYTES of every non-clean path; restore
  writes back byte-exact (recovers overwritten dev edits), new paths only
  are reverted (tracked → git checkout, untracked → unlink); _tracked_files
  distinguishes them; every git call checked, never silent
- P1 F2 guard accepted rc=1 (false-green: failures before reaching the
  pollution vector) → offenders must PASS (rc==0) in the fresh worktree;
  git status returncode now checked
- P2 F3 silent parser/cleanup failures → covered by the -z parser + checked
  returncodes + check=True on checkout

Evidence: test_user_journey_e2e 38 passed 1 skipped with the new fixture;
main clone porcelain-clean after the run (0 lines)
