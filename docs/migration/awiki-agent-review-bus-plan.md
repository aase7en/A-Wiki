# A-Wiki Agent Review Bus — Implementation Plan

> Status: Architecture plan approved for the A-Wiki vNext migration.
> Track: Parallel architecture track; implementation must not bypass the active phase gates.
> Current executor: ZCode / GLM 5.3.
> Current architecture reviewer: ChatGPT on demand through GitHub review handoffs.
> Future reviewers: Codex / OpenAI API / other compatible agents through the same protocol.

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
Codex                  ChatGPT/API/etc.
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

Current implementation role: `ZCode / GLM 5.3`

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

Current role while Codex quota is unavailable:

```text
ChatGPT architecture review through GitHub handoff
```

Future compatible reviewers:

```text
Codex GitHub reviewer
OpenAI API reviewer
local reviewer model
other vendor reviewer
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
  "executor": "zcode-glm-5.3",
  "reviewer": "codex",
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

## 9. Current Mode While Codex Is Unavailable

Until an automatic reviewer is available, use:

```text
GLM executor
   |
   v
push branch
   |
   v
structured review handoff
   |
   v
ChatGPT reads GitHub directly
   |
   v
verdict
```

The user should only send a short trigger such as:

```text
Review Phase 1 clean branch
```

The user should not copy full logs/diffs when GitHub already contains the data.

This is an interim mode, not the final autonomous mode.

---

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

Recommended sequencing:

```text
Phase 0  Baseline                 DONE
Phase 1  Stabilize Automation     NEXT
Phase 2  CI / Health
Phase 3  Kernel Contract
         + define review protocol as a kernel protocol
Phase 4  Project Adapter
Phase 5  Memory Layers
Phase 6  Hook Engine
Phase 7  Model Control Plane
Phase 8  Eval / Promotion
         + implement automatic review adapter foundations
Phase 9  A-Loop v2
         + connect review loop states to A-Loop
Phase 10 External Modules
Phase 11 Docs Slimming
```

Do not stop Phase 1–2 to build a large orchestrator.

---

## 15. Near-Term Work for GLM 5.3

### Now

Continue the original migration.

Phase 1 Priority #1 remains:

```text
harden scripts/hooks/session_start.py::git_pull
```

Then continue Phase 1 according to the master plan.

### During Phase 1–2

GLM should only add lightweight review handoff metadata when useful; do not create a new framework yet.

### During Phase 3

Add the formal protocol document/schema design to the Kernel Contract.

### During Phase 8–9

Implement the first automated review transport/adapter and loop.

---

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
GLM Executor
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
GLM Fix <----------------------+
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
