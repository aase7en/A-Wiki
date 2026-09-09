---
type: source
title: "20 — ENGINEERING MAIN FLOW"
slug: 20-engineering-main-flow
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/20-ENGINEERING-MAIN-FLOW.md
tags: [ai]
---

# 20 — ENGINEERING MAIN FLOW

## Activate when

- implementing a feature/refactor/planned change,
- creating or consuming a spec,
- decomposing multi-session work,
- running the core build loop.

The preferred build spine follows the current AIHero-style main flow:

`grill-with-docs → to-spec → to-tickets → implement → code-review`

The project extends this with stronger SSoT, verification, E2E/audit, release, and continuity gates.

---

# 1. Route adaptively

Do not mechanically run all stages.

## Small, fuzzy repository change
`grill-with-docs → implement → code-review`

## Multi-session/multi-agent change
`grill-with-docs → to-spec → to-tickets → implement per ticket → code-review`

## Huge/foggy effort
Use the shaping node first.

## Already agreed and well-specified
Start at the first unresolved/unfinished stage; do not restart grilling.

---

# 2. Grill / grill-with-docs

Purpose: shared understanding before building.

Use repository-backed grilling to:

- construct the unresolved decision tree,
- identify the current decision frontier,
- ask only decision-relevant questions,
- give a recommended default and trade-off,
- retrieve facts from repo/tools rather than asking the human,
- detect contradictions,
- clarify canonical domain vocabulary,
- identify constraints/non-goals,
- surface failure/ownership/security/operational implications,
- capture important durable decisions.

Do not conduct an interview for facts the system can retrieve.

Do not implement through unresolved important decisions.

Important uncertainty must be:

- `RESOLVED`
- `ASSUMPTION_ACCEPTED`
- `DELEGATED_TO_AGENT`

before implementation proceeds.

---

# 3. Facts vs decisions

## Facts
Examples: code behavior, API support, branch state, test result.

Investigate directly.

## Decisions
Examples: product priority, UX preference, lock-in, cost/reliability trade-off.

Present evidence/recommendation; human owns major decisions unless delegated.

---

# 4. To-spec

Use a spec when the work needs to survive session/agent boundaries.

A spec synthesizes settled understanding; it should not restart the interview.

Include where relevant:

- objective/outcome,
- current and desired behavior,
- scope/non-goals,
- canonical terminology,
- invariants,
- interfaces/seams,
- data contracts,
- failure behavior,
- security/privacy,
- performance,
- observability,
- migration/compatibility,
- acceptance criteria,
- test seams,
- rejected alternatives that matter.

Do not invent requirements.

---

# 5. Seams before implementation

Choose the highest useful stable seam(s) before coding.

Prefer:

`existing seam > new seam`

`higher meaningful seam > fragile internal seam`

`few stable seams > unnecessary proliferation`

Examples:

- public function,
- module API,
- HTTP contract,
- CLI contract,
- user-visible interaction,
- persisted state transition.

Tests should protect durable behavior.

---

# 6. Adaptive spec rule

A heavyweight spec is unnecessary for a trivial one-context task.

If decisions are settled and one fresh context can safely complete the change, direct implementation may be appropriate.

If work spans multiple sessions/agents/tickets or complex acceptance criteria, create a durable spec.

---

# 7. Spec review gate

Before implementation for material work verify:

- material decisions survived,
- no requirement was invented,
- non-goals survived,
- numeric/default limits survived,
- negative requirements survived,
- edge cases survived,
- test seams survived,
- security constraints survived.

Outcome:

- `SPEC_PASS`
- `SPEC_BLOCKED`

A blocked spec loops upstream.

---

# 8. To-tickets

Use tickets for multi-context execution.

Prefer tracer-bullet vertical slices:

```text
one narrow capability
├─ data
├─ logic
├─ interface
└─ tests
```

Avoid horizontal tickets such as "all backend" unless a wide mechanical refactor requires a different strategy.

---

# 9. Wide-refactor exception

When one mechanical change spans the codebase, use expand-contract when appropriate:

`EXPAND → MIGRATE SAFE BATCHES → VERIFY → CONTRACT`

Keep intermediate states green where possible.

---

# 10. Ticket contract

Each meaningful ticket should define:

- ID,
- parent objective/spec,
- goal/why,
- dependencies/blockers,
- preconditions,
- scope,
- allowed files/areas,
- forbidden files/areas,
- acceptance criteria,
- test seam,
- verification,
- evidence,
- retry/escalation,
- owner/claim,
- status.

Default size: one coherent fresh-agent context.

If a ticket needs hidden conversational knowledge, fix the ticket or SSoT.

---

# 11. Blocking graph

Tickets form a dependency graph.

Only unblocked tickets become `READY`.

The set of independent READY tickets is the execution frontier.

Parallelize only safe independent frontier tasks.

---

# 12. Implement

Implementation executes settled decisions.

If a genuine missing architectural/product decision appears:

`DECISION_REQUIRED`

Return upstream rather than inventing the decision.

Implementation rhythm where applicable:

`READ CONTRACT → VERIFY REPO GATE → IDENTIFY SEAM → RED → GREEN → REFACTOR → TARGETED VERIFY → NEXT SLICE → FULL SUITE → SELF REVIEW`

Use TDD where meaningful; do not write superficial tests merely to claim TDD.

---

# 13. Implementation scope

- smallest coherent change,
- avoid unrelated refactors,
- reuse established architecture,
- preserve required compatibility,
- keep diff understandable,
- maintain useful observability,
- do not suppress real failures,
- do not weaken valid tests to get green.

Checkpoint after meaningful mutation.

---

# 14. Self review

Before independent review inspect:

- objective alignment,
- scope creep,
- accidental files,
- duplicated/dead code,
- hidden coupling,
- unsafe assumptions,
- incomplete error handling,
- missing tests,
- performance regression,
- security/privacy concerns,
- stale docs/comments,
- generated artifacts,
- dependency changes,
- TODO/FIXME debt.

Fix obvious issues first.

---

# 15. Code review — two orthogonal axes

Review the actual diff against a fixed point.

## Standards
"Was it built correctly according to this repository?"

Inspect repo conventions, architecture, maintainability, naming, design quality, smells, unintended complexity.

## Spec
"Did we build the correct thing?"

Inspect objective, spec/ticket, acceptance criteria, negative requirements, non-goals, missing behavior, scope creep.

Never blend the axes into a single score.

Per axis:

- `PASS`
- `NOTE`
- `CHANGES_REQUIRED`
- `BLOCKED`

Any material failure means overall `CHANGES_REQUIRED`.

---

# 16. Independent review

For material changes prefer a reviewer that did not author the implementation.

Reviewer inspects:

- actual diff,
- actual spec/ticket,
- repository rules,
- actual tests/evidence.

Review the artifact, not merely the author's summary.

After code review, continue to the verification node.
