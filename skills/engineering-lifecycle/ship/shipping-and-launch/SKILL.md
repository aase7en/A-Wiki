---
name: shipping-and-launch
description: Pre-launch checklists, feature flag lifecycle, staged rollouts, rollback procedures, monitoring setup. Use when preparing to deploy to production.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Shipping and Launch

## Overview

Shipping is a process, not an event. Launch checklists prevent the common mistakes that happen under release pressure: missing monitoring, incomplete rollback plans, unannounced breaking changes. Faster is safer — meaning automated pipelines and small increments are safer than manual releases and giant batches.

## When to Use

- Preparing to deploy a feature to production
- Before any production release
- Coordinating a multi-service launch
- Reviewing the go/no-go decision for a release

**When NOT to use:** Local development or CI-only changes.

## Pre-Launch Checklist

### Code & Config
- [ ] All code changes reviewed (via `scrutinize` or person fan-out)
- [ ] Feature flag configured (disabled by default for rollout)
- [ ] Database migrations tested (forward + rollback)
- [ ] Configuration validated in staging environment
- [ ] Third-party API changes verified

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass for the critical user journey
- [ ] Manual smoke test in staging

### Monitoring & Observability
- [ ] RED metrics configured for new endpoints
- [ ] At least one symptom-based alert with runbook
- [ ] Dashboard updated to show new feature metrics
- [ ] Logs flowing and searchable
- [ ] Rollback triggers defined (what metric threshold triggers rollback?)

### Communication
- [ ] Release notes drafted (if user-facing)
- [ ] On-call engineer notified
- [ ] Dependent teams notified
- [ ] Rollback plan documented

## Staged Rollout

```
Stage 1: 1% of users   ← watch metrics for 1 hour
Stage 2: 10% of users  ← watch metrics for 2 hours
Stage 3: 50% of users  ← watch metrics for 4 hours
Stage 4: 100% of users ← watch metrics for 24 hours
```

**Go/no-go at each stage:**
- Go: metrics normal, no alerts, no bug reports
- Hold: minor issues, fix before expanding
- Rollback: critical issues, disable feature flag

## Rollback Plan

Every launch needs a rollback plan:
- **Feature flag off**: fastest — disable the flag
- **Code revert**: if feature flag is not sufficient
- **Database revert**: if schema migration is involved
- **DNS/Config revert**: if infrastructure changed

Define the threshold for automatic rollback:
- Error rate increase > 1%
- P99 latency increase > 500ms
- Any P0 or P1 incident related to the change

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We've tested everything, we don't need a staged rollout" | Staging is never production. Always stage the rollout. |
| "The rollback is just reverting the commit" | Schema migrations and data changes may not be safely revertable. Test the rollback. |
| "We don't need a pre-launch checklist for a small feature" | Small features have the same rollback costs when they break. Use the checklist. |
| "If it breaks, we'll fix it in the next release" | If it breaks in production, users see it before you fix it. Don't ship known-risk changes. |

## Red Flags

- No rollback plan before deployment
- No monitoring or alerts for the new feature
- Feature flag not available (all-or-nothing release)
- Launching on a Friday afternoon
- Skipping the staging deploy before production
- Not notifying on-call before the release
- Last-minute changes not reviewed

## Verification

- [ ] Pre-launch checklist completed
- [ ] Rollback plan documented and tested
- [ ] Staged rollout plan defined
- [ ] Monitoring and alerts in place
- [ ] Feature flag deployed (disabled by default)
- [ ] On-call and stakeholders notified
- [ ] Rollback triggers defined with numeric thresholds
