---
type: source
title: "90 — MASTER NORMATIVE SPEC"
slug: 90-master-spec
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/90-MASTER-SPEC.md
tags: []
---

# 90 — MASTER NORMATIVE SPEC

> **REFERENCE ONLY. DO NOT READ BY DEFAULT.**
>
> Runtime agents should use `00-AGENT-ENTRY.md` and `PROJECT-GRAPH.yaml`.
> Read this file only for module ambiguity/conflict, methodology audit, or template maintenance.

---

# A. Mission

Create a project operating system in which humans, agents, models, deterministic tools, repositories, trackers, and execution environments behave like a disciplined engineering organization.

The project must remain coherent across:

- sessions,
- context windows,
- models/vendors,
- worker crashes,
- remote/local state drift,
- CI failures,
- handoffs,
- long-running work.

The human owns goals and major decisions; the system owns durable continuity.

---

# B. Governing invariants

1. SSoT is not chat memory.
2. Verify handoffs against actual state.
3. Read repository-local instructions before mutation.
4. Avoid duplicate/shadow project-management files.
5. Persist implementation-critical decisions before context loss.
6. Route through only the workflow nodes required by current state.
7. Use the shortest safe workflow, not maximum ceremony.
8. Split long work into resumable tasks.
9. Prefer vertical tracer-bullet tickets.
10. Use bounded parallelism from a dependency graph.
11. Implementation executes settled decisions; it does not silently redesign.
12. Review "built right" and "built the right thing" independently.
13. Start hard debugging from a reproducer.
14. Deterministic evidence outranks model confidence.
15. Deep E2E targets realistic failure/recovery paths.
16. Audit is separate from ordinary code review.
17. Turn defects into executable prevention where possible.
18. Inspect the actual remote PR diff.
19. Green CI is necessary but not sufficient.
20. Re-audit the final PR head after CI repairs.
21. Verify merged/deployed reality when applicable.
22. Failed gates loop backward.
23. Checkpoint before context/session/worker rotation.
24. Never force the human to act as project memory.
25. Do not claim DONE without applicable evidence.

---

# C. Responsibility model

- Strong reasoning model: architecture, synthesis, difficult review, security reasoning.
- Bounded/cheap/local model: scoped worker and research tasks.
- Deterministic tools/tests: verifier.
- Repository/durable docs/tracker: memory.
- Orchestrator: manager/router.
- Execution integration: hands.
- Human: goals, preferences, consequential decisions.

`MODEL PROPOSES → TOOLS VERIFY → REPOSITORY REMEMBERS`

---

# D. Authority order

Default order:

1. latest explicit user instruction,
2. safety/security,
3. approved ADR/decision,
4. repository agent instructions,
5. project plan,
6. active work state,
7. verified handoff,
8. approved spec,
9. tickets/tracker,
10. actual runtime/repo state,
11. remote state,
12. deterministic evidence,
13. current conversation,
14. memory/inference.

Material conflict becomes `DECISION_REQUIRED`.

---

# E. Lifecycle state machine

```text
RECOVER SSoT
→ REPO / OWNERSHIP GATE
→ ROUTE
→ OPTIONAL SHAPING
→ MAIN FLOW
→ VERIFY / DEBUG
→ E2E / AUDIT
→ REPORT
→ DEFECT MEMORY
→ REPO HEALTH
→ PRE-PR
→ COMMIT
→ PR
→ REMOTE DIFF
→ CI/CD
→ RE-AUDIT
→ MERGE
→ FETCH / RECONCILE
→ POST-MERGE VERIFY
→ FINAL CHECKPOINT / HANDOFF
```

This is recursive.

Examples:

- spec blocked → design/spec,
- implementation discovers decision → design,
- review fails → implementation,
- deep bug → debug/repair/review/tests/E2E,
- audit fails → earliest responsible stage,
- CI fails → classify/repair/review/test/CI,
- post-merge failure → incident/defect loop.

---

# F. Runtime routing

## Concept only
`grill-me → decision/plan`

## Small repo change with uncertainty
`SSoT → repo gate → grill-with-docs → implement → code-review → applicable assurance`

## Multi-session repo change
`SSoT → repo gate → grill-with-docs → to-spec → to-tickets → implement → code-review → assurance`

## Huge/foggy work
`wayfinder → decisions → main flow`

## External fact blocker
`research → decision process`

## Experiential/design uncertainty
`prototype → evidence → decision → main flow`

## Hard bug
`reproduce → diagnose → regression → repair → review → tests → E2E as required`

---

# G. Main flow

Current conceptual spine:

`grill-with-docs → to-spec → to-tickets → implement → code-review`

### Grill
Resolve the important decision frontier, retrieve facts, clarify domain language, capture durable decisions.

### Spec
Synthesize settled understanding. Do not invent requirements or restart the interview.

