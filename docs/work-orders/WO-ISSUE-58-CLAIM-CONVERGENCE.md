# WO-ISSUE-58 — Claim authority convergence + canonical reader

Status: CANDIDATE_READY / REVIEW_REQUIRED
Issue: aase7en/A-Wiki#58
Risk: R3 — coordination authority, hooks, claim enforcement
Topology: CONTROL_PLANE_ONLY (A-Wiki upstream authority)

## Binding

- Repo: aase7en/A-Wiki
- Worktree: isolated consumer-local worktree; machine path intentionally omitted
- Branch: `fix/issue-58-claim-convergence`
- Base: `16897b2d34f3ff0de0938f7651cf19bbce106b43`
- Durable owner role: GPT integrator
- Durable claim: `Issue #58 claim authority convergence` COLLAB row
- Local TTL cache: derived same-machine lease; runtime identifier intentionally omitted
- Parent dependency: Conductor #551/#552 -> #549/#550

## Goal

Make durable COLLAB/Git claim identity the canonical repo/cross-machine truth,
with local TTL claims as a derived same-machine enforcement cache. Publish a
machine-readable claim reader that Conductor can bind to exact task IDs without
persisting machine-specific worktree paths.

## Brain Gate

- Gain: one claim authority plus exact machine-readable task binding.
- Shape: existing conductor adapter + claim hook + deterministic tests.
- Weight: reuse COLLAB/Git and the existing TTL cache; add no store/scheduler.
- Safety: public-safe identity only; no secrets/private/machine path in reader.
- Verify: RED/GREEN claim, hook, conductor, privacy/security and CI gates.

## Acceptance

1. Exact task reader returns claim_id, generation, agent, scope, branch and
   current branch HEAD from COLLAB/Git.
2. Reader requires exact task identity; no fuzzy inference for mutable binding.
3. `conductor claim` mirrors/refreshes the local TTL cache idempotently.
4. TTL expiry/release never deletes the durable COLLAB claim.
5. Foreign durable claim blocks shared-surface mutation even when TTL cache is
   empty/unreadable.
6. Local worktree path stays consumer-side; public claim evidence stores none.
7. Legacy callers remain compatible; no third claim/lease/receipt store.
8. Focused + related tests, privacy/security scan, independent R3 review and CI.

## Forbidden

- no new scheduler/task DB/claim store
- no WorkerLease semantic merge
- no direct main push
- no secret/private Drive content
- no reset/clean/stash/force operations


## Candidate evidence — 2026-09-27

- RED proof: 5 targeted contract tests failed before implementation.
- GREEN focused/related: 99/99 PASS across conductor, claim cache and hooks.
- Canonical reader CLI: PASS; emits `awiki-claim-reader/v1` with exact task,
  deterministic claim id, generation, scope, branch/head and consumer-side
  worktree verification requirement.
- Registry gate: PASS (30 hooks; 17 hard / 13 soft).
- Security scan: PASS (6361 tracked files; 51 baselined; 0 new findings).
- Wiki health: PASS (0 hard errors; advisories unchanged).
- py_compile: PASS for changed Python surfaces.
- `git diff --check`: PASS.
- No machine-local path is emitted by the reader; no private/secret file read.
- Remaining gates: freeze exact candidate SHA, independent R3 review, exact-head
  hosted CI, acceptance/merge, post-main verification, then release claim.


## Replacement hardening — 2026-09-27

Candidate `4eaa55d078c2abc9defa56a3a12ceefcd8aa4489` passed exact-head
hosted CI but is superseded before acceptance. A read-only pre-review audit found
that `scripts/hooks_runner.py` still exported a per-worktree
`AWIKI_CLAIMS_STORE`, overriding the new Git-common-dir default and therefore
preventing same-repository linked worktrees from sharing the derived TTL cache.

The repair preserves foreign/adopted-repo isolation while sharing one TTL cache
only when the workspace and A-Wiki brain resolve to the same Git common-dir.
Additional ABA/staleness hardening now requires:

