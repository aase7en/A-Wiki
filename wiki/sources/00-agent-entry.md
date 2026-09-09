---
type: source
title: "00 — AGENT ENTRY / GRAPH ROUTER"
slug: 00-agent-entry
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/00-AGENT-ENTRY.md
tags: [ai]
---

# 00 — AGENT ENTRY / GRAPH ROUTER

## Status

**Always read this file first for substantial project work.**

This is the runtime router. It is intentionally short compared with the full operating specification.

Do **not** load all workflow documents by default.

---

# 1. Core invariant

**SSoT is durable project/repository state, not chat memory.**

Conversation context may help, but it is never sufficient evidence of project state.

Use:

> actual state + durable records + deterministic evidence

before model memory or assumptions.

---

# 2. First-pass recovery

Before substantial work determine:

1. Which project/repository is active?
2. What is the user's current objective?
3. What durable SSoT exists?
4. What does actual repository/runtime state say?
5. Is another worker already doing overlapping work?
6. What workflow state are we currently in?
7. What is the smallest safe next micro-step?
8. What evidence would prove it complete?

Do not restart work merely because the conversation/session is new.

---

# 3. Mandatory node routing

Read `PROJECT-GRAPH.yaml`, then traverse only the necessary nodes.

Minimum common paths:

## Repository session start/resume

`ENTRY → SSOT → REPO_SAFETY`

## New/fuzzy feature

`ENTRY → SSOT → REPO_SAFETY → SHAPING? → MAIN_FLOW`

## Agreed implementation task

`ENTRY → SSOT → REPO_SAFETY → MAIN_FLOW → VERIFY`

## Bug investigation

`ENTRY → SSOT → REPO_SAFETY → VERIFY → DEFECT_MEMORY`

Add `E2E_AUDIT` if risk or blast radius warrants it.

## PR / release / merge

`ENTRY → SSOT → REPO_SAFETY → VERIFY → E2E_AUDIT? → RELEASE`

## Delegation / worker / GPT Work

Add:

`→ DELEGATION`

before handing work off.

## Context becoming crowded

`ENTRY → SSOT`

and execute the checkpoint/session-rotation protocol before changing sessions.

---

# 4. Do not over-read

Do not read:

- release rules for a pure research question,
- E2E rules for a terminology discussion,
- delegation rules when no delegation is needed,
- the full master spec on every task.

Load a node only because the current state requires it.

If a node is ambiguous or two modules conflict:

1. prefer higher-priority project-specific authority,
2. consult `90-MASTER-SPEC.md`,
3. classify unresolved material conflict as `DECISION_REQUIRED`.

---

# 5. Task routing

Choose the shortest safe flow.

### Concept only / no repo
`grill-me → decision/plan`

### Repo + fuzzy but small
`grill-with-docs → implement → code-review → required assurance`

### Repo + multi-session work
`grill-with-docs → to-spec → to-tickets → implement → code-review → required assurance`

### Huge/foggy effort
`wayfinder → resolve decisions → main flow`

### External fact blocks decision
`research → decision process`

### Design question requires experience/code
`prototype → learn → feed conclusion back → normal flow`

### Hard bug
`reproduce → diagnose → regression test → repair → review → verify`

---

# 6. Micro-step autonomy

Use small, resumable steps.

A useful micro-step has:

- ID
- goal
- preconditions
- scope
- action
- expected result
- verification
- evidence
- status
- next step

Continue through safe steps without repeatedly asking "continue?".

Stop only when:

- `HUMAN_DECISION_REQUIRED`
- `HUMAN_ACTION_REQUIRED`
- `AUTHORIZATION_REQUIRED`
- `SAFETY_BLOCK`
- `NO_SAFE_NEXT_ACTION`

---

# 7. Failure means loop, not forward progress

Examples:

`SPEC BLOCKED → Grill/Spec`

`CODE REVIEW FAIL → Implement → Review again`

`BUG FOUND → Reproduce → Repair → Review → Tests → E2E as needed`

`AUDIT FAIL → earliest responsible design/implementation stage`

`CI FAIL → classify → repair → verify → CI again`

Never bypass a failed gate merely to reach PR/merge/DONE.

---

# 8. Completion standard

Do not mark substantive work `DONE` solely because:

- code exists,
- an agent says finished,
- unit tests pass,
- review passes,
- CI is green,
- PR is merged.

`DONE` requires all **applicable** gates:

- requirement satisfied,
- implementation verified,
- diff reviewed,
- deterministic tests passed,
- realistic verification passed when relevant,
- material audit completed when relevant,
- known risks recorded,
- defect prevention updated when relevant,
- durable state updated,
- merged/deployed state verified when relevant,
- another agent can continue without chat memory.

---

# 9. Context safety

If context quality is degrading:

1. stop at a safe micro-step boundary,
2. persist task state,
3. persist evidence,
4. record repo state,
5. update handoff,
6. record one next safe action,
7. then rotate session/context.

Never use the human as project memory.

---

# 10. Default opening behavior

For every new substantial task:

`RECOVER SSoT → VERIFY ACTUAL STATE → IDENTIFY GRAPH NODE → EXECUTE NEXT SAFE MICRO-STEP → VERIFY → CHECKPOINT`

Then continue through required graph edges.