### Tickets
Create bounded implementation slices with blockers, acceptance criteria, verification, and evidence.

### Implement
Execute settled contract, preferably at pre-agreed stable seams and with test-first verification where meaningful.

### Code review
Review Standards and Spec as independent axes.

---

# H. Shaping

Use only when needed.

### Wayfinder
Map large unresolved decision spaces.

### Research
Answer external factual blockers from primary/authoritative sources.

### Prototype
Build disposable experiments to answer a design question that discussion cannot settle.

### Brainstorm
Generate alternatives/trade-offs; never confuse options with approved decisions.

Delegated shaping must be bounded and non-recursive unless explicitly designed otherwise.

---

# I. Task decomposition

Each meaningful task:

- ID,
- goal,
- parent objective,
- dependencies,
- scope,
- allowed/forbidden areas,
- acceptance criteria,
- test seam,
- verification,
- evidence,
- retry/escalation,
- owner,
- status.

Prefer one task per fresh execution context.

Use expand-contract for wide mechanical refactors when vertical slices cannot remain green.

---

# J. Repository gate

Before mutation verify:

- repo/worktree,
- branch/base,
- HEAD,
- dirty state,
- remote reality,
- task/owner,
- scope/files,
- overlapping work.

Unknown dirty state is protected.

Destructive difficult-to-reverse actions require verified authorization.

Secrets are never persisted into Git/docs/issues/PR/logs.

---

# K. Verification

Independent review for material changes.

Start hard bugs from a named reproducer.

Classify failures accurately:

- code,
- assertion,
- build,
- tool,
- infra,
- transport,
- auth,
- permission,
- dependency,
- environment,
- CI,
- deployment,
- unknown.

Run applicable deterministic verification and record exact command/results.

Never weaken valid checks merely to achieve green.

---

# L. Realistic E2E

Exercise applicable:

- normal lifecycle,
- UI states,
- dependency failures,
- retries,
- resume/restart,
- duplicate/idempotent execution,
- concurrency,
- malformed/large input,
- stale state,
- migration/rollback,
- mobile/desktop/accessibility,
- locale/time boundaries,
- performance,
- operational diagnosability.

Failure loops through repair and re-verification.

---

# M. Audit

Risk-proportionate audit dimensions:

- security,
- privacy,
- reliability,
- architecture,
- performance,
- operations,
- UX/accessibility,
- deployment.

Audit verdict:

- PASS,
- PASS_WITH_NOTES,
- CHANGES_REQUIRED,
- BLOCKED.

Normal code review is not automatically an audit.

---

# N. Defect memory

For material defects preserve reusable root-cause knowledge and prefer:

`regression test → deterministic checker → type/schema → architecture invariant → CI/lint → monitoring → docs → prose`

A bug is not fully learned from until the chosen prevention is implemented and verified.

---

# O. Release

Before PR:

- correct repo/branch/base,
- intended diff/commits,
- tests,
- required E2E,
- review,
- required audit,
- updated SSoT,
- no secret/blocker.

After PR creation inspect actual remote diff.

CI states are classified accurately.

CI failures are diagnosed, not guessed at.

After CI green, re-audit latest PR head.

Merge only under repo policy/approvals.

Fetch/reconcile merged state and verify deployment/runtime when applicable.

---

# P. Continuity

Checkpoint at meaningful boundaries.

Handoff includes:

- project/objective/phase/task/status,
- completed verified work,
- evidence,
- repo state,
- changed files,
- decisions,
- unresolved decisions,
- warnings,
- do-not-do,
- TODO,
- one next safe action,
- resume instructions.

Receiving agents verify handoff against reality.

When context degrades, checkpoint and rotate rather than forcing continuation.

---

# Q. Delegation

Every worker/subagent/GPT Work handoff is a bounded contract.

Parallelism comes from independent READY tasks, not random fan-out.

Parent agent owns synthesis.

Durable worker output is still a claim until reconciled with SSoT/evidence/review.

---

# R. Human stop conditions

Continue autonomously through safe micro-steps.

Stop only for:

- genuine product/subjective decision,
- manual action,
- authorization,
- destructive-action approval,
- credentials/login unavailable to agent,
- no safe next action.

When stopping, provide exact manual steps and success criteria.

---

# S. Completion invariant

Substantive DONE means applicable evidence confirms:

- requirement satisfied,
- implementation complete,
- diff reviewed,
- deterministic verification passed,
- realistic assurance passed where required,
- material audit complete where required,
- risks/limitations recorded,
- defect prevention updated where relevant,
- durable state updated,
- merged/deployed state verified where relevant,
- another agent can continue without chat memory.

---

# T. Final continuity test

Before stopping:

> Can a new competent agent with zero access to this conversation continue safely using only project files, actual repository state, tracker, evidence, and handoff?

If not, the checkpoint is incomplete.