- fetched `origin/<branch>` HEAD is preferred over a stale local branch ref;
- every durable generation advance rotates the derived cache claim id;
- a newer durable generation may transfer the cache owner;
- same-generation foreign takeover and older-generation replay are rejected;
- an old cache id cannot release a replacement generation.

RED evidence: linked-worktree runtime test failed before hook-runner repair; four
additional stale/ABA tests failed before generation/remote-head repair.

GREEN evidence after repair:
- related conductor/claim/hook/adopt/runtime suite: **292/292 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (0 new findings);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

The interrupted read-only review of the superseded SHA produced no acceptance
verdict and is not acceptance evidence. A fresh exact-SHA R3 review is required
for the replacement candidate.


## Foreign-repo authority isolation hardening — 2026-09-27

Candidate `993aefd4efb6933bf02f48fbf576a5f84aa77d46` is superseded before
acceptance. A direct read-only diagnostic proved that a foreign/adopted
workspace with no local durable authority could inherit the A-Wiki brain's
`COLLAB.md` claim and be blocked by an unrelated A-Wiki scope.

Root cause: `check_agent_claim.py` resolved durable claims and absolute file
paths against its own A-Wiki `REPO_ROOT`, ignoring the normalized hook
payload's `cwd`.

Repair contract:
- resolve the authority root from payload `cwd`, walking to the nearest
  repo-level `COLLAB.md` when one exists;
- a foreign workspace without `COLLAB.md` has no inherited A-Wiki durable
  claims;
- a foreign workspace with its own `COLLAB.md` enforces that repo's durable
  claims, including absolute file paths normalized relative to that workspace;
- local TTL collision receives the same workspace-relative path;
- explicit `AWIKI_DURABLE_CLAIMS_FILE` remains a deliberate override for
  tests/emergency use.

RED evidence: 2/2 new foreign-authority isolation tests failed before repair.
GREEN evidence after repair:
- `tests/test_check_agent_claim_hook.py`: **17/17 PASS**;
- direct foreign-no-COLLAB diagnostic: **PASS / rc 0** (no brain claim leak);
- related conductor/claim/hook/adopt/runtime suite: **294/294 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (0 new findings);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

A fresh exact-head R3 review and exact-head hosted CI are required for the
replacement candidate. Superseded/cancelled reviews are not acceptance
evidence.

## Nested workspace authority boundary hardening — 2026-09-27

Candidate `c88da14ace9b3963749074c2d7389f05e8caebce` is superseded before
acceptance. Adversarial read-only verification proved that a nested foreign Git
repository, or a nested non-Git workspace, could inherit a parent directory's
`COLLAB.md` because the durable-authority resolver walked upward by filesystem
parent rather than respecting repository boundaries.

Root cause: `_workspace_root()` treated the nearest ancestor containing
`COLLAB.md` as authority, even when payload `cwd` belonged to a distinct
nested Git repository.

Repair contract:
- resolve Git workspaces with `git rev-parse --show-toplevel`;
- that Git top-level is the hard authority boundary even if it has no
  `COLLAB.md`;
- non-Git workspaces remain isolated to their own `cwd`;
- never walk upward into an unrelated parent claim authority;
- linked A-Wiki worktrees continue to resolve to their own worktree Git
  top-level while the derived TTL cache sharing remains keyed by Git common-dir.

RED evidence: 2/2 nested-boundary regression tests failed before repair.
GREEN evidence after repair:
- `tests/test_check_agent_claim_hook.py`: **19/19 PASS**;
- related conductor/claim/hook/adopt/runtime pytest suite: **296/296 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (0 new findings);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

A fresh exact-head hosted CI and independent R3 review are required for the
replacement candidate. Earlier exact-SHA reviews/CI are superseded evidence.


## Canonical authority closure — durable-first MCP migration — 2026-09-27

After the workspace-boundary repair, recovery found the remaining ownership
ambiguity at the public claim entrypoints: legacy TTL-only rows could still look
like ownership to callers even though COLLAB/Git is now canonical.

