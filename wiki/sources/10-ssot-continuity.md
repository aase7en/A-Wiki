---
type: source
title: "10 — SSoT / CONTINUITY / HANDOFF"
slug: 10-ssot-continuity
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/10-SSOT-CONTINUITY.md
tags: []
---

# 10 — SSoT / CONTINUITY / HANDOFF

## Activate when

- beginning or resuming substantial project work,
- changing session/model/worker,
- context is becoming crowded,
- durable task state is unclear,
- handoff claims must be verified.

---

# 1. Source-of-truth principle

Chat/session memory is temporary.

Durable state is authoritative.

A new competent agent with zero access to the previous conversation must be able to continue from project/repository artifacts and actual state.

---

# 2. Source priority

Unless the latest explicit user instruction overrides it:

1. latest explicit user instruction
2. safety/security constraints
3. approved ADRs / authoritative decisions
4. repository-level agent instructions
5. authoritative project plan/roadmap
6. active work/work-order/task state
7. latest verified handoff
8. approved spec
9. issue tracker/tickets/blocking graph
10. actual repository/filesystem/runtime state
11. remote Git/PR/issues/live claims
12. deterministic tool evidence
13. current conversation
14. model memory/inference

Never silently let a lower source override a higher one.

---

# 3. Conflicts

If authoritative sources materially conflict:

`DECISION_REQUIRED`

Record:

- existing position,
- conflicting position,
- evidence,
- why they conflict,
- recommended resolution,
- impact of options,
- safe independent work that can continue.

Stop only the affected work.

---

# 4. Do not create shadow SSoT

Before creating planning/status/handoff/memory/decision files:

1. inspect project structure,
2. locate equivalent roles,
3. reuse existing documents where possible.

Logical roles may include:

- project plan/roadmap,
- current work,
- handoff,
- context/glossary,
- ADRs,
- specs,
- tickets/issues,
- defect records.

Do not maintain the only TODO in chat.

---

# 5. Knowledge classes

## Durable knowledge
Architecture principles, stable constraints, proven integrations, validated procedures, recurring failure patterns.

## Decisions
Use ADRs only for decisions that are important, non-obvious, expensive to reverse, and represent a real trade-off.

## Working state
Current task, branch, checklist, partial attempts, blockers, temporary failures.

## Specification
Feature/change-specific implementation contract.

Do not mix these indiscriminately.

---

# 6. Critical-decision persistence

No implementation-critical decision may have its only copy in chat.

Persist at the smallest appropriate durable location:

- vocabulary → context/glossary,
- long-lived architecture → ADR,
- implementation contract → spec,
- minor accepted choice → decision log/current work,
- execution state → task/current work/handoff.

---

# 7. Session start protocol

Before substantial work:

1. identify project/repo/worktree,
2. read repository agent instructions,
3. read project plan,
4. read current work/work orders,
5. read latest handoff,
6. read relevant ADR/context/spec/tickets,
7. inspect relevant PRs/issues/live claims,
8. inspect actual repo/runtime state,
9. compare actual state against handoff,
10. identify current objective/task/status,
11. identify blockers/decisions,
12. identify one next safe action.

Do not ask the user for retrievable state.

---

# 8. Handoff is a claim, not truth

Receiving agent must verify:

`HANDOFF → project identity → repo → branch/HEAD → dirty state → claimed artifacts → important evidence → reconcile → continue`

Classify inherited work where useful:

- `NOT_STARTED`
- `PARTIAL`
- `COMPLETE_UNVERIFIED`
- `COMPLETE_VERIFIED`
- `UNEXPECTED_DRIFT`
- `OWNERSHIP_CONFLICT`
- `UNKNOWN`

Do not blindly rerun non-idempotent work.

---

# 9. Checkpoint discipline

Checkpoint at meaningful boundaries:

`GATE → READ → EDIT → TEST → REVIEW → COMMIT`

For fragile execution surfaces, checkpoint more frequently.

A checkpoint should preserve:

- what changed,
- where,
- why,
- evidence,
- blockers,
- task status,
- next safe action.

---

# 10. Handoff triggers

Update handoff when:

- session ends,
- context is rotated,
- execution may terminate,
- work moves to another model/vendor/worker,
- Chat ↔ GPT Work,
- worker ↔ worker,
- major checkpoint,
- unexpected failure,
- deliberate pause.

---

# 11. Handoff format

Use project equivalent if present; otherwise:

```md
# HANDOFF

## Project
Name / repository / path

## Current Objective
Exact desired outcome

## Current Phase
Workflow stage

## Current Task
ID + goal

## Status
Canonical status

## Completed
Verified work only

## Evidence
Commands/tests/files/hashes/reviews

## Repository State
Repository:
Worktree:
Branch:
HEAD:
Dirty state:

## Files Changed
Exact paths/areas

## Decisions Made
Established decisions only

## DECISION_REQUIRED
Unresolved decisions

## Known Problems / Warnings

## Do Not Do

## TODO
Ordered remaining work

## Next Safe Action
ONE immediate action

## Resume Instructions
```

---

# 12. Context health

Warning signs:

- repeated rereading,
- contradictory assumptions,
- forgotten constraints,
- giant logs dominating context,
- unrelated tasks mixed together,
- large completed phases still active,
- summaries replacing source inspection,
- requirements disappearing under token pressure.

When context degrades, rotate deliberately.

---

# 13. Session rotation

Before rotating:

1. stop at safe micro-step boundary,
2. update task status,
3. update checklist,
4. record completed work,
5. record evidence,
6. record unresolved issues,
7. record repository state,
8. update handoff,
9. record one next safe action,
10. ensure no critical decision exists only in chat.

Then resume in a fresh context from durable state.

---

# 14. Continuity test

Before stopping ask:

> Could a new agent with no access to this conversation continue safely from project files, repository state, tracker, evidence, and handoff?

If no, checkpoint is incomplete.
