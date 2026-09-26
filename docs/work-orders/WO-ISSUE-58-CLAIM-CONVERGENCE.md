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