The migration closes that seam:
- `claim_acquire` requires an exact `task_id` and writes durable COLLAB/Git
  ownership first, then mirrors a same-machine TTL cache row;
- direct legacy `agent_claims.acquire()` rows are typed
  `PARTIAL_UNRECONCILED` and are never ownership authority;
- only `RECONCILED` derived cache rows participate in collision blocking;
- durable-success/cache-failure is returned as typed
  `PARTIAL_UNRECONCILED` rather than minting a false cache owner;
- `claim_list`, `claim_release`, and `claim_advance` explicitly describe
  their derived-cache role; release/advance never release durable COLLAB/Git;
- MCP tests now use isolated COLLAB/Git fixtures and prove durable-first ordering;
- runtime/hook fixtures that require a hard block seed reconciled cache rows,
  while legacy TTL-only regression tests prove they do not block.

Focused regression after contract-drift fixture repair:
- hard-hook/runtime seam proof: **16/16 PASS**;
- full related conductor/claim/MCP/hook/adopt/runtime pytest surface:
  **320/320 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked / 51 baselined / 0 new);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS;
- added-line secret-signature scan: **0 hits**.

The previous exact-head CI on `6a4ebe7466e66644eee48ff2dbea64725ad9116f`
covered the boundary repair only and is superseded for acceptance. The final
migration candidate requires new exact-head hosted CI and a fresh independent
R3 review before merge.

## Canonical guidance + registry convergence — 2026-09-27

Candidate `d6e29253d3cd6fcdf070c074a86750dde9a99806` is superseded before
acceptance. Source/runtime behavior had converged on durable-first ownership,
but two canonical guidance surfaces still described the old same-machine TTL
model: AGENTS Iron Law #11 said cross-machine coordination was not covered, and
the canonical `a-claim` skill showed `claim_acquire` without an exact
`task_id` and treated `.tmp` lease state as the practical claim authority.

The documentation/registry repair keeps one authority model everywhere:
- `COLLAB.md + Git` is the canonical durable cross-machine ownership authority;
- MCP `claim_acquire` requires an exact `task_id`, writes/validates durable
  ownership first, then mirrors a derived same-machine TTL cache;
- `claim_list`, `claim_advance`, and `claim_release` are explicitly
  cache-side operations; cache expiry/release never releases durable ownership;
- only `RECONCILED` foreign cache rows may enforce same-machine collision;
  legacy/`PARTIAL_UNRECONCILED` rows are informational, never ownership;
- durable completion/release updates the same COLLAB row through reviewed Git;
- `a-claim` registry metadata/version advanced to **1.1.0** and generated
  surfaces were regenerated from the registry rather than hand-edited.

Verification after guidance convergence:
- claim/hook/MCP focused pytest subset: **277/277 PASS**;
- skill-registry/discovery pytest suite: **71/71 PASS**;
- registry validation: PASS;
- generated-surface check: **13/13 surfaces no drift**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked / 51 baselined / 0 new);
- wiki health: PASS (0 hard errors);
- `git diff --check`: PASS;
- added-line secret-signature scan: **0 hits**.

The earlier source candidate retained its stronger related source evidence
(**320/320 PASS**) but is not an acceptance SHA after this canonical guidance
change. A new frozen exact head requires fresh hosted CI and an independent R3
review.

## R3 adversarial replay repair — generation ABA + detached branch — 2026-09-27

Candidate `f03b3ff9ddc2281c6f9d037b2940456011322f37` is superseded before
acceptance. Fresh exact-head R3 review independently reran the focused suite
(277/277 PASS) and then found two trust-boundary defects by adversarial replay:

1. After a durable claim was committed, released in Git, and the same task was
   claimed again, `add_claim()` returned generation 1 while the canonical
   reader reported generation 2 after commit; the derived cache id therefore
   failed to rotate and could preserve ABA identity.
2. `_claim_branch()` rejected an empty branch only after considering a caller-
   supplied branch, so a detached HEAD could pass `branch="main"` and mint a
   durable claim bound to a branch the checkout was not actually on.

