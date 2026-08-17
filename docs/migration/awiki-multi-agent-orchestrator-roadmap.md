# A-Wiki Multi-Agent Orchestrator — Roadmap Extension

> Status: **Architecture roadmap — approved direction, implementation deferred behind active vNext phase gates.**
> Parent plans: `docs/migration/awiki-vnext-plan.md`, `docs/migration/awiki-agent-review-bus-plan.md`
> Architecture branch: `architect/awiki-multi-agent-orchestrator-roadmap`
> Design principle: **A-Wiki is the Team Operating System; individual AI agents are replaceable capability providers.**

---

## 1. Why this roadmap exists

The current A-Wiki migration exposed a real operational pattern:

```text
User goal
  -> ChatGPT architecture / review
  -> ZCode / GLM execution
  -> tests + GitHub
  -> ChatGPT re-review
  -> GLM remediation
```

This works, but the human owner is still partially acting as the message bus between agents. It also becomes fragile when one provider is temporarily unavailable because of quota, outage, local-tool limitations, or session constraints.

A-Wiki should evolve from a shared second brain into a **vendor-neutral AI team operating system** that can:

- run with one agent when only one is available;
- pair an executor with an independent reviewer when useful;
- split parallelizable work across multiple agents;
- substitute another capable agent when a preferred provider is unavailable or quota-exhausted;
- preserve one durable task/review/memory state across agent vendors and sessions;
- keep humans responsible for goals and high-risk decisions, not routine message relay.

The system must degrade gracefully. Multi-agent execution is an optimization, **not a dependency for correctness**.

---

## 2. North-star architecture

```text
                              HUMAN OWNER
                                   |
                          Goal / Priority / Gates
                                   |
                                   v
                         +-------------------+
                         |      A-WIKI       |
                         | TEAM OPERATING OS |
                         +---------+---------+
                                   |
            +----------------------+----------------------+
            |                      |                      |
            v                      v                      v
      ORCHESTRATION            SHARED STATE          GOVERNANCE
      - task routing           - memory              - privacy
      - mode choice            - handoffs            - claims
      - fallback               - review state        - safety
      - reassign               - Git/PR state        - budget
      - concurrency            - evidence            - human gates
            |                                             |
            +----------------------+----------------------+
                                   |
                     Capability-based agent pool
                                   |
       +----------------+----------+----------+----------------+
       |                |                     |                |
       v                v                     v                v
   OpenAI/Codex      ZCode/GLM           Claude Code       Kilo/etc.
   ChatGPT/Work      Antigravity         Coworker          future agent
```

Core invariant:

> **One brain, many agents, many projects, many models, one durable workflow and governance layer.**

---

## 3. Agent identity must be capability-based, not vendor-hardcoded

Do not encode workflow policy as:

```yaml
reviewer: codex
executor: glm-5.3
```

Prefer:

```yaml
executor:
  requires:
    - repository-write
    - shell
    - tests
  preferred:
    - zcode-glm
    - codex
    - claude-code
  fallback: any-capable-agent

reviewer:
  requires:
    - repository-read
    - code-review
    - deep-reasoning
  independent_from_executor: true
  preferred:
    - codex
    - chatgpt
    - claude
  fallback: any-capable-agent
```

Provider/model names are runtime candidates. The stable contract is capability + policy.

This prevents A-Wiki from being redesigned every time a model version, product, CLI, quota policy, or vendor changes.

---

## 4. Execution modes

`AUTO` should be the default policy. The orchestrator selects the lightest mode that satisfies risk and verification requirements.

### SOLO

One agent plans, implements, tests, and performs self-review.

Use when:

- task is localized and low-risk;
- deterministic tests are strong;
- only one capable agent is available;
- all independent reviewers are quota-exhausted/offline.

If independent review is required but unavailable:

```yaml
independent_review: pending
readiness: conditionally_ready
```

Never pretend self-review is independent review.

### PAIR

```text
Executor -> Reviewer -> Executor remediation -> Reviewer
```

Default for medium/high-risk code changes.

### ARCHITECT_EXECUTOR

```text
Architect/Reviewer
      |
      v
Execution Agent
      |
      v
Mechanical Verification
      |
      v
Architecture Re-review
```

This is the mode proven in the current vNext migration.

### PARALLEL

Independent work packages are assigned to separate agents/worktrees.

Example:

```text
Task A -> GLM       backend
Task B -> Claude    tests
Task C -> Kilo      documentation
                 -> integration/review gate
```

Only use when file/task claims prove the packages do not collide.

### COUNCIL

Multiple agents independently analyze one decision; one synthesizer produces the decision record.

Use for architecture, security, migrations, or uncertain tradeoffs — not routine edits.

