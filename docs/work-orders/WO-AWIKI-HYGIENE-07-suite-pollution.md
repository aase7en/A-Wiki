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

## Review round 2 — Terra BLOCK → snapshot semantics completed (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt2.txt (2×P1 + 2×P2)

- P1 F1 ls-files could C-quote special names → membership wrong → tracked
  file deleted instead of checkout → `git ls-files -z`; untracked deletion
  now confined to known generator surfaces (wiki/, raw/, exports/, .tmp/,
  .wiki-graph.json, brain-map.canvas, skills-registry.json); tracked files
  changed mid-test are reverted tree-wide (r4 doc correction, matches the
  fixture docstring); concurrency limitation documented in the fixture
  docstring
- P1 F2 snapshot lost "file deliberately deleted" state and symlink-ness →
  _snapshot_entry returns (file|symlink|absent); restore re-creates exact
  state incl. keeping deletions deleted and symlinks as links
- P2 F3 parser now checks BOTH status columns for R/C, validates record
  shape, fails loud on malformed input
- P2 F4 guard's worktree cleanup checks rc, prunes, rmtree fallback

Evidence: test_user_journey_e2e 39 passed + guard GREEN at new HEAD below

## Round 2 residual — guard scope precision (2026-11-13)

Whole-file rc==0 made the guard depend on FTS assertions that need
.wiki-index.db (gitignored; present in CI via workflow build, absent in a
fresh worktree) — failure at test_user_journey_e2e.py:265, unrelated to
pollution. Guard now targets exactly the pollution vectors: full
test_skills_service.py + TestJourney2bMcpButtons (the class pressing
wiki_regen_index for real). rc==0 remains required for those targets.

Evidence: tests/test_repo_hygiene.py 2 passed (9.8s)

## Review round 3 — Terra BLOCK → mode/visibility/malformed completes (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt3.txt

- P1 F1 restore lost file mode → snapshot keeps st_mode & 0o7777, restore
  chmods after rewrite
- P2 F2 guard cleanup could pass silently → cleanup_ok asserted post-finally
  (worktree dir must be gone)
- P2 F3 R/C record missing original path now raises (malformed = loud)
- P2 F4 concurrency docstring now matches behavior (tracked rolled back
  tree-wide; untracked deleted only in generator surfaces)

Evidence: user_journey + hygiene guard + skills_service → 115 passed,
1 skipped; main clone porcelain-clean after run

## Review round 4 — Terra BLOCK → final residuals (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt4.txt

- P1 F1 mode-only change (bytes equal) was not restored → restore condition
  now compares current st_mode too, chmods whenever either differs
- P2 F2 registration could outlive cleanup → rmtree BEFORE prune, then the
  guard verifies the path is absent from `git worktree list --porcelain`
- P2 F3 WO round-2 sentence now matches fixture behavior (tracked reverted
  tree-wide; untracked deletion surface-scoped)

Evidence: hygiene guard 2 passed; trio (user_journey + guard + skills_service)
115 passed / 1 skipped at round-3 commit; main clone clean after every run

## Review round 5 — Terra BLOCK → one residual (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt5.txt

- P2 listing could fail with empty stdout → false pass; substring match
  fragile → returncode checked; registration compared against structured
  `worktree <path>` entry lines

Evidence: guard 2 passed

## Review round 6 — Terra BLOCK → last residual (2026-11-13)

Receipt: /tmp/awiki-rev86-terra-receipt6.txt

- P2 quoted-path fragility in worktree list → verified empirically that
  paths are NOT C-quoted (space/paren worktree printed raw) but `-z` IS
  supported (NUL-terminated, xxd-verified) → listing now uses
  --porcelain -z, Path.resolve() comparison on both sides

Evidence: guard 2 passed
