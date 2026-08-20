# A-Wiki Agent Review Bus — Implementation Plan

> Status: Architecture plan approved for the A-Wiki vNext migration; the Phase 3 protocol contract is durable and the first automated adapter remains Phase 8 scope.
> Track: Parallel architecture track; implementation must not bypass the active phase gates.
> Current migration state: Phase 6 is **CHANGES_REQUIRED**; Phases 7+ are **NOT_STARTED**.
> Role contract: choose a claimed executor and an independent reviewer by capability, trust, availability, cost/latency envelope, and required evidence. Provider/model names are runtime candidates, not policy.

## 1. Purpose

The goal is to remove the human copy/paste relay between AI agents.

A-Wiki should provide a durable, vendor-neutral review channel where an executor agent can publish work, a reviewer agent can return structured findings, and the executor can fix/retest/re-submit without requiring the user to manually transfer long prompts between tools.

A-Wiki must treat the transport and the intelligence provider as separate concerns:

```text
Executor Agent
     |
     v
A-Wiki Review Protocol
     |
     v
GitHub PR / Review State
     |
     +---------------------+
     |                     |
     v                     v
Reviewer A             Reviewer B
hosted adapter         local/human adapter
```

The protocol must continue to work when one provider is unavailable.

---

## 2. Core Principle

Do not build direct agent-to-agent chat as the source of truth.

Use durable repository state as the coordination bus:

```text
Git branch
Pull request
Review comments
Machine-readable review state
CI / test results
Phase status
```

Benefits:

- resumable across sessions
- auditable
- model/vendor independent
- no hidden conversational state required
- compatible with human review
- supports rollback
- supports future automation

---

## 3. Roles

### Executor

Current implementation role: any claimed executor that satisfies the task's capability, trust, isolation, and verification contract. A cost-effective or local agent is preferred when it meets that contract.

Responsibilities:

```text
READ
IMPLEMENT
TEST
COMMIT
PUSH
REQUEST REVIEW
READ FINDINGS
FIX
RETEST
RESUBMIT
```

The executor must not self-approve architecture changes.

### Reviewer

Current role: an independent high-reasoning reviewer that did not implement the target change and can inspect the exact durable target and its evidence.

Compatible reviewer surfaces:

```text
hosted reviewer adapter
local reviewer adapter
human reviewer
other contract-compatible reviewer
```

Reviewer responsibilities:

```text
READ DIFF
READ PLAN
CHECK TEST EVIDENCE
CHECK ARCHITECTURE
NORMALIZE FINDINGS
RETURN VERDICT
```

### Human Owner

The user should be required only for:

- goal / priority changes
- destructive or high-risk decisions
- secrets / permissions
- production deployment
- irreversible migration
- unresolved reviewer conflict
- final merge policy when required

The user should not be required to relay normal review messages.

---

## 4. Review State Machine

```text
PLANNED
   |
   v
IMPLEMENTING
   |
   v
TESTING
   |
   v
REVIEW_REQUESTED
   |
   v
REVIEWING
   |
   +-------------------+
   |                   |
   v                   v
CHANGES_REQUIRED    APPROVED
   |                   |
   v                   v
IMPLEMENTING         CI_VERIFY
                       |
                 +-----+-----+
                 |           |
                 v           v
              FAILED      READY
                 |           |
                 v           v
           IMPLEMENTING  HUMAN_GATE / NEXT_PHASE
```

Stop states:

```text
BLOCKED
SECURITY_STOP
DATA_LOSS_STOP
SCOPE_DRIFT
REVIEW_CONFLICT
MAX_REVIEW_CYCLES
```

---

## 5. Machine-Readable Review Contract

Future canonical location:

```text
.awiki/review/
```

Suggested state file:

```text
.awiki/review/state.json
```

Example:

```json
{
  "schema": "awiki-review/v1",
  "phase": "1",
  "cycle": 2,
  "executor": "claimed-executor-1",
  "reviewer": "independent-reviewer-1",
  "status": "CHANGES_REQUIRED",
  "head_sha": "<commit>",
  "findings": [
    {
      "id": "R-001",
      "severity": "blocker",
      "area": "git-safety",
      "file": "scripts/hooks/session_start.py",
      "summary": "SessionStart can mutate a non-main branch",
      "required_action": "Prevent automatic rebase/pull outside safe main-branch conditions",
      "state": "open"
    }
  ],
  "required_tests": [
    "pytest tests/test_session_start_hook.py"
  ],
  "next_action": "FIX_AND_REREVIEW"
}
```

Do not store secrets, private data, hidden reasoning, API tokens, or full private prompts in this file.

---

## 6. Review Verdicts

Allowed verdicts:

```text
PASS
PASS_WITH_NOTES
CHANGES_REQUIRED
BLOCK
```

Finding severity:

```text
blocker
major
minor
note
```

Finding lifecycle:

```text
open
addressed
verified
wont_fix
superseded
```

Every blocker/major finding must have a stable ID such as `R-001`.

---

## 7. Review Cycle Rules

Each review cycle must be attributable to one HEAD SHA.

Executor flow:

```text
1. implement
2. run required tests
3. commit
4. push
5. request review for HEAD SHA
6. wait/read verdict
7. if CHANGES_REQUIRED:
      fix only listed findings
      rerun tests
      commit
      push
      request new review
8. if PASS/PASS_WITH_NOTES:
      run final CI gate
9. mark READY only when review + CI gates pass
```