### SWARM

Planner decomposes work, several executors operate in parallel, tester/reviewer aggregates results.

This is a late-stage capability. Do not make SWARM a prerequisite for the MVP.

---

## 5. Agent Availability Registry

A-Wiki needs a runtime view of which workers are actually usable now.

Conceptual schema:

```yaml
schema: awiki-agent-registry/v1
agents:
  - id: zcode-glm
    adapter: zcode
    status: available
    capabilities:
      - repository-read
      - repository-write
      - shell
      - long-context
      - testing
    quota:
      state: unknown
    health:
      last_seen: runtime-only

  - id: codex
    adapter: openai-codex
    status: quota_exhausted
    capabilities:
      - repository-read
      - repository-write
      - code-review
      - testing
    quota:
      state: exhausted
      retry_after: runtime-only
```

Allowed availability states should include at least:

```text
AVAILABLE
BUSY
DEGRADED
QUOTA_LOW
QUOTA_EXHAUSTED
RATE_LIMITED
COOLDOWN
OFFLINE
AUTH_REQUIRED
UNKNOWN
```

Runtime availability/quota/latency must **not** be committed as permanent Git policy.

Commit only stable capability declarations, preference policy, thresholds, and accepted architectural decisions.

---

## 6. Routing decision pipeline

```text
Task intake
   |
   v
Classify risk / complexity / domain
   |
   v
Determine required capabilities
   |
   v
Read agent availability + provider health
   |
   v
Choose execution mode
   |
   v
Rank candidate agents
   |
   v
Check cost / quota / privacy / local-tool constraints
   |
   v
Assign + claim
   |
   v
Execute / verify / review
```

Suggested decision factors:

- repository permissions
- filesystem/shell access
- context capacity
- domain skill availability
- independent-review requirement
- current quota/cooldown
- expected cost
- latency
- privacy boundary
- platform/OS compatibility
- task parallelizability
- current claims/worktree ownership
- historical eval quality for the capability

---

## 7. Durable protocols

### 7.1 `awiki-task/v1`

```yaml
schema: awiki-task/v1
id: AW-219
goal: Harden provider fallback
project: A-Wiki
risk: high
mode: pair
status: implementing
required_capabilities:
  - repository-write
  - tests
acceptance:
  - no direct-main mutation
  - regression suite green
assigned:
  executor: zcode-glm
  reviewer: openai-reviewer
head_sha: null
```

### 7.2 `awiki-review/v1`

Already planned by the Agent Review Bus. It remains the canonical independent review contract.

### 7.3 `awiki-handoff/v1`

A handoff must preserve enough information for a different agent to resume without hidden chat history:

```yaml
schema: awiki-handoff/v1
task_id: AW-219
from: zcode-glm
to_role: reviewer
branch: feature/example
head_sha: abc123
changed_files: []
tests:
  passed: []
  failed: []
open_questions: []
known_risks: []
next_action: review
```

Do not store private chain-of-thought. Store decisions, evidence, assumptions, outputs, and reproducible commands only.

---

## 8. Claims, leases, and worktree isolation

Multi-agent work is unsafe without ownership boundaries.

Conceptual claim:

```yaml
task: AW-219
agent: zcode-glm
lease: 30m
files:
  - scripts/lib/providers/client.py
  - tests/providers/**
worktree: .worktrees/AW-219-glm
```

Requirements:

- file/path claims are time-limited leases;
- conflicting claims block writes or require explicit coordination;
- each concurrent executor gets an isolated worktree/branch;
- dirty unrelated WIP is never silently rebased, reset, cleaned, or overwritten;
- stale claims can expire/recover safely;
- reviewer is read-only unless explicitly assigned remediation work.

DISC-001 makes worktree isolation a hard architectural requirement for autonomous parallel work.

---

## 9. Communication model: durable bus, not direct hidden chat

Do not make direct Agent A -> Agent B chat the source of truth.

Initial durable transport:

```text
Git branch
PR
commit SHA
review comments
machine-readable state
CI/test artifacts
```

Future transport can include MCP/event queues, but all transports normalize into the same task/review/handoff contracts.

```text
Agent Adapter
    |
    v
A-Wiki protocol
    |
    +--> GitHub transport
    +--> local MCP transport
    +--> future remote queue
```

A new vendor should require an adapter, not a rewrite of the workflow.

---

## 10. MCP orchestration surface

A-Wiki MCP should eventually expose vendor-neutral orchestration namespaces.

