---
name: awiki-lifecycle-router
description: Discovers and invokes the right A-Wiki lifecycle skill. Use when starting a session or when you need to discover which skill applies to the current task. This is the meta-skill that governs how all engineering lifecycle skills are discovered and invoked. Also maps A-Wiki-specific intents (ingest-source, lint-wiki, pharmacy-order).
---

# A-Wiki Lifecycle Router

**source**: adapted from addyosmani/agent-skills using-agent-skills skill (MIT)

## Overview

The engineering lifecycle skills in `skills/engineering-lifecycle/` encode the workflows senior engineers use. Each skill has steps, verification gates, and anti-rationalization tables. This meta-skill helps you discover and apply the right one.

A-Wiki also has domain-specific skills (wiki management, pharmacy, research, delegation) that are outside the lifecycle. These are discoverable through the skill tool.

## Skill Discovery

### Engineering Lifecycle

```
Task arrives
    │
    ├── Don't know what you want yet? ────→ grill-me (A-Wiki skill)
    ├── New project/feature/change? ───────→ define/spec-driven-development
    ├── Have a spec, need tasks? ──────────→ plan/planning-and-task-breakdown
    ├── Implementing code? ────────────────→ build/incremental-implementation
    │   ├── UI work? ────────────────────→ build/frontend-ui-engineering
    │   ├── API work? ──────────────────→ build/api-and-interface-design
    │   ├── Need doc-verified code? ─────→ build/source-driven-development
    │   └── Stakes high / unfamiliar? ───→ build/doubt-driven-development
    ├── Writing/running tests? ────────────→ build/test-driven-development
    ├── Something broke? ──────────────────→ debug-mantra (A-Wiki skill)
    ├── Reviewing code? ───────────────────→ scrutinize (A-Wiki skill)
    │   ├── Too complex? ───────────────→ review/code-simplification
    │   ├── Security concerns? ─────────→ review/security-and-hardening
    │   └── Performance concerns? ─────→ review/performance-optimization
    ├── Committing/branching? ─────────────→ ship/git-workflow-and-versioning
    ├── CI/CD pipeline work? ─────────────→ ship/ci-cd-and-automation
    ├── Writing docs/ADRs? ────────────────→ ship/documentation-and-adrs
    ├── Adding logs/metrics/alerts? ───────→ ship/observability-and-instrumentation
    └── Deploying/launching? ─────────────→ ship/shipping-and-launch
```

### A-Wiki Domain-Specific Intents

```
    ├── Wiki ingest (URL/pasted text/file)? → ingest-source (A-Wiki skill)
    ├── Wiki health check / lint? ──────────→ lint-wiki (A-Wiki skill)
    ├── Wiki search? ───────────────────────→ wiki-search-local (A-Wiki skill)
    ├── Pharmacy order lookup? ────────────→ pharmacy-order-lookup (A-Wiki skill)
    ├── Cross-domain synthesis? ───────────→ ask-notebooklm (A-Wiki skill)
    ├── Multi-model delegation? ───────────→ delegate-subagent (A-Wiki skill)
    ├── Refine vague ideas? ───────────────→ brainstorm-before-build (A-Wiki skill)
    └── Extract what user wants? ──────────→ grill-me (A-Wiki skill)
```

## Core Operating Behaviors

These apply at all times, across all skills:

1. **Surface assumptions** — Before implementing, explicitly state what you're assuming.
2. **Manage confusion actively** — No silent guesses. Name the confusion, ask.
3. **Push back when warranted** — Quantify downsides, propose alternatives.
4. **Enforce simplicity** — Can this be done in fewer lines?
5. **Maintain scope discipline** — Touch only what you're asked to touch.
6. **Verify, don't assume** — "Seems right" is never sufficient.

## Lifecycle Sequence

For a complete feature, the typical skill sequence is:

```
1.  grill-me                     → Extract what the user actually wants
2.  brainstorm-before-build      → Clarify intent, refine vague ideas before building
3.  define/spec-driven-development → Define what we're building
4.  plan/planning-and-task-breakdown → Break into verifiable chunks
5.  build/context-engineering    → Load the right context
6.  build/source-driven-development → Verify against official docs
7.  build/incremental-implementation → Build slice by slice
8.  build/test-driven-development → Prove each slice works
9.  build/doubt-driven-development → Cross-examine non-trivial decisions
10. scrutinize + review/security-and-hardening → Review before merge
11. review/code-simplification  → Reduce unnecessary complexity
12. ship/documentation-and-adrs  → Document decisions
13. ship/shipping-and-launch     → Deploy safely
```

## Quick Reference

| Phase | Skill | One-Line Summary |
|-------|-------|-----------------|
| Define | `spec-driven-development` | Requirements and acceptance criteria before code |
| Define | `brainstorm-before-build` (A-Wiki) | Clarify intent then pick approach before building |
| Plan | `planning-and-task-breakdown` | Decompose into small, verifiable tasks |
| Build | `incremental-implementation` | Thin vertical slices, test each before expanding |
| Build | `test-driven-development` | Failing test first, then make it pass |
| Build | `doubt-driven-development` | Adversarial fresh-context review of non-trivial decisions |
| Build | `source-driven-development` | Verify against official docs before implementing |
| Build | `frontend-ui-engineering` | Production-quality UI with accessibility |
| Build | `api-and-interface-design` | Stable interfaces with clear contracts |
| Build | `context-engineering` | Right context at the right time |
| Verify | `debug-mantra` (A-Wiki) | Four-mantra debugging discipline |
| Verify | `browser-testing-with-devtools` | Chrome DevTools MCP for runtime verification |
| Review | `scrutinize` (A-Wiki) | Outsider-perspective end-to-end review |
| Review | `code-simplification` | Preserve behavior while reducing complexity |
| Review | `security-and-hardening` | OWASP prevention, input validation |
| Review | `performance-optimization` | Measure first, optimize only what matters |
| Ship | `git-workflow-and-versioning` | Atomic commits, clean history |
| Ship | `ci-cd-and-automation` | Automated quality gates on every change |
| Ship | `deprecation-and-migration` | Remove old systems and migrate users safely |
| Ship | `documentation-and-adrs` | Document the why, not just the what |
| Ship | `observability-and-instrumentation` | Structured logs, RED metrics, traces |
| Ship | `shipping-and-launch` | Pre-launch checklist, monitoring, rollback plan |

## Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order. Don't skip verification.
3. **Multiple skills can apply.** Chain them as the task demands.
4. **When in doubt, start with a spec.** If non-trivial and no spec exists, begin with `spec-driven-development`.