Repair:
- `claim_generation()` now counts committed task-row additions/replacements
  plus the current staged/unstaged task-row addition/replacement versus HEAD;
  this makes the generation correct before the mandatory claim commit and
  identical after commit;
- new durable claims mirror the computed generation instead of hard-coded 1;
- release -> reclaim rotates both generation and derived cache identity;
- `_claim_branch()` now requires a real current checkout branch first; an
  explicit branch may only equal that current branch and cannot bypass
  detached HEAD;
- the missing-COLLAB regression fixture now uses a real Git main checkout so
  it continues to test durable failure rather than failing at branch binding.

RED evidence: both new regressions failed before repair.
GREEN / verification after repair:
- ABA + detached-HEAD focused regressions: **2/2 PASS**;
- durable-failure fixture + both new regressions: **3/3 PASS**;
- related conductor/claim/MCP/hook/adopt/runtime pytest surface:
  **324/324 PASS**;
- adversarial replay: `GEN1_PRE 1/1`, `GEN2_PRE 2/2`, cache id rotated,
  `GEN2_POST 2`;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked / 51 baselined / 0 new);
- wiki health: PASS (0 hard errors);
- generated skill surfaces: **13/13 no drift**; registry validation PASS;
- py_compile + `git diff --check`: PASS;
- added-line secret-signature scan: **0 hits**.

The interrupted review of the superseded SHA is defect evidence, not an
acceptance verdict. The replacement exact head requires fresh hosted CI and a
fresh independent R3 review.

## R3 exact-binding repair — placeholder claims + task-ID casing — 2026-09-27

Candidate `a5d853d0b93b906ac45dfa7c31f3cc2d5981fc9e` passed exact-head
PR Loop Gate and Core CI, but fresh independent R3 review returned two P2
blocking findings:

1. the primary `conductor claim` path could omit `--scope`/`--branch`, write
   `<scope>`/`<branch>`, and report a RECONCILED ownership result that the
   canonical reader could not resolve (`BRANCH_UNBOUND`);
2. `add_claim()` matched durable task IDs case-insensitively while generation
   and cache keys remained exact-case, allowing `TASK-X` vs `task-x` to split
   generation/cache identity and weaken ABA protection.

Repair:
- CLI `conductor claim` now requires both `--scope` and `--branch`;
- direct new durable claims reject placeholder/blank scope or branch before
  mutating COLLAB or minting a cache owner;
- durable task matching is exact-case; a casing-only alias is rejected with an
  explicit exact-task-ID conflict;
- exact same-task/same-agent retries remain backward-safe: callers may omit
  scope/branch on an existing durable row and the row's durable binding is
  reused rather than rewritten.

RED evidence: both new review regressions failed before repair.
GREEN / verification after repair:
- review regressions + existing idempotent retry: **3/3 PASS**;
- CLI missing scope/branch exits non-zero and names both required arguments;
- related conductor/claim/MCP/hook/adopt/runtime pytest surface:
  **327/327 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked / 51 baselined / 0 new);
- wiki health: PASS (0 hard errors);
- generated skill surfaces: **13/13 no drift**; registry validation PASS;
- py_compile + `git diff --check`: PASS;
- added-line secret-signature scan: **0 hits**.

The harvested R3 review of `a5d853d0...` is defect evidence, not acceptance
evidence. The replacement exact head requires fresh hosted CI and a fresh
independent exact-SHA R3 review.

## R3 branch-ref repair — exact durable branch resolution — 2026-09-27

Candidate `e51510f595c9afcb18effa257df25a43ae7e8cc4` passed exact-head
Core CI and PR Loop Gate, but fresh independent R3 review found one remaining
P2 blocker on the direct CLI writer:

- `conductor claim --branch <nonexistent-ref>` could write a COLLAB row and
  report a RECONCILED cache even though the canonical reader immediately failed
  with `BRANCH_HEAD_UNRESOLVED`.

Repair:
- new durable claim creation resolves the requested branch to an exact local
  `refs/heads/<branch>` or fetched `refs/remotes/origin/<branch>` commit before
  entry-gate evaluation or COLLAB mutation;