```text
agent.list
agent.capabilities
agent.health
agent.available

task.create
task.get
task.next
task.assign
task.claim
task.release
task.status
task.complete

handoff.create
handoff.read

review.request
review.status
review.submit
review.findings
review.resolve

claim.acquire
claim.list
claim.release

workflow.start
workflow.advance
workflow.pause
workflow.stop

provider.health
provider.cooldown

memory.recall
memory.remember
```

MCP is the interface. **The orchestration policy remains inside A-Wiki**, not inside vendor-specific MCP servers.

---

## 11. Hooks: safety police, not orchestration manager

Hooks should enforce invariants around the orchestrator rather than contain the orchestrator itself.

Good hook responsibilities:

```text
session start  -> register agent / inspect task
pre-write      -> verify claim + privacy gate
pre-bash       -> destructive-command safety
pre-push       -> branch/test policy
post-commit    -> update task evidence
post-push      -> mark reviewable
stop           -> persist state + release/renew claims
```

Do not put complex task decomposition, provider ranking, or multi-agent scheduling inside hooks. That becomes opaque and difficult to test.

---

## 12. Degraded-mode and quota fallback rules

The orchestrator must keep useful work moving when providers are unavailable.

### Preferred reviewer unavailable

```text
Codex quota exhausted
   -> try ChatGPT reviewer
   -> try Claude reviewer
   -> if none available:
        SOLO/self-review
        mark independent_review=pending
```

### Preferred executor unavailable

```text
GLM unavailable
   -> find next candidate satisfying executor capabilities
   -> preserve same awiki-task/v1 contract
```

### Only one capable agent remains

```text
AUTO -> SOLO
mechanical verification required
independent review deferred, never fabricated
```

### Provider recovers later

Pending review tasks can be automatically queued for an independent reviewer when capability returns.

---

## 13. Human escalation policy

Autonomy should stop for:

- secret/credential exposure
- destructive data loss risk
- public/private boundary ambiguity
- production deployment
- irreversible migration
- force push / protected-branch rewrite
- security blocker
- architecture conflict that changes agreed scope
- reviewer disagreement above policy threshold
- budget/cost threshold breach
- repeated failure / max review cycles
- task goal ambiguity that materially changes outcome

Routine implementation findings should not require the human owner to relay messages.

---

## 14. Orchestrator service — later phase

Once the protocols and Review Bus are stable, A-Wiki can host a lightweight local service:

```text
awiki-orchestrator
        |
        +-- task/state engine
        +-- agent registry
        +-- capability router
        +-- GitHub adapter
        +-- MCP interface
        +-- provider/agent health
        +-- retry/reassignment
        +-- audit log
```

Possible local endpoint is an implementation detail, not a contract. Avoid coupling the architecture to a fixed port or daemon model until necessary.

The first implementation should prefer SQLite/files + existing A-Wiki primitives before adding external infrastructure.

---

## 15. Operator observability

The future dashboard should answer:

```text
What goal is active?
Which mode is running?
Which agents are available?
Who owns each task/file?
Which agents are quota-limited?
What is waiting for review?
What is blocked and why?
What tests/CI are green/red?
How much cost/time has been consumed?
Which human decisions are required?
```

Suggested views:

- Active Agents
- Task Board
- Claims / Worktrees
- Review Queue
- Provider/Quota Health
- Cost/Budget
- Blocked / Escalations
- READY_FOR_HUMAN

Observability data is runtime state; do not churn Git with telemetry.

---

## 16. Security and privacy requirements

The orchestrator must never turn multi-agent convenience into wider data exposure.

Rules:

- public-safe A-Wiki knowledge remains separate from private Drive data;
- task envelopes use least necessary context;
- private context is only mounted/retrieved for agents explicitly allowed to receive it;
- secrets never enter GitHub review state;
- provider adapters declare trust/privacy constraints;
- external MCP modules are default-off and least-privilege;
- all destructive actions require explicit policy gates;
- agent-generated state must preserve provenance.

---

## 17. Relationship to A-Wiki memory

Multi-agent orchestration and memory must reinforce each other without polluting global knowledge.

```text
Task execution evidence
      |
      v
Session / Project Memory
      |
      v
Distill
      |
      v
Privacy + Generalization + Evidence gates
      |
      v
Global Knowledge Promotion
```

Agent chatter is not automatically global memory.

Useful durable memory includes:

- architecture decisions
- failed approaches and why
- accepted reviewer findings
- verified test/eval outcomes
- provider capability lessons
- reusable workflows

---

## 18. Roadmap integration with current vNext migration

Do **not** interrupt the active migration to build the full orchestrator.

### Existing phases that become foundations

