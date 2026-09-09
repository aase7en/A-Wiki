---
type: source
title: "50 — RELEASE / PR / CI-CD / MERGE"
slug: 50-release
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/50-RELEASE.md
tags: []
---

# 50 — RELEASE / PR / CI-CD / MERGE

## Activate when

Committing, opening/reviewing a PR, waiting on CI/CD, merging, or verifying post-merge/deployment state.

---

# 1. Branch policy

Use bounded branches appropriate to work type, e.g.:

- `feat/<task-id>-<slug>`
- `fix/<task-id>-<slug>`
- `refactor/<task-id>-<slug>`
- `docs/<task-id>-<slug>`
- `chore/<task-id>-<slug>`

Dedicated repo-health branches may be used by project convention.

Do not use one generic branch as a dumping ground for unrelated work.

---

# 2. Commit discipline

Before commit:

- inspect diff,
- verify intended files,
- run required verification,
- remove debug artifacts,
- remove secrets,
- update task/current-work state.

Commits should represent coherent verified changes.

---

# 3. Pre-PR gate

Verify:

- correct repo,
- correct source/base branch,
- expected commits,
- understood diff,
- no accidental files,
- required tests passed,
- E2E passed where required,
- review complete,
- audit complete where required,
- SSoT updated,
- no secrets,
- no unresolved blocking findings.

Only then open PR.

---

# 4. PR content

Communicate:

- problem/objective,
- spec/ticket,
- implementation summary,
- major decisions,
- changed areas,
- test evidence,
- E2E evidence,
- audit result,
- risks/limitations,
- migrations,
- rollback notes when relevant,
- visual evidence for UI work when useful.

PR description is not the only durable project memory.

---

# 5. Remote diff audit

After PR creation inspect the actual remote diff.

Do not assume:

`local diff == PR diff`

Verify:

- base,
- commits,
- unexpected files,
- generated junk,
- secrets,
- formatting churn,
- dependency/lockfile surprises,
- merge-base surprises,
- missing intended files.

Material mismatch:

`STOP MERGE`

Reconcile first.

---

# 6. CI/CD states

Classify:

- `PASS`
- `FAIL`
- `PENDING`
- `CANCELLED`
- `SKIPPED_VALID`
- `SKIPPED_INVALID`
- `INFRA_FAILURE`

Do not mislabel infrastructure cleanup/tool failure as assertion failure.

Do not call a process fully successful when required CI did not reach valid success.

---

# 7. CI failure loop

`CI FAILURE → classify → exact failed check/evidence → reproduce where possible → root cause → repair → review → test → push → CI again`

Do not push speculative fixes repeatedly.

---

# 8. Waiting rule

Do not claim invisible background work unless an actual durable automation/background mechanism exists.

If CI is still running and tools can poll, poll.

Otherwise checkpoint:

- `CI_PENDING`,
- PR,
- current SHA,
- pending checks,
- next safe action.

---

# 9. Post-CI re-audit

After required CI passes verify:

- PR HEAD equals reviewed SHA,
- no unexpected commits,
- remote diff still matches intent,
- findings resolved,
- docs match behavior,
- CI repair did not introduce new risk.

Only then:

`MERGE_READY`

---

# 10. Merge gate

Merge only when applicable:

- required CI passes,
- required review/approval exists,
- latest SHA reviewed,
- blocking audit findings resolved,
- repo policy permits merge,
- ownership conflicts resolved,
- human approval obtained if policy requires it.

Green CI alone is not approval.

---

# 11. Merge record

Record:

- PR number,
- source branch,
- target branch,
- merge method,
- merged SHA,
- date/time,
- final CI,
- final review,
- final audit.

---

# 12. Fetch / reconcile

After remote merge:

1. fetch remote,
2. verify merge exists,
3. verify target/default branch contains expected commit,
4. reconcile tracking state,
5. inspect dirty worktrees,
6. never overwrite unrelated local changes,
7. update SSoT to merged reality.

Remote merge does not update every worker automatically.

---

# 13. Post-merge verification

Where meaningful:

- build merged HEAD,
- smoke test,
- critical user journey,
- deployment health,
- migration status,
- logs/telemetry,
- runtime config,
- health endpoints,
- rollback readiness.

`CI GREEN != PRODUCTION VERIFIED`

---

# 14. Post-merge failure

If deployment/runtime fails, record a new incident/defect state:

- symptom,
- impact,
- merge SHA,
- environment,
- reproducer,
- evidence,
- mitigation,
- next safe action.

Then enter the debugging loop.

---

# 15. Closeout

Before release task becomes DONE, update:

- task/work order,
- current work,
- PR/merge state,
- tests/E2E/audit evidence,
- defect memory where relevant,
- handoff/next action.
