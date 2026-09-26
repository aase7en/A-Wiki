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