```text
Phase 3  Kernel Contract
         - define awiki-task/v1
         - formalize awiki-review/v1
         - define agent/capability vocabulary
         - define orchestration/storage contracts

Phase 4  Project Adapter
         - expose project identity/context to orchestrated agents

Phase 5  Memory Layers
         - durable project/session/experiment handoff memory

Phase 6  Hook Engine
         - vendor-neutral claim/safety lifecycle gates

Phase 7  Model Control Plane
         - provider/model health and policy/runtime separation

Phase 8  Eval + Routing Promotion
         - first automatic reviewer adapter
         - evaluation evidence for capability routing

Phase 9  A-Loop v2
         - connect task/review/remediation states to measurable improvement loops

Phase 11 Documentation Slimming
         - compatibility matrix + operator docs
```

### Post-vNext orchestration expansion

#### Phase 12 — Agent Registry & Availability

Deliver:

- `awiki-agent-registry/v1`
- adapter capability declarations
- runtime health/quota/cooldown state
- candidate filtering
- no Git telemetry churn

#### Phase 13 — Assignment Engine

Deliver:

- `AUTO / SOLO / PAIR / ARCHITECT_EXECUTOR / PARALLEL / COUNCIL`
- capability-based ranking
- independent-review policy
- claim-aware assignment
- quota/provider fallback
- cost/risk thresholds

#### Phase 14 — Orchestrator Service + MCP

Deliver:

- task engine
- handoff engine
- review queue integration
- agent registration/heartbeat
- retry/reassign
- MCP orchestration namespace
- durable restart-safe state

#### Phase 15 — Operator UI / Integrations

Deliver:

- task/agent/review dashboard
- quota/provider health
- human escalation inbox
- optional product-specific plugin/connectors

Plugin/UI is not the core protocol.

#### Phase 16 — Autonomous Loop Hardening

Deliver:

- max-cycle controls
- timeout/recovery
- budget ceilings
- crash recovery
- stale claim recovery
- adversarial/regression evals
- multi-agent conflict handling
- pending-review recovery when providers return

---

## 19. MVP definition

Do not start with a large swarm.

The first useful orchestrator is complete when **two heterogeneous agents can collaborate without the user copying messages**.

MVP acceptance criteria:

- one agent can register as executor;
- another can register as reviewer;
- task survives session restart;
- exact HEAD SHA is review target;
- findings have stable IDs;
- executor automatically receives actionable findings;
- executor can remediate and resubmit;
- CI/mechanical verification contributes to readiness;
- quota/unavailable reviewer can be substituted;
- one-agent SOLO fallback remains usable;
- pending independent review is represented truthfully;
- claims/worktree isolation prevents collisions;
- no automatic merge/deploy/destructive branch rewrite;
- vendor/model replacement does not change the task protocol.

---

## 20. Example: current real-world scenario generalized

```text
OpenAI coding quota exhausted
ChatGPT architecture/review available
ZCode/GLM executor available

AUTO evaluates task
   -> large migration + independent review required
   -> select ARCHITECT_EXECUTOR mode
   -> ChatGPT = architect/reviewer capability
   -> GLM = executor capability
   -> GitHub = durable review transport
   -> user only approves high-risk gates
```

Later:

```text
GLM quota exhausted
Codex available

Same task protocol
   -> executor candidate changes
   -> no workflow rewrite
```

This exact adaptability is a primary product requirement, not an edge case.

---

## 21. Shared-conversation architecture intake

Owner-provided public ChatGPT Share reference:

```text
https://chatgpt.com/share/6a835b35-9494-83ec-8c93-1d4cecb8710b
```

At the time of this architecture update, the assistant environment could not retrieve the shared page content reliably. Therefore this document **does not invent or attribute unseen requirements** from that link.

Future intake procedure when content is accessible:

```text
Fetch shared conversation
  -> extract candidate requirements/ideas
  -> classify: CORE / MODULE / PATTERN / REFERENCE / REJECT
  -> deduplicate against this roadmap and existing A-Wiki capabilities
  -> privacy check
  -> architecture impact review
  -> add only accepted deltas with provenance
```

This keeps external conversation intake evidence-based and prevents architecture drift.

---

## 22. Final operating model

```text
USER
  |
  | "ทำงานนี้ให้"
  v
A-Wiki Orchestrator
  |
  +-- choose mode
  +-- choose capabilities
  +-- assign/claim worktrees
  +-- provide relevant memory/skills
  |
  +--> one agent when sufficient
  |
  +--> multiple agents when beneficial
  |
  +--> substitute providers when unavailable
  |
  v
Mechanical verification + independent review when required
  |
  v
READY / BLOCKED / HUMAN_GATE
```

A-Wiki should not try to make every task multi-agent.

> **The goal is not “more agents.” The goal is the smallest reliable team that can complete the task under the current constraints.**
