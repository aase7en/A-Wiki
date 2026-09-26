# WO-ISSUE-58 — Claim authority convergence + canonical reader

Status: IMPLEMENTING / RED-FIRST
Issue: aase7en/A-Wiki#58
Risk: R3 — coordination authority, hooks, claim enforcement
Topology: CONTROL_PLANE_ONLY (A-Wiki upstream authority)

## Binding

- Repo: aase7en/A-Wiki
- Worktree: `/Users/aase7en/Desktop/_worktrees/A-Wiki-issue58-claim-convergence`
- Branch: `fix/issue-58-claim-convergence`
- Base: `16897b2d34f3ff0de0938f7651cf19bbce106b43`
- Durable owner: `chatgpt-sol`
- Durable claim: COLLAB row 
- Local TTL claim: `a95e8c226df4` (canonical Mac store)
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
