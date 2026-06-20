---
name: deprecation-and-migration
description: Remove old systems and migrate users safely. Use when removing old systems, migrating users, or sunsetting features. Use before making a breaking change to plan the migration path.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Deprecation and Migration

## Overview

Code is a liability, not an asset. Every line of code costs maintenance, cognitive load, and deploy time. Removing code responsibly — without breaking users — is a core engineering skill. This skill covers compulsory vs. advisory deprecation patterns, migration strategies, and zombie code detection.

## When to Use

- Deprecating an API, endpoint, or library
- Removing or retiring a feature
- Migrating users to a new system
- Cleaning up feature flags after rollout
- Any change that removes something from the public interface

**When NOT to use:** Internal refactoring where the public API doesn't change.

## Deprecation Patterns

### Compulsory Deprecation

Old system must be removed by a deadline:
1. Announce deprecation with timeline (N months minimum)
2. Enable migration path (migration script, converter, parallel system)
3. Monitor migration progress
4. After deadline: remove old system, keep migration path for stragglers
5. After grace period: remove migration path

### Advisory Deprecation

Old system can remain but new users should use the new system:
1. Mark old system as "deprecated" in docs
2. New development uses new system
3. Old systems maintain backward compatibility
4. No removal date — let usage decay naturally

## Migration Strategies

### Parallel Run
Both systems run simultaneously until all users migrate:
- New traffic goes to new system
- Old traffic continues on old system
- After completion: redirect all traffic, remove old system

### Coexistence
Both systems exist but serve different users:
- Old users stay on old system
- New users go to new system
- Old users migrate at their own pace

### Strangler Fig
Gradually replace functionality:
- Route one feature at a time to the new system
- Each route switches independently
- When all features are switched, remove the old system

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Let's just keep the old code, it doesn't hurt anyone" | Dead code costs maintenance, increases surface area for bugs, and confuses new engineers. Delete it. |
| "We'll remove it after the migration is complete" | "After the migration" never comes. Remove as you go. |
| "Nobody uses this API anymore, we can just delete it" | "Nobody" is a dangerous assumption. Deprecate formally, then verify usage dropped before removal. |
| "The migration is simple, users can just update their code" | Not all users follow your releases. Provide a migration path. |

## Red Flags

- Removing code without checking who depends on it
- No deprecation warning period before removal
- Breaking changes in a minor version
- No migration script or migration guide
- "We only have one user, we can ask them" — that's still a user who needs a migration path
- Killing a service without draining in-flight requests
- Zombie code — code that is never executed but is maintained "just in case"

## Verification

- [ ] Deprecation timeline documented and announced
- [ ] Migration path exists (or justified why not needed)
- [ ] Usage/telemetry confirms old system is unused before removal
- [ ] No active users will break by removing the code
- [ ] Old code is actually deleted (not commented out)
- [ ] If API: version bump to indicate breaking change
