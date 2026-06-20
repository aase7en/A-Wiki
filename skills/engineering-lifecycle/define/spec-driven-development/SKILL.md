---
name: spec-driven-development
description: Creates specs before coding. Use when starting a new project, feature, or significant change and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Spec-Driven Development

## Overview

Write a structured specification before writing any code. The spec is the shared source of truth — it defines what we're building, why, and how we'll know it's done. Code without a spec is guessing.

## When to Use

- Starting a new project or feature
- Requirements are ambiguous or incomplete
- The change touches multiple files or modules
- You're about to make an architectural decision
- The task would take more than 30 minutes to implement

**When NOT to use:** Single-line fixes, typo corrections, or changes where requirements are unambiguous.

## The Gated Workflow

```
SPECIFY → PLAN → TASKS → IMPLEMENT
   │       │       │        │
   ▼       ▼       ▼        ▼
 Human   Human   Human    Human
 reviews reviews reviews  reviews
```

### Phase 1: Specify

Start with a high-level vision. Ask clarifying questions until requirements are concrete.

**Surface assumptions immediately:**
```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL
4. We're targeting modern browsers only
→ Correct me now or I'll proceed with these.
```

**Write a spec covering six core areas:**

1. **Objective** — What are we building and why? What does success look like?
2. **Commands** — Full executable commands with flags (build, test, lint, dev)
3. **Project Structure** — Where code, tests, and docs live
4. **Code Style** — One real code snippet showing your style
5. **Testing Strategy** — Framework, coverage, test levels
6. **Boundaries** — Always do / Ask first / Never do

### Phase 2: Plan

With the validated spec, generate a technical implementation plan:
1. Identify major components and their dependencies
2. Determine implementation order
3. Note risks and mitigation strategies
4. Define verification checkpoints

### Phase 3: Tasks

Break the plan into discrete, implementable tasks:
- Each task completes in one focused session
- Each has explicit acceptance criteria
- Each includes a verification step
- Tasks ordered by dependency, not importance
- No task requires changing more than ~5 files

### Phase 4: Implement

Execute tasks one at a time following `incremental-implementation` and `test-driven-development`. Use `context-engineering` to load the right spec sections at each step.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is simple, I don't need a spec" | Simple tasks don't need *long* specs, but they still need acceptance criteria. A two-line spec is fine. |
| "I'll write the spec after I code it" | That's documentation, not specification. The spec's value is in forcing clarity *before* code. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. |
| "Requirements will change anyway" | That's why the spec is a living document. An outdated spec is still better than no spec. |

## Red Flags

- Starting to write code without any written requirements
- Asking "should I just start building?" before clarifying what "done" means
- Implementing features not mentioned in any spec or task list
- Making architectural decisions without documenting them

## Verification

- [ ] The spec covers all six core areas
- [ ] The human has reviewed and approved the spec
- [ ] Success criteria are specific and testable
- [ ] Boundaries (Always/Ask First/Never) are defined
- [ ] The spec is saved to a file in the repository