- an unresolved/typo branch fails closed before any durable row or cache owner
  is created;
- legacy unit fixtures that previously used synthetic branch strings now create
  real Git repositories/commits/branch refs so tests exercise the same durable
  binding contract as production.

RED evidence: new unresolved-branch regression failed before repair.
GREEN / verification after repair:
- unresolved-branch regression: **1/1 PASS**;
- updated branch-binding fixture set: **6/6 PASS**;
- related conductor/claim/MCP/hook/adopt/runtime pytest surface:
  **328/328 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked / 51 baselined / 0 new);
- wiki health: PASS (0 hard errors);
- generated skill surfaces: **13/13 no drift**; registry validation PASS;
- py_compile + `git diff --check`: PASS;
- added-line secret-signature scan: **0 hits**.

The review of `e51510f5...` is defect evidence, not acceptance evidence. The
replacement exact head requires fresh hosted CI and a fresh independent R3
review before merge.


## R3 shallow-history identity hardening — 2026-09-27

Candidate `67a10db2513be3c0a8157f066cbebf3fad0e44dc` is superseded before acceptance. A fresh independent exact-head R3 review reran the focused claim/hook suite (283/283 PASS) and then found a cross-machine identity defect by adversarial shallow-clone replay: the same durable task had generation 2 in a full repository but generation 1 in a `--depth 1` clone. Because `claim_id` includes generation, the canonical durable identity could differ by machine/history depth.

Root cause: `claim_generation()` counted local `COLLAB.md` Git history without first proving that the local repository had complete history. Shallow clones can omit prior claim/release generations while still presenting a current claim row.

Repair contract:
- canonical claim generation fails closed when `git rev-parse --is-shallow-repository` is true;
- the reader never mints a canonical generation/claim id from incomplete Git history;
- new durable claims preflight complete history before any `COLLAB.md` mutation;
- the writer converts shallow-history resolution failure to typed `ClaimConflict` and leaves durable state unchanged;
- no automatic network fetch and no guessed generation; the checkout must first obtain complete history through the normal recovery path.

RED evidence: 2/2 new shallow-history regression tests failed before repair.
GREEN evidence after repair:
- targeted shallow reader/writer + ABA generation: 3/3 PASS;
- related conductor/claim/hook/adopt/runtime/MCP suite: 330/330 PASS;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (0 new findings);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

The cancelled review of superseded `67a10db2...` is blocker evidence only, not acceptance evidence. Fresh exact-head hosted CI and a new independent R3 review are required for the replacement candidate.


## R3 direct-writer checkout binding hardening — 2026-09-27

Candidate `f1a35577f1e10724903ede0608bbb91c9a8fa293` is superseded before acceptance. Fresh independent exact-head R3 review reran the focused claim/hook suite (287/287 PASS) and then reproduced a direct-writer binding defect: `add_claim(..., branch="main")` accepted and persisted a durable claim while the repository was in detached HEAD state (`accepted=True`, recorded branch `main`, checkout branch `<detached>`).

Root cause: the MCP wrapper already required an attached current branch, but the canonical direct/CLI writer only verified that the requested branch ref existed. Existence of `refs/heads/main` did not prove that the mutating checkout was actually attached to `main`.

Repair contract:
- direct durable writer requires the repository checkout to be attached to the same exact branch recorded by the durable claim;
- detached HEAD is ineligible even when the requested branch ref exists;
- current-branch mismatch is rejected before COLLAB/cache mutation;
- existing same-task retries also verify their durable branch against the current checkout before refreshing the derived cache;
- branch-ref existence and checkout attachment remain separate fail-closed checks.

RED evidence: direct detached-writer regression failed before repair.
GREEN evidence after repair:
- detached/new-claim + append/idempotent/branch-ref/shallow focused set: **5/5 PASS**;
- related conductor/claim/hook/adopt/runtime/MCP suite: **331/331 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (0 new findings);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

