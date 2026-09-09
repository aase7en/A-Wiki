---
type: source
title: "30 — REPOSITORY SAFETY / IDENTITY / OWNERSHIP"
slug: 30-repo-safety
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/30-REPO-SAFETY.md
tags: []
---

# 30 — REPOSITORY SAFETY / IDENTITY / OWNERSHIP

## Activate when

Any repository mutation, branch/commit/worktree operation, destructive action, or multi-worker repository coordination is involved.

---

# 1. Repository identity gate

Before mutation verify:

- project,
- repository,
- absolute worktree,
- remote,
- default/base branch,
- current branch,
- HEAD SHA,
- dirty state,
- active task,
- active owner,
- allowed scope,
- forbidden scope,
- allowed files,
- forbidden files,
- overlapping work.

Never assume identity from a previous session.

Never assume local tracking refs equal remote reality.

---

# 2. Read repo-local instructions first

Before meaningful repository work inspect and follow the repository's own:

- `AGENTS.md`,
- `AGENT.md`,
- contributor/development instructions,
- task/work-order rules,
- safety/ownership files,

or established equivalents.

Project-template workflow must not silently override repository-specific safety constraints.

---

# 3. Live claims gate

Before architecture, major implementation, or broad refactor inspect where available:

- remote branches,
- open PRs,
- issues,
- active work orders,
- task claims,
- active workers,
- recent merges,
- existing implementation,
- related specs/designs.

Do not duplicate work because it is absent from your checkout.

Do not mutate overlapping scope owned by another worker without reconciliation.

---

# 4. Drift

If actual state differs materially from expected handoff/baseline classify:

- `EXPECTED`
- `NOT_STARTED`
- `PARTIAL`
- `COMPLETE_UNVERIFIED`
- `COMPLETE_VERIFIED`
- `UNEXPECTED_DRIFT`
- `OWNERSHIP_CONFLICT`
- `UNKNOWN`

If unsafe:

`STOP MUTATION`

Reconcile before changes.

---

# 5. Dirty worktree safety

Unknown modifications/untracked files may belong to another task/worker.

Never casually:

- reset,
- checkout over,
- clean,
- stash-and-forget,
- delete,
- overwrite

unknown dirty state.

Identify ownership first.

---

# 6. Multi-worker rule

Parallel mutation requires explicit separation by:

- task ownership,
- worktree/branch strategy,
- allowed files/areas,
- dependency/blocking graph,
- reconciliation plan.

Avoid overlapping mutable scope.

---

# 7. Destructive actions

Actions such as:

- force push,
- hard reset,
- branch deletion,
- user-file deletion,
- dropping database objects,
- history rewriting,
- production-data deletion,
- credential rotation

require verified scope and authorization.

If difficult to reverse and approval is not established:

`AUTHORIZATION_REQUIRED`

---

# 8. Secrets

Do not persist:

- passwords,
- API keys,
- tokens,
- cookies,
- private keys,
- auth secrets

into Git, specs, handoffs, issues, PRs, or logs.

Reference secure configuration locations/mechanisms without copying secrets.

---

# 9. Retry safety

Before retrying an interrupted mutation determine:

- `NOT_STARTED`
- `PARTIAL`
- `COMPLETE_UNVERIFIED`
- `COMPLETE_VERIFIED`
- `UNKNOWN`

Do not blindly rerun non-idempotent operations.

Inspect resulting state first.

---

# 10. Idempotency

Where automated work may retry, protect against:

- duplicate records,
- duplicate commits,
- repeated notification,
- repeated deployment/migration,
- duplicate issue creation,
- repeated file append,
- concurrent duplicate execution.

Document non-idempotent retry boundaries.

---

# 11. Mutation gate verdict

Before changing files be able to state internally:

`SAFE_TO_MUTATE = YES`

or

`SAFE_TO_MUTATE = NO`

Never mutate under uncertainty merely to make progress.
