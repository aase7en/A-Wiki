---
name: planning-and-task-breakdown
description: Decompose specs into small, verifiable tasks with acceptance criteria and dependency ordering. Use when you have a validated spec and need implementable units. Use before starting any multi-file implementation.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Planning and Task Breakdown

## Overview

A validated spec defines *what* to build. This skill breaks it into *how* to build it: small, verifiable tasks with clear boundaries. Good task breakdown turns "implement the feature" into a sequence of safe, testable steps.

## When to Use

- You have a spec and need implementable units
- Before starting any multi-file or multi-step implementation
- You're about to start coding and need a roadmap

**When NOT to use:** Single-line fixes or changes so small the task is obvious.

## The Process

### Step 1: Review the Spec

Read the spec and extract:
- Core functionality (must-have features)
- Nice-to-have (can defer)
- Dependencies (what must exist before what)
- Risk areas (what could go wrong)

### Step 2: Identify Task Boundaries

Slice horizontally or vertically:

**Vertical slices (preferred):**
```
Slice 1: Create a task (DB + API + basic UI)
Slice 2: List tasks (query + API + UI)
Slice 3: Edit a task (update + API + mock modal)
Slice 4: Delete a task (delete + API + confirmation)
```

**Risk-first slicing:**
```
Slice 1: Prove the WebSocket connection works (highest risk)
Slice 2: Build real-time updates on the proven connection
Slice 3: Add offline support
```

### Step 3: Write Tasks

Each task should be:
- Completable in one focused session (30-90 minutes)
- No more than ~5 files changed
- Has explicit acceptance criteria
- Has a verification step

**Task template:**
```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done]
  - Verify: [How to confirm — test command, build, manual check]
  - Files: [Which files will be touched]
```

### Step 4: Order by Dependency

```
Phase 1: Foundation (no dependencies)
  Task 1: Database schema
  Task 2: Data access layer

Phase 2: Core Feature (depends on Phase 1)
  Task 3: API endpoint
  Task 4: Basic UI component

Phase 3: Polish (depends on Phase 2)
  Task 5: Error handling
  Task 6: Edge cases
```

### Step 5: Human Review

Present the task plan to the user. Don't proceed until approved:
- Are these the right slices?
- Is the order correct?
- Are acceptance criteria clear?
- Any missing tasks?

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I can figure it out as I go" | You'll miss dependencies, duplicate work, or build the wrong thing first. |
| "Task breakdown takes too long" | A 10-minute breakdown saves hours of mid-implementation pivots. |
| "The tasks are obvious, no need to write them" | Writing them surfaces implicit assumptions and helps the human correct them early. |

## Red Flags

- Tasks too large (more than ~5 files or 90 minutes)
- Acceptance criteria missing or vague ("works well")
- No verification step for tasks
- All tasks ordered in parallel (no dependency analysis)
- Human skipped the review step

## Verification

- [ ] Spec has been reviewed and validated
- [ ] Each task has acceptance criteria and verification step
- [ ] Tasks are ordered by dependency
- [ ] Human has approved the task plan
- [ ] Risk areas identified and addressed in sequencing