Do not silently carry an approval from an older SHA to a newer SHA.

---

## 8. GitHub as Initial Transport

Initial transport should be GitHub because A-Wiki already uses Git and GitHub as durable project state.

Recommended mapping:

```text
branch       = implementation state
PR           = review session
commit SHA   = immutable review target
PR comments  = human-readable review
state JSON   = machine-readable normalized review
CI checks    = mechanical gate
```

The protocol must not depend on one GitHub bot identity.

---

## 9. Current Durable Mode Before Automatic Reviewer

Until the Phase 8 adapter exists, use the same contract manually against durable GitHub state:

```text
claimed executor
   |
   v
implement, test, commit, push exact SHA
   |
   v
structured review handoff
   |
   v
independent reviewer reads repository state directly
   |
   v
durable verdict and stable finding IDs
```

The user should only provide a short trigger when GitHub already contains the target and evidence. Normal findings must not require the user to relay logs or prompts between agents.

A local uncommitted snapshot may be inspected to find defects, but it cannot receive PASS because there is no immutable review target. This is the current Phase 6 condition.

## 10. Future Automatic Reviewer Mode

When a compatible reviewer becomes available, replace the manual review trigger with an adapter:

```text
GitHub event / polling
       |
       v
review adapter
       |
       v
reviewer model/provider
       |
       v
normalized awiki-review/v1 result
       |
       v
GitHub + state.json
```

The executor logic must remain unchanged.

Only the reviewer adapter changes.

---

## 11. Proposed Components

Do not implement all of these immediately. Build them incrementally after the migration foundations are stable.

Target structure:

```text
scripts/orchestration/
├─ review_protocol.py
├─ review_state.py
├─ github_review_bus.py
└─ review_loop.py

schemas/
└─ awiki-review.schema.json

docs/protocols/
└─ agent-review-loop.md

skills/awiki/
└─ a-agent-review-loop/
   └─ SKILL.md
```

Potential CLI later:

```text
awiki review status
awiki review request
awiki review ingest
awiki review resolve R-001
awiki review ready
```

---

## 12. Safety Requirements

The review loop must never automatically:

- merge to `main`
- force-push protected branches
- deploy production
- expose secrets
- publish private Drive content
- accept a failing security gate
- bypass required tests
- suppress unresolved blockers

Automatic fix/re-review is allowed only inside the isolated working branch/worktree.

---

## 13. Isolation Requirement

The DISC-001 incident established a new architectural requirement:

> Autonomous agent work should use an isolated worktree/branch whenever the main checkout contains unrelated WIP.

The review bus must preserve this invariant.

The executor must report:

```text
branch
base SHA
HEAD SHA
working tree status
changed files
```

before review starts.

---

## 14. Integration with Existing Migration

This plan is a **parallel track**, not permission to skip the existing A-Wiki vNext phases.

Current sequencing:

```text
Phase 0–5  DONE / PASS + merged
Phase 6    Hook Engine — CHANGES_REQUIRED (current)
Phase 7    Model Control Plane — NOT_STARTED
Phase 8    Eval / Promotion
           + first automated review adapter foundations — NOT_STARTED
Phase 9    A-Loop v2
           + connect review loop states to A-Loop — NOT_STARTED
Phase 10   External Modules — NOT_STARTED
Phase 11   Docs Slimming — NOT_STARTED
```

Phases 12–16 are separately defined by `docs/migration/awiki-multi-agent-orchestrator-roadmap.md` and are all **NOT_STARTED**. Do not pull that implementation into Phase 6.

## 15. Near-Term Work

### Now

Remediate only the durable Phase 6 findings P6-R01..P6-R07 after the local identity, claim, worktree, and dirty-state gates succeed. Preserve the current work order and do not overwrite uncommitted work.

### After remediation

Run the required Phase 6 gates, commit and push an attributable implementation SHA, then request independent review of that exact SHA. An approval of an older or uncommitted snapshot is invalid.

### Later phases

- Phase 7 owns the model/provider control plane and remains NOT_STARTED.
- Phase 8 owns the first automated review transport/adapter foundations.
- Phase 9 connects review-loop states to A-Loop.
- Phases 12–16 own the wider Conductor/orchestrator service and operator surface.

## 16. Acceptance Criteria for Agent Review Bus v1

The first operational version is complete when:

- executor can publish a review request without human copy/paste
- reviewer can target an exact HEAD SHA
- findings have stable IDs
- executor can ingest findings automatically
- fixes can be mapped back to finding IDs
- tests are re-run after fixes
- new SHA invalidates old approval
- CI status is included in readiness
- unresolved blockers prevent READY
- no automatic merge to main
- state survives process/session restart
- reviewer implementation can be swapped without changing executor protocol

---

## 17. Ultimate Workflow

```text
USER GOAL
   |
   v
A-Wiki Router / Plan
   |
   v
Executor
   |
   v
Tests
   |
   v
GitHub Review Bus
   |
   v
Reviewer Agent
   |
   +---- CHANGES_REQUIRED ----+
   |                           |
   v                           |
Executor Fix <-----------------+
   |
   v
Retest / Re-review
   |
   v
PASS + CI GREEN
   |
   v
READY_FOR_HUMAN or NEXT_PHASE
```

The human becomes the owner of goals and high-risk decisions, not the transport layer between agents.
