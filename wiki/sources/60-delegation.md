---
type: source
title: "60 — DELEGATION / SUBAGENTS / WORKERS / GPT WORK"
slug: 60-delegation
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/60-DELEGATION.md
tags: []
---

# 60 — DELEGATION / SUBAGENTS / WORKERS / GPT WORK

## Activate when

Work is being handed to another agent, worker, model, vendor, Codex/GPT Work session, or parallel execution lane.

---

# 1. Delegation principle

Do not delegate:

> Continue the project.

Delegate a bounded task contract.

The receiving worker should need no hidden chat context.

---

# 2. Task contract

Include:

- role,
- project,
- repository/path,
- branch/HEAD/dirty state when relevant,
- current objective,
- exact task ID/goal,
- authoritative sources to read first,
- required context,
- allowed scope,
- forbidden scope,
- allowed files/actions,
- forbidden files/actions,
- dependencies/blockers,
- acceptance criteria,
- verification,
- evidence required,
- checkpoint requirements,
- expected output,
- handoff destination.

---

# 3. Parallelism

Parallelism should come from the dependency graph, not from blindly launching many agents.

Before parallel mutation define:

- independent READY tasks,
- ownership,
- worktree/branch strategy,
- allowed files,
- reconciliation strategy.

Do not assign overlapping mutable scope without explicit coordination.

---

# 4. Good subagent uses

- code archaeology,
- primary-source research,
- architecture alternatives,
- security review,
- test strategy,
- performance analysis,
- independent diff review.

Bad uses:

- many agents doing the same vague task,
- recursive uncontrolled delegation,
- "improve everything",
- outsourcing final judgment without synthesis.

Lead agent owns synthesis and final recommendation.

---

# 5. Research-agent constraint

One bounded question per research agent.

Prevent uncontrolled recursive spawning.

The parent agent owns source quality, reconciliation, and conclusions.

---

# 6. Execution surface routing

## Fragile/interactive surfaces
Use for short inspection, small edits, quick tests, immediate HITL decisions.

Prefer small resumable steps and frequent checkpoints.

## Durable/long-running surfaces
Use for repository-wide analysis, long research, large implementation, architecture/security review, extended testing/docs.

Execution durability does not make the worker authoritative.

---

# 7. GPT Work / durable-worker packet

Before handing off, checkpoint SSoT.

Provide:

```text
ROLE
PROJECT
REPOSITORY
ABSOLUTE PATH
BRANCH
HEAD
DIRTY STATE
ACTIVE TASK
OBJECTIVE

READ FIRST
- repo agent instructions
- project plan
- current work
- handoff
- ADRs
- spec/tickets

AUTHORITATIVE SOURCES

ALLOWED SCOPE
FORBIDDEN SCOPE

MICRO-STEPS

ACCEPTANCE CRITERIA

VERIFICATION

EVIDENCE REQUIRED

CHECKPOINT REQUIREMENTS

EXPECTED OUTPUT

HANDOFF DESTINATION
```

For difficult repository-wide work recommend the highest reasoning effort actually available, e.g.:

`Effort: UltraHigh / Highest Available`

---

# 8. Worker completion is not final authority

Worker reports must be reconciled with:

- project SSoT,
- actual repository state,
- deterministic evidence,
- required independent review.

A worker saying `DONE` is a claim until verified.

---

# 9. Human action handoff

When only the human can proceed, stop at the smallest blocking point and provide:

- WHAT I NEED YOU TO DO
- WHY IT IS REQUIRED
- EXACT STEPS
- WHAT SUCCESS LOOKS LIKE
- WHAT TO SEND BACK / WHAT HAPPENS NEXT

Do not bury manual steps inside a long report.
