---
name: ci-cd-and-automation
description: Automated quality gates, shift-left testing, and deployment pipelines. Use when setting up or modifying build and deploy pipelines. Use when adding automated checks to protect code quality.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# CI/CD and Automation

## Overview

CI/CD takes the discipline of testing, linting, and verifying and makes it automatic — run on every commit, not just when someone remembers. The shift-left principle means catching issues as early as possible: lint in the editor, test on commit, security scan on push.

## When to Use

- Setting up a new project's CI pipeline
- Adding or modifying quality gates (lint, test, type-check, audit)
- Configuring deployment automation
- Adding infrastructure-as-code checks
- Reviewing CI pipeline reliability or speed

**When NOT to use:** The change has no automation component.

## Principles

### Shift Left
Move quality checks as early in the pipeline as possible:
```
EDITOR: lint-on-save, type checking
  → PRE-COMMIT hook: lint, format checks
    → CI COMMIT: unit tests, type check, build
      → CI PR: integration tests, security scan, E2E tests
        → CI MAIN: deploy staging, integration tests
          → CD PRODUCTION: deploy, smoke test, rollback
```

### Faster Is Safer
A fast CI pipeline is a safe CI pipeline. Slow CI encourages skipping.
- Unit tests < 1 minute
- Full CI suite < 10 minutes
- Deploy < 5 minutes

### Feature Flags
Features are deployed via flags, not by branching:
- Deploy code before the feature is complete
- Toggle on for testing, toggle off for production
- Remove the flag after full rollout

## Quality Gate Pipeline

```
Stage 1: Lint + Format  ← fails on style issues (30s)
Stage 2: Type Check      ← fails on type errors (30s)
Stage 3: Unit Tests      ← fails on logic errors (2min)
Stage 4: Build           ← fails on compilation errors (1min)
Stage 5: Security Audit  ← fails on known vulnerabilities (1min)
Stage 6: Integration     ← fails on API/DB interaction (5min)
```

If Stage 2 fails, Stages 3-6 don't run (fast feedback).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI is slow, let me skip some checks" | If CI is slow, make it faster. Don't disable checks. |
| "This is just a small change, I don't need CI" | Small changes are where subtle bugs hide. Always run CI. |
| "We'll add CI later after the prototype is done" | CI from day one sets the quality baseline. Adding it later means retrofitting. |
| "Manual testing is enough for this project" | Manual testing doesn't scale and doesn't repeat. Automate what you can. |

## Red Flags

- CI pipeline longer than 10 minutes
- Tests that are skipped in CI but run locally
- Flaky tests treated as acceptable failures
- Manual deployment steps documented but not automated
- Security audit not in the pipeline
- CI passes but deploy fails (pipeline doesn't match deployment config)

## Verification

- [ ] Every quality gate is automated
- [ ] Failed gates block the pipeline (not warnings)
- [ ] CI is fast enough to run on every commit (< 10 min)
- [ ] Feature flags used for incomplete features
- [ ] Rollback is automated
- [ ] Pipeline passes for the current change
