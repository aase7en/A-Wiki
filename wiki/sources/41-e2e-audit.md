---
type: source
title: "41 — REALISTIC E2E / DEEP-BUG HUNT / AUDIT"
slug: 41-e2e-audit
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/41-E2E-AUDIT.md
tags: []
---

# 41 — REALISTIC E2E / DEEP-BUG HUNT / AUDIT

## Activate when

- preparing a release candidate,
- user-visible or stateful system changed,
- concurrency/retry/recovery matters,
- security/privacy risk exists,
- deployment/migration is involved,
- ordinary tests are insufficient,
- user explicitly requests deep bug hunting.

Risk-proportionate: do not force heavyweight audit onto trivial changes.

---

# 1. E2E goal

Do not only ask:

> Does it run?

Ask:

> Can we make it fail in ways real users and production systems eventually will?

Test the real lifecycle where possible.

---

# 2. Scenario catalog

Choose relevant cases.

## Normal lifecycle
- first run,
- normal workflow,
- save/reload,
- complete lifecycle.

## UI states
- loading,
- empty,
- success,
- validation error,
- dependency error,
- permission denied.

## Failure
- API unavailable,
- timeout,
- filesystem failure,
- DB failure,
- degraded dependency.

## Recovery
- retry,
- resume,
- restart,
- interruption,
- partial completion.

## Idempotency
- duplicate request,
- repeated command,
- double-click,
- worker retry.

## Concurrency
- two users,
- two workers,
- simultaneous writes,
- stale optimistic state.

## Input boundaries
- empty/null,
- malformed,
- huge,
- duplicate,
- unexpected encoding.

## State boundaries
- stale data,
- old schema,
- expired session,
- changed permissions.

## Compatibility
- upgrade,
- migration,
- rollback,
- existing persisted data.

## UX/accessibility
- mobile/desktop,
- breakpoints,
- keyboard,
- semantics,
- error communication.

## Localization/time
- timezone,
- locale,
- date boundary,
- DST when relevant,
- multilingual content.

## Performance
- realistic data volume,
- cold start,
- repeated operation,
- memory/resource growth.

## Operations
- logs,
- telemetry,
- alertability,
- diagnosability.

---

# 3. E2E failure loop

If material failure appears:

`E2E FAILURE → reproduce → root cause → regression coverage → repair → self-review → independent review → targeted tests → full relevant tests → E2E again`

Do not simply patch and advance.

---

# 4. Audit dimensions

Perform applicable audit separately from normal code review.

## Security
- trust boundaries,
- authentication,
- authorization,
- secrets,
- injection,
- unsafe deserialization,
- path/file operations,
- dependency exposure.

## Privacy
- PII/PHI,
- logs/telemetry,
- retention,
- data minimization.

## Reliability
- retries,
- idempotency,
- duplication,
- concurrency,
- timeouts,
- partial completion,
- recovery.

## Architecture
- module boundaries,
- coupling,
- layering,
- ownership,
- accidental complexity,
- future reversibility.

## Performance
- hot paths,
- memory,
- I/O,
- N+1,
- startup cost,
- repeated work.

## Operations
- observability,
- metrics/logs,
- supportability,
- rollback.

## UX/accessibility
- interaction traps,
- responsive behavior,
- keyboard,
- semantic structure,
- error states.

## Deployment
- migrations,
- compatibility,
- config,
- rollback path.

---

# 5. Audit verdict

Use:

- `AUDIT_PASS`
- `AUDIT_PASS_WITH_NOTES`
- `AUDIT_CHANGES_REQUIRED`
- `AUDIT_BLOCKED`

Do not claim an audit occurred if only ordinary code review happened.

---

# 6. Assurance evidence

Record:

- required scenarios,
- executed scenarios,
- pass/fail,
- environment,
- screenshots/traces/logs if safe and useful,
- audit findings,
- unresolved risks,
- disposition.

A green unit suite is not a substitute for realistic system verification when the risk demands it.
