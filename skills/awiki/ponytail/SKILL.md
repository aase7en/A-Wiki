---
name: ponytail
description: "Scoped minimal-solution discipline: question whether the task needs to exist (YAGNI), reach for the smallest existing tool/pattern first (stdlib > dependency, one line > fifty), and checkpoint only the prior context that materially helps continuation. Use when work risks over-engineering, bloat, or speculative generality."
version: 1.0.0
author: A-Wiki (adapted from community ponytail/lazy-solution skills; scope guidance only, no upstream runtime)
domain: [engineering, productivity]
lifecycle_phase: build
category: discipline
agents: [all]
status: canonical
invocation: auto
invocation_hint: "/Ponytail"
triggers:
  - "ponytail"
  - "lazy mode"
  - "simplest solution"
  - "minimal solution"
  - "yagni"
  - "shortest path"
  - "over-engineering"
  - "ง่ายที่สุด"
---

# Ponytail — laziest solution that actually works

Forces the smallest change that genuinely solves the stated problem, and keeps
just enough prior context to continue work without re-reading everything.

## The ladder (climb only when the rung below cannot do the job)

1. Does this task need to exist at all? (YAGNI first — deleting a requirement
   beats writing code for it)
2. Standard library / built-in platform feature before any dependency
3. Existing project utility or pattern before a new abstraction
4. One line of code before fifty; a flag before a config schema; a config
   before a database table
5. Copy-paste-once before extracting a reusable module (extract only on the
   second real occurrence)

## Prior-context checkpointing (the continuity half)

When a task spans turns/sessions, checkpoint ONLY:

- The current objective in one sentence
- Decisions already made + the one-line why
- The exact resume point (file:line / command / URL)
- Open blockers, if any

Everything else (tool transcripts, exploratory reads, failed attempts) stays
out of the checkpoint — it is recoverable from history when truly needed.
Reference, don't inline.

## Hard rules

- Never weaken a security, correctness, or review gate to be "simpler" —
  laziness applies to ceremony, never to safety
- Never delete tests to make a change smaller; if a test forces fifty lines,
  the need is real
- Explicit user requests outrank this skill (they ask for the general solution,
  they get the general solution)

## Relationship to other entries

- `caveman` compresses OUTPUT style; this skill compresses SOLUTION SHAPE and
  carried CONTEXT. Different axes; combine freely.
- `token-optimization` is the measurement/tooling side of the same economy
  goal (A-Wiki #76 three-tier AUTO_ON_DEMAND family).
