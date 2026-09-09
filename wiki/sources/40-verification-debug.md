---
type: source
title: "40 — VERIFICATION / REVIEW / DEBUGGING"
slug: 40-verification-debug
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/40-VERIFICATION-DEBUG.md
tags: []
---

# 40 — VERIFICATION / REVIEW / DEBUGGING

## Activate when

- implementation exists,
- reviewing a diff,
- investigating a bug,
- tests/build fail,
- CI failure needs classification,
- a deep technical defect is suspected.

---

# 1. Verification hierarchy

Prefer evidence in this order where practical:

1. deterministic reproducer,
2. automated test/check,
3. actual diff/state inspection,
4. runtime evidence/logs/traces,
5. independent review,
6. model reasoning alone.

AI confidence is not verification.

---

# 2. Independent review

For material changes, prefer a reviewer that did not author the implementation.

Review the actual artifact.

Always preserve the two axes:

## Standards
Was it built correctly according to repository rules?

## Spec
Did it build the correct requested behavior?

Do not let one pass hide failure of the other.

---

# 3. Code review is not deep bug hunting

Normal standards/spec review may miss:

- race conditions,
- stale state,
- retries,
- duplicate execution,
- partial failure,
- sequencing bugs,
- boundary input,
- resource leaks,
- time/date issues,
- hidden trust-boundary bypasses.

Escalate high-risk candidates to `41-E2E-AUDIT.md`.

---

# 4. Debugging principle

Start with a reproducible signal, not a theory.

Ideal invariant:

`ONE NAMED COMMAND/SCENARIO → RED WHEN BUG EXISTS → GREEN WHEN FIXED`

---

# 5. Debug loop

For a material bug:

1. reproduce,
2. verify it matches the reported failure,
3. minimize,
4. define a tight feedback loop,
5. rank hypotheses when useful,
6. define falsifiable predictions,
7. instrument,
8. test hypotheses,
9. identify root cause,
10. define blast radius,
11. add regression coverage,
12. implement minimal repair,
13. remove temporary instrumentation,
14. self-review,
15. independent review where warranted,
16. targeted tests,
17. full relevant suite,
18. realistic E2E if behavior/risk warrants it.

Do not patch symptoms while causal defect remains.

---

# 6. Deterministic verification

Depending on project run applicable:

- unit tests,
- integration tests,
- contract tests,
- typecheck,
- lint,
- build,
- schema validation,
- migration tests,
- static analysis,
- security scanning,
- snapshot comparison,
- property/fuzz tests,
- benchmark/performance checks.

Record:

- exact command,
- environment,
- result,
- pass/fail counts,
- warnings,
- artifacts.

---

# 7. Test integrity

Never get green by:

- deleting valid tests,
- weakening assertions without justification,
- broad skipping,
- swallowing errors,
- disabling checks,
- hiding failures,
- declaring flaky tests irrelevant without investigation.

If a test is wrong, document why before changing it.

---

# 8. Failure classification

Distinguish:

- `CODE_FAILURE`
- `TEST_ASSERTION_FAILURE`
- `BUILD_FAILURE`
- `TOOL_FAILURE`
- `INFRA_FAILURE`
- `TRANSPORT_FAILURE`
- `AUTH_FAILURE`
- `PERMISSION_FAILURE`
- `DEPENDENCY_FAILURE`
- `ENVIRONMENT_FAILURE`
- `CI_FAILURE`
- `DEPLOYMENT_FAILURE`
- `UNKNOWN_FAILURE`

A transport/tunnel crash is not evidence that code failed.

A tool timeout is not proof the task did not complete.

Inspect state before retrying.

---

# 9. Diagnostic artifact safety

Logs, traces, HAR files, DB dumps, screenshots, repro payloads may contain secrets/PII/PHI.

Redact before committing, publishing, attaching to PR/issues, or sending to external services.

---

# 10. Verification report

Preserve:

- objective,
- baseline/fixed point,
- commands,
- results,
- review findings,
- defects,
- root causes,
- repairs,
- remaining risks,
- next safe action.

If verification assumptions changed during a repair, rerun the affected gates.
