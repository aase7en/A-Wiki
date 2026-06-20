---
name: documentation-and-adrs
description: Architecture Decision Records, API documentation, and inline documentation standards — document the why. Use when making architectural decisions, changing APIs, or shipping features that others will maintain.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Documentation and ADRs

## Overview

Documentation lives at three levels: high-level ADRs for architectural decisions, API docs for interface consumers, and inline code comments for maintainers. The most important thing to document is the *why* — the context and reasoning behind a decision — not the *what* (the code already says that).

## When to Use

- Making an architectural decision (use ADR)
- Changing a public API (update API docs)
- Adding non-obvious logic (add inline comment)
- Shipping a feature (update README or user docs)
- Onboarding a new developer (update setup docs)

**When NOT to use:** Obvious patterns that match existing conventions. Well-named code is its own documentation.

## Architecture Decision Records

ADR format (based on Michael Nygard's template, adapted for A-Wiki):

```markdown
# ADR-001: Use SQLite for Local Wiki Index

**Date**: 2026-06-20
**Status**: Accepted

## Context
A-Wiki needs local full-text search without requiring an external database server.
Options considered: SQLite FTS5, Elasticsearch, Meilisearch, grep-based.

## Decision
Use SQLite with FTS5 extension. It ships with Python 3, requires no server process,
and provides ranked full-text search out of the box.

## Consequences
- Positive: Zero-infrastructure search, fast for <100k documents
- Negative: Not suitable for multi-user or distributed search
- Neutral: FTS5 syntax differs from standard SQL LIKE queries

## Compliance
- Stays within A-Wiki Iron Law: Cost-first, Level -1 (free, offline)
- No external dependencies beyond Python stdlib
```

## API Documentation

Every API endpoint should document:
- Purpose (one sentence)
- Method + path
- Request schema (required vs optional fields)
- Response schema (success + error)
- Auth requirements
- Rate limits
- Example curl command

## Inline Comments

- Document *why* not *what*: `// Use retry logic because the upstream API is eventually consistent`
- Mark tricky code: `// WARNING: This regex must match the format from [external system]`
- Reference ADRs: `// See ADR-005 for why we chose PostgreSQL over MySQL`
- Do NOT document obvious patterns: `// Increment counter` above `counter++`

## Keeping Docs Alive

- Update docs in the same PR as the code change (not a separate docs PR)
- Stale docs are worse than no docs — they actively mislead
- Run `lint-wiki` before closing any wiki-related PR
- When a spec changes, update the spec file and any affected ADRs

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code is self-documenting" | Clean code explains *what* but not *why*. The reasoning behind decisions is invisible in the code. |
| "I'll document it after the code is stable" | You won't. You'll move to the next task. Document in the same commit. |
| "ADRs are bureaucratic overhead" | ADRs are the cheapest way to save future-you from reverse-engineering past decisions. |
| "Nobody reads documentation" | The people who need documentation (new team members, future maintainers) are the ones you don't hear from until they're blocked. |

## Red Flags

- PRs with code changes but no doc updates
- ADRs missing date or status fields
- Comments that explain *what* rather than *why*
- Outdated README that contradicts the code
- Decisions re-litigated because the original reasoning was not recorded
- "Magic" values, regexes, or config without explanation

## Verification

- [ ] ADR written for architectural decisions (with status and date)
- [ ] API endpoint documented (purpose, request, response, auth)
- [ ] Non-obvious code has *why* comments
- [ ] Spec or README updated if the change affects external behavior
- [ ] No stale documentation remaining