The cancelled review of superseded `f1a35577...` is blocker evidence only, not acceptance evidence. Fresh exact-head hosted CI and a new independent R3 review are required for the replacement candidate.

## R3 exact-branch + concurrent durable-writer hardening — 2026-09-27

Candidate `06bce029bb932016870f8156106e5678e1f52b43` is superseded before
acceptance. Fresh independent exact-head R3 review reproduced two authority
correctness defects:

1. `read_canonical_claim()` accepted a Git tag whose name matched the durable
   `branch` field because `_branch_head()` had a generic ref fallback after the
   exact local/origin branch refs.
2. Concurrent `add_claim()` writers could both report success while a
   read-modify-write race on `COLLAB.md` discarded one durable claim row.

Repair contract:
- canonical branch HEAD resolution now accepts only exact
  `refs/remotes/origin/<branch>` or `refs/heads/<branch>` commit refs; tags or
  other generic refs cannot satisfy durable branch identity;
- same-repository durable writers serialize the complete COLLAB transaction
  through a transient OS file lock in the Git common-dir, so linked worktrees
  share the mutex without creating another claim/lease/authority store;
- POSIX uses `flock`; Windows uses the stdlib `msvcrt` byte-range lock with a
  bounded acquisition timeout;
- legacy no-mutation validation remains before lock acquisition so existing
  error contracts for missing/exact task/scope/branch inputs are preserved;
- all authoritative parse/validate/write/generation/cache-mirror work is
  repeated inside the serialized transaction.

RED evidence:
- tag-only `orphan` ref was incorrectly returned as `branch_head_sha`;
- concurrent durable writers lost/corrupted claim rows while reporting success.

GREEN evidence after repair:
- exact tag-vs-branch + concurrent writer targeted tests: **2/2 PASS**;
- compatibility + repair focused tests: **4/4 PASS**;
- related conductor/claim/hook/adopt/runtime/MCP pytest suite: **333/333 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked files; 51 baselined; **0 new findings**);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

A fresh exact-head hosted CI and independent R3 review are required for the
replacement candidate. The cancelled review of `06bce029...` is defect
evidence only, not acceptance evidence.

## R3 durable-table input validation + command contract hardening — 2026-09-27

Candidate `64bb8faf453b484751e3961706775b6fd5d45f39` is superseded before
acceptance. Fresh independent exact-head R3 review completed with two P2
findings:

1. the public `/A-Claim` command still documented the legacy `claim_acquire`
   flow without the now-required exact `task_id`;
2. durable writer inputs were not safe for the tracked Markdown authority
   table: an absolute machine-local scope could leak into `COLLAB.md`, and a
   newline/pipe payload could inject an additional parsed claim row.

Repair contract:
- `commands/A-Claim.md` now requires recovery of the exact WO/COLLAB `task_id`
  before `claim_acquire` and passes it with scope + goal;
- `conductor/README.md` now shows the current CLI contract with exact topic,
  `--scope`, and `--branch`;
- durable scalar fields reject Markdown table delimiters, line breaks, and
  control characters before mutation;
- durable scopes must be semicolon-separated repo-relative globs and reject
  POSIX/Windows absolute paths, home-relative paths, parent traversal, and
  table/control injection;
- validation is performed before the lock and repeated inside the serialized
  durable transaction; no cache write occurs on rejection.

RED evidence: 10/10 new security/command-contract cases failed before repair.
GREEN evidence after repair:
- targeted unsafe-scope/scalar + `/A-Claim` contract cases: **10/10 PASS**;
- related conductor/claim/hook/adopt/runtime/MCP pytest suite: **343/343 PASS**;
- privacy scan: PASS;
- hook registry: PASS (30 hooks; 17 hard / 13 soft);
- security scan: PASS (6361 tracked files; 51 baselined; **0 new findings**);
- wiki health: PASS (0 hard errors);
- py_compile + `git diff --check`: PASS.

The completed R3 review of `64bb8faf...` is defect evidence only. A fresh
exact-head hosted CI and independent R3 review are required for the replacement
candidate.
